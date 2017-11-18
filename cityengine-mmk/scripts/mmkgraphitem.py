'''
Created on 11.03.2017

@author:  zhechkoz

'''
import math

class MMKGraphItem(object):
    def __init__(self, id, vertices):
        self.id = id
        self.vertices = self.decodeVertices(vertices)

    def decodeVertices(self, verticesList):
        vertices = []
        for i in xrange(0, (len(verticesList) - 1), 3):
            x = float(verticesList[i])
            y = float(verticesList[i+1])
            z = float(verticesList[i+2])
            vertices.append(MMKGraphVertex(x, y, z))
        return vertices
 
    def appendVertex(self, x, y, z):
        vertex = MMKGraphVertex(x, y, z)
        self.vertices.append(vertex)
    
    # Has to be overriden by all subclasses
    def transform(self, dx, dy, dz):
        pass

    def reprJSON(self):
        return dict(id=self.id, vertices=self.vertices)
        

class MMKGraphVertex(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def distanceTo(self, other):
        if not isinstance(other, self.__class__):
            raise ValueError("Distance can only be calculated between two vertices!")

        vabs = MMKGraphVertex(other.x-self.x, other.y-self.y, other.z-self.z)
        abs = math.sqrt(vabs.x**2 + vabs.y**2 + vabs.z**2)
        return abs

    def reprJSON(self):
        return dict(x=self.x,
                    y=self.y,
                    z=self.z
               )
               
               
class SUMOGraphItem(MMKGraphItem):
    def __init__(self, id, vertices):
        newVertices = []
        for vertex in vertices.split(' '):
            (x, y) = vertex.split(',')
            newVertices.extend((x, 0, y))
        super(SUMOGraphItem, self).__init__(id, newVertices)

    def transform(self, dx, dy, dz):
        # Apply transformation for every point to match Unity CS
        for vertex in self.vertices:
            vertex.x = -vertex.x + dx
            vertex.z = -vertex.z + dz


class SUMOGraphEdge(SUMOGraphItem):
    def __init__(self, id, vertices, order, start, end):
        super(SUMOGraphEdge, self).__init__(id, vertices)
        self.order = order
        self.start = start
        self.end = end
        self.lanes = {}
    
    def transform(self, dx, dy, dz):  
        super(SUMOGraphEdge, self).transform(dx, dy, dz)
        for lane in self.lanes.values():
            lane.transform(dx, dy, dz)

    def appendLane(self, id, vertices, index, length):
        lane = SUMOGraphLane(id, vertices, index, length)
        self.lanes[lane.id] = lane


class SUMOGraphNode(SUMOGraphItem):
    def __init__(self, id, vertices, hierarchy):
        super(SUMOGraphNode, self).__init__(id, vertices)
        self.hierarchy = hierarchy
        self.lanes = {}
    
    def transform(self, dx, dy, dz):  
        super(SUMOGraphNode, self).transform(dx, dy, dz)
        for lane in self.lanes.values():
            lane.transform(dx, dy, dz)

    def appendLane(self, id, vertices, index, length):
        lane = SUMOGraphLane(id, vertices, index, length)
        self.lanes[lane.id] = lane


class SUMOGraphLane(SUMOGraphItem):
    def __init__(self, id, vertices, index, length):
        super(SUMOGraphLane, self).__init__(id, vertices)
        self.index = index
        self.length = length

    def reprJSON(self):
        dict = {'length' : self.length,
                'index' : self.index
        }
        dict.update(super(SUMOGraphLane, self).reprJSON())
        return dict


class CEGraphItem(MMKGraphItem):
    def __init__(self, id, vertices, osmID):
        super(CEGraphItem, self).__init__(id, vertices)

        try:
            self.osmID = int(osmID) # All OSM IDs are 64 bit signed integers
        except ValueError or TypeError:
            self.osmID = 0
            print('WARNING: Item with invalid OSM ID found: ' + id)
    
    def initializeAttributes(self, ce, item):
        pass
    
    def transform(self, dx, dy, dz):
        # Apply transformation for every point to match Unity CS
        for vertex in self.vertices:    
            vertex.x = -(vertex.x + dx)
            vertex.y = -vertex.y
            vertex.z = vertex.z + dz
    
    def reprJSON(self):
        dict = {'osm' : self.osmID}
        dict.update(super(CEGraphItem, self).reprJSON())
        return dict
   
   
class CEGraphSegment(CEGraphItem):
    def __init__(self, id, vertices, osmID, neighbours, hierarchy=None, oneway=None, maxspeed=None):
        super(CEGraphSegment, self).__init__(id, vertices, osmID)

        if len(neighbours) != 2:
                raise ValueError('Segments should have exactly two end nodes!\n' + id)

        self.start = neighbours[0]
        self.end = neighbours[1]
        self.length = self.vertices[0].distanceTo(self.vertices[1])
        self.shapes = []
        self.forwardLanes = []
        self.backwardLanes = []
        self.hierarchy = hierarchy
        self.maxspeed = maxspeed
        self.oneway = oneway
    
    def initializeAttributes(self, ce, item):
        super(CEGraphSegment, self).initializeAttributes(ce, item)
        
        highway = ce.getAttribute(item, 'highway')
        maxspeed = ce.getAttribute(item, 'maxspeed')
        lanes = ce.getAttribute(item, 'lanes')
        oneway = ce.getAttribute(item, 'oneway') == 'yes'

        if maxspeed == None or maxspeed <= 0:
            print('WARNING: Segment with invalid maxspeed found: ' + self.id)

        if lanes == None or lanes <= 0:
            print('WARNING: Segment with invalid lanes found: ' +  self.id)

        self.hierarchy = highway
        self.maxspeed = maxspeed
        self.oneway = oneway

    def transform(self, dx, dy, dz):  
        super(CEGraphSegment, self).transform(dx, dy, dz)
        for shape in self.shapes:
            shape.transform(dx, dy, dz)

    def appendShapes(self, shapeID, vertices, osmID):
        shape = CEGraphItem(shapeID, vertices, osmID)
        self.shapes.append(shape)

    def appendLanes(self, lanes, forward=True):
        if forward:
            self.forwardLanes += lanes
        else:
            self.backwardLanes += lanes
        
    def reprJSON(self):
        totalLanes = {'forward' : self.forwardLanes}
        totalLanes.update({'backward' : self.backwardLanes} if self.backwardLanes else {})

        dict = {'hierarchy' : self.hierarchy,
                'maxspeed' : self.maxspeed,
                'lanes' : totalLanes,
                'oneway' : self.oneway,
                'length' : self.length,
                'start' : self.start,
                'end' : self.end,
        }
        
        dict.update({'shapes' : self.shapes} if self.shapes else {})

        dict.update(super(CEGraphSegment, self).reprJSON())
        return dict


class CEGraphNode(CEGraphItem):
    def __init__(self, id, vertices, osmID, neighbours, hierarchy='unknown'):
        super(CEGraphNode, self).__init__(id, vertices, osmID)

        self.neighbourSegments = neighbours
        self.hierarchy = hierarchy
        self.shapes = []
        self.lanes = []

    def transform(self, dx, dy, dz):  
        super(CEGraphNode, self).transform(dx, dy, dz)
        for shape in self.shapes:
            shape.transform(dx, dy, dz)

    def appendShapes(self, shapeID, vertices, osmID):
        shape = CEGraphItem(shapeID, vertices, osmID)
        self.shapes.append(shape)

    def appendLanes(self, lanes):
        self.lanes += lanes

    def reprJSON(self):
        dict = {'hierarchy' : self.hierarchy,
                'neighbourSegments' : self.neighbourSegments
        }
        
        dict.update({'lanes' : self.lanes} if self.lanes else {})
        dict.update({'shapes' : self.shapes} if self.shapes else {})

        dict.update(super(CEGraphNode, self).reprJSON())
        return dict
