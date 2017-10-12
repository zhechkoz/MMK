'''
Created on 25.02.2017

@author: murauermax and zhechkoz

'''
from scripting import *
import os, sys, errno
import simplejson as json
import xml.etree.ElementTree as ET
import datetime
from collections import namedtuple
import math
import utm
import re

# Get a CityEngine instance
ce = CE()

# Define OSM data location
osm = 'data/tum-sanitized.osm'
sumo = 'data/tum-sanitized.net.xml'

# Define center coordinates
ox = 690985
oz = 5336220

sumoox = 606
sumooz = 596

# Define cleanup settings which preserve osm meta data
cleanupSettings = CleanupGraphSettings()
cleanupSettings.setIntersectSegments(False)
cleanupSettings.setMergeNodes(False)
cleanupSettings.setSnapNodesToSegments(False)
cleanupSettings.setResolveConflictShapes(True)

osmSettings = OSMImportSettings()

# https://pypi.python.org/pypi/utm
class CoordinatesConvertor(object):
    def __init__(self):
        (authAndCode, _) = ce.getSceneCoordSystem()
        
        if authAndCode == None or authAndCode.split(':')[0].strip() != 'EPSG':
            raise Exception('Map is not in WGS84 coordinates!')
        
        code = authAndCode.split(':')[1].strip()[2:]
        if code[0] == '6':
            self.northern = True
        elif code[0] == '7':
            self.northern = False
        else:
            raise Exception('Coordinates code not correct!')
        
        self.zoneNumber = int(code[1:])
        
    def from_latlon(self, lat, lon):
        return utm.from_latlon(lat, lon)
        
    def to_latlon(self, easting, northing):
        return utm.to_latlon(abs(easting), abs(northing), self.zoneNumber, northern=self.northern) 


class MMKGraph(object):
    def __init__(self):
        self.author = 'TUM - MMK'
        self.date = datetime.date.today()
        self.project = ce.project()
        self.nodeCnt = 0
        self.segmentCnt = 0
        self.nodes = {}
        self.segments = {}
        self.OSMOID = {}
   
    def reprJSON(self):
        return dict(author=self.author, 
                    date=str(self.date), 
                    project=self.project, 
                    nodeCnt=self.nodeCnt, 
                    segementCnt=self.segmentCnt, 
                    nodes=self.nodes.values(), 
                    segments=self.segments.values()
               )
        
    def setNodeCnt(self, nodeCnt):
        self.nodeCnt = nodeCnt
    
    def setSegmentCnt(self, segmentCnt):
        self.segmentCnt = segmentCnt
    
    def appendGraphItem(self, item):
        if isinstance(item, MMKGraphNode):
            self.nodes[item.OID] = item
            if self.OSMOID.has_key(item.osmID):
                raise ValueError('More than one node have the same OSM ID')
        elif isinstance(item, MMKGraphSegment):
            self.segments[item.OID] = item         
        else:
            raise ValueError('GraphItem should be node or segment')

        self.OSMOID.setdefault(item.osmID, []).append(item.OID)
   
    def getNode(self, OID):
        return self.nodes.get(OID, None)
    
    def getSegment(self, OID):
        return self.segments.get(OID, None)

    def getNodeByOSMID(self, osmID):            
        return self.getNode(self.OSMOID.get(osmID, [''])[0])
    
    def getSegmentsByOSMID(self, osmID):            
        ids = self.OSMOID.get(osmID, [])
        segments = [self.getSegment(oid) for oid in ids] 
        return segments
    
    def collectLanesFromSUMOItems(self, SUMOedges, SUMOnodes):
        for (id, nodes) in SUMOnodes.iteritems():
            osmID = int(id)
            ceNode = self.getNodeByOSMID(osmID)

            if not ceNode:
                # Node was deleted during CE cleanup process so
                # try to find the nearest node which exists and append the
                # lanes information. 
                # Important: User has to match the CE model
                missingNode = nodes[0]
                minDistance = sys.maxint
                for node in self.nodes.values():
                    abs = missingNode.vertices[0].distanceTo(node.vertices[0]) 
                    if abs < minDistance:
                        minDistance = abs
                        ceNode = node

            for node in nodes:
                ceNode.appendLanes(node.lanes)
                ceNode.hierarchy = node.hierarchy

        for (id, edges) in SUMOedges.iteritems():
            forward = True
            osmID = 0

            if len(id) > 1 and id[0:2] == '--':
                # Edge's OSM ID is negative and direction is negative, so
                # this is a backwards segment
                osmID = int(id[2:])
                forward = False
            elif len(id) > 0 and id[0] == '-':
                # If there is an edge with a positive sign then this is a
                # backwards direction segment, else this is a forward 
                # segment with a negative OSM ID (according to OSM IDs can be negative)
                forward = not SUMOedges.has_key(id[1:])
                osmID = int(id) if forward else int(id[1:])
            elif len(id) > 0:
                # Normal forward edge
                osmID = int(id)
                forward = True
            else:
                print("Not valid OSM ID format found " + str(id))
                continue
            
            segments = self.getSegmentsByOSMID(osmID)

            if len(segments) == 0:
                print('WARNING: Segment with OSM ID ' + str(id) + ' found in SUMO is missing!')
                continue
            else:
                for segment in segments:
                        for edge in edges:
                            segment.appendLanes(edge.lanes, forward=forward)    
    
    def exportJson(self, exportName):
        dir = ce.toFSPath('/' + ce.project())
        mkdir_p(os.path.join(dir, 'export'))
        dir = ce.toFSPath('export/' +  exportName)

        with open(dir, 'w+') as file:  
            file.write(json.dumps(self, indent=4, sort_keys=True, cls=ComplexEncoder))
        print('File exported! Location: ' + dir + '\n')

      
class MMKGraphItem(object):   
    def __init__(self, itemID, vertices):
        self.OID = itemID
        self.vertices = []
        self.decodeAndAppendVertices(vertices)

    def appendVertex(self, x, y, z):
        vertex = MMKGraphVertex(x, y, z)
        self.vertices.append(vertex)
        
    def decodeAndAppendVertices(self, verticesList):
        for i in xrange(0,(len(verticesList)-1),3):
            x = float(verticesList[i])
            y = float(verticesList[i+1])
            z = float(verticesList[i+2])
            x, y, z = self.transform(x, y, z)
           
            self.appendVertex(x, y, z)          
        
    def transform(self, x, y ,z):
        # Apply transformation for every point to match Unity CS
        x = x - ox if x > 0 else x + ox
        z = z - oz if z > 0 else z + oz
            
        return -x, -y, z
    
    def decodeAttributes(self, attributesDict):
        for (key, value) in attributesDict.iteritems():
            setattr(self, key, value)
    
    def reprJSON(self):
        return dict(ID=str(self.OID), vertices=self.vertices)
   

class MMKGraphSegment(MMKGraphItem):
    def __init__(self, itemOID, vertices, attributesDict, neighbours):
        super(MMKGraphSegment, self).__init__(itemOID, vertices)
        
        if len(neighbours) != 2:
                raise ValueError('Segments should have exactly two end nodes!\n' + str(self.itemOID))
        
        self.start = neighbours[0]
        self.end = neighbours[1]
        self.length = self.vertices[0].distanceTo(self.vertices[1])
        self.shapes = []
        self.lanesForward = []
        self.lanesBackward = []
        self.decodeAttributes(attributesDict)
        
    def appendShapes(self, shapeOID, vertices):
        shape = MMKGraphShape(shapeOID, vertices)
        self.shapes.append(shape)
    
    def appendLanes(self, lanes, forward = True):
        if forward:
            self.lanesForward.extend(lanes)
        else:
            self.lanesBackward.extend(lanes)
        
    def reprJSON(self):
        totalLanes = {'forward' : self.lanesForward}
        if len(self.lanesBackward) > 0:
            totalLanes['backward'] = self.lanesBackward
            
        dict = {'hierarchy' : self.hierarchy, 
                'maxspeed' : self.maxspeed, 
                'lanes' : totalLanes,
                'oneway' : self.oneway,
                'osm' : self.osmID, 
                'length' : self.length, 
                'start' : self.start, 
                'end' : self.end, 
        }
        
        if len(self.shapes) > 0:
            dict['shapes'] = self.shapes

        dict.update(super(MMKGraphSegment, self).reprJSON())
        return dict

  
class MMKGraphNode(MMKGraphItem):
    def __init__(self, itemOID, vertices, attributesDict, neighbours):
        super(MMKGraphNode, self).__init__(itemOID, vertices)
        
        self.decodeAttributes(attributesDict)
        self.corrSegments = neighbours
        self.hierarchy = 'unknown'
        self.shapes = []
        self.lanes = []

    def appendShapes(self, shapeOID, vertices):
        shape = MMKGraphShape(shapeOID, vertices)
        self.shapes.append(shape)

    def appendLanes(self, lanes):
        self.lanes.extend(lanes)

    def reprJSON(self):
        dict = {'hierarchy' : self.hierarchy, 
                'corrSegments' : self.corrSegments, 
                'osm' : self.osmID,
        }
        
        if len(self.lanes) > 0:
            dict['lanes'] = self.lanes
        
        if len(self.shapes) > 0:
            dict['shapes'] = self.shapes
        
        dict.update(super(MMKGraphNode, self).reprJSON())
        return dict
        

class MMKGraphShape(MMKGraphItem):
    def __init__(self, itemOID, vertices):
        super(MMKGraphShape, self).__init__(itemOID, vertices)
    
    def reprJSON(self):
        return super(MMKGraphShape, self).reprJSON()

        
class MMKGraphVertex(object):      
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        
    def distanceTo(self, other):
        vabs = MMKGraphVertex(other.x-self.x, other.y-self.y, other.z-self.z)
        abs = math.sqrt(vabs.x**2 + vabs.y**2 + vabs.z**2) 
        return abs

    def reprJSON(self):
        return dict(x=self.x, 
                    y=self.y, 
                    z=self.z
               )


class SUMOItem(MMKGraphItem):
    def __init__(self, itemOID, vertices):
        super(SUMOItem, self).__init__(itemOID, vertices)
    
    def transform(self, x, y, z):
        # Apply transformation for every point to match Unity CS
        x = -x + sumoox
        z = -z + sumooz
            
        return x, y, z
        
class SUMOEdge(SUMOItem):
    def __init__(self, itemOID, vertices, order, start, end):
        super(SUMOEdge, self).__init__(itemOID, vertices)
        self.order = order
        self.start = start
        self.end = end
        self.lanes = []
        
    def appendLane(self, id, vertices, index, length):
        lane = SUMOLane(id, vertices, index, length)
        self.lanes.append(lane)

        
class SUMONode(SUMOItem):
    def __init__(self, itemOID, vertices):
        super(SUMONode, self).__init__(itemOID, vertices)
        self.lanes = []
        
    def appendLane(self, id, vertices, index, length):
        lane = SUMOLane(id, vertices, index, length)
        self.lanes.append(lane)
        

class SUMOLane(SUMOItem):
    def __init__(self, itemOID, vertices, index, length):
        super(SUMOLane, self).__init__(itemOID, vertices)
        self.index = index
        self.length = length

    def reprJSON(self):
        dict = {'length' : self.length,
                'index' : self.index
        }
        dict.update(super(SUMOLane, self).reprJSON())
        return dict

def parseGraph(graphLayerName, MMKGraphObj):   
    # Parse segments
                
    segments = ce.getObjectsFrom(ce.scene, ce.isGraphSegment)    
    MMKGraphObj.setSegmentCnt(len(segments))    
    for o in segments:
        neighbours = ce.getObjectsFrom(o, ce.isGraphNode)
        neighboursList = []
        
        attributesDict = attributeSegment(o)
        
        for neighbour in neighbours:
            neighboursList.append(ce.getOID(neighbour))
        
        segment = MMKGraphSegment(ce.getOID(o), ce.getVertices(o), attributesDict, neighboursList)
        
        shapes = ce.getObjectsFrom(o, ce.isShape)
        for s in shapes:
            segment.appendShapes(ce.getOID(s), ce.getVertices(s))

        MMKGraphObj.appendGraphItem(segment)
            
            
    # Parse nodes
    
    nodes = ce.getObjectsFrom(ce.scene, ce.isGraphNode)
    MMKGraphObj.setNodeCnt(len(nodes))    
    for o in nodes:
        neighbours = ce.getObjectsFrom(o, ce.isGraphSegment)
        neighboursList = []
        
        for neighbour in neighbours:
            neighboursList.append(ce.getOID(neighbour)) 
        
        attributesDict = attributeNode(o, neighboursList, MMKGraphObj)
        
        node = MMKGraphNode(ce.getOID(o), ce.getVertices(o), attributesDict, neighboursList)
        
        shapes = ce.getObjectsFrom(o, ce.isShape)
        for s in shapes:    
            node.appendShapes(ce.getOID(s), ce.getVertices(s)) 
            
        MMKGraphObj.appendGraphItem(node)

    # Try to parse SUMO Lanes
    
    sumoFile = ce.toFSPath(sumo)
    if not os.path.isfile(sumoFile):
        print('WARNING: SUMO file not found! Lane information will not be generated!')
    else:
        edges, nodes = parseSUMONet(sumoFile)
        MMKGraphObj.collectLanesFromSUMOItems(edges, nodes)
        

def parseSUMONet(sumoFile):
    sumo = ET.parse(sumoFile)
    root = sumo.getroot()
    sumoEdges, sumoNodes = ({}, {})
    junctions = {j.attrib['id'] : j.attrib for j in root.findall('junction')}

    for edge in root.findall('edge'):
        edgeAttrib = edge.attrib

        idOrder = re.split('_|#', edgeAttrib['id']) # If no order in id set it to 0
        (id, order) = (idOrder[0], int(idOrder[1]) if len(idOrder) > 1 else 0)
        isNode = (len(id) > 0 and id[0] == ':') # Nodes are always internal and start with a ':'
        id = id[1:] if isNode else id
        
        vertices = []
        itemAttr = {}

        if isNode:
            junctionAttrib = junctions.get(id, None)
            if junctionAttrib:
                vertices.extend((junctionAttrib['x'], 0, junctionAttrib['y']))
                itemAttr = {'hierarchy' : junctionAttrib['type']}
            
            sumoItem = SUMONode(id, vertices)
            sumoNodes.setdefault(sumoItem.OID, []).append(sumoItem)
        else:
            if edgeAttrib.has_key('shape'):
                for vertex in edgeAttrib['shape'].split(' '):
                    (x, y) = vertex.split(',')
                    vertices.extend((x, 0, y))            

            (start, end) = (edgeAttrib.get('from', ''), edgeAttrib.get('to', ''))
            sumoItem = SUMOEdge(id, vertices, order, start, end)
            sumoEdges.setdefault(sumoItem.OID, []).append(sumoItem)
            
        sumoItem.decodeAttributes(itemAttr)

        for lane in edge.findall('lane'):
            laneAttrib = lane.attrib
            id = laneAttrib['id']
            length = laneAttrib.get('length', 0)
            index = laneAttrib.get('index', 0)
            vertices = []
            
            if laneAttrib.has_key('shape'):
                for vertex in laneAttrib['shape'].split(' '):
                    (x, y) = vertex.split(',')
                    vertices.extend((x, 0, y))

            sumoItem.appendLane(id, vertices, index, length)

    return sumoEdges, sumoNodes
    
def attributeSegment(segment):
    highway = ce.getAttribute(segment, 'highway')
    maxspeed = ce.getAttribute(segment, 'maxspeed')
    lanes = ce.getAttribute(segment, 'lanes')
    oneway = ce.getAttribute(segment, 'oneway') == 'yes'
    osmID = ce.getAttribute(segment, 'osm_id')
    
    if osmID == None:
        print('WARNING: Segment with invalid OSM ID found: ' + str(ce.getOID(segment)))
        osmID = 0
    else:
        osmID = int(osmID) # All OSM IDs are 64 bit integers
    
    if maxspeed == None or maxspeed <= 0:
        print('WARNING: Segment with invalid maxspeed found: ' + str(ce.getOID(segment)))
    
    if lanes == None or lanes <= 0:
        print('WARNING: Segment with invalid lanes found: ' + str(ce.getOID(segment)))
    
    attributesDict = {'hierarchy' : highway, 
                      'maxspeed' : maxspeed, 
                      'oneway' : oneway,
                      'osmID' : osmID
    }
    
    return attributesDict

def attributeNode(node, neighbours, graph):
    osmID = ce.getAttribute(node, 'osm_id')
    
    if osmID == None:
        print('WARNING: Node with invalid OSM ID found: ' + str(ce.getOID(node)))
        osmID = 0
    else:
        osmID = int(osmID) # All OSM IDs are 64 bit integers

    return {'osmID' : osmID}  
        
def mkdir_p(path):
    try:
        os.makedirs(path)      
    except OSError, exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        elif exc.errno == 20047:
            #another microsoft thing
            pass
        else:
            raise

            
class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj,'reprJSON'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self, obj)

        
def cleanupGraph():
    graphlayer = ce.getObjectsFrom(ce.scene, ce.isGraphLayer)
    ce.cleanupGraph(graphlayer, cleanupSettings)

def fixIntersectionShapes():
    objects = ce.getObjectsFrom(ce.scene, ce.isGraphSegment)
    intersections = []
    # http://cehelp.esri.com/help/index.jsp?topic=/com.procedural.cityengine.help/html/manual/is/create/streetshapes.html
    shapeWhiteList = ['CROSSING', 'JUNCTION', 'FREEWAY', 'FREEWAY_ENTRY'] 
    
    for o in objects:
        attrStart = ce.getAttribute(o, 'connectionStart') or ''
        attrEnd = ce.getAttribute(o, 'connectionEnd') or ''
        
        if any(shape in attrStart for shape in shapeWhiteList) != any(shape in attrEnd for shape in shapeWhiteList):
            intersections.append(o)
    
    for intersection in intersections:
        lanes = int(ce.getAttribute(intersection, 'lanes'))
        if lanes == 1:
            continue

        oneway = ce.getAttribute(intersection, 'oneway') == 'yes'
        lanesForward = ce.getAttribute(intersection, 'lanes:forward')
        lanesBackward = int(ce.getAttribute(intersection, 'lanes:backward') or 0)

        if not lanesForward:
            if oneway:
                lanesForward = lanesBackward = lanes
            else:
                lanesForward = int(lanes / 2)
                lanesBackward = lanes - lanesForward
        else:
            lanesForward = int(lanesForward)
        
        offset = 2 * (lanesForward - lanesBackward)
        offset = -offset if lanesForward > lanesBackward else offset
        
        ce.setAttributeSource(intersection, '/ce/street/streetOffset', 'OBJECT')
        oldOffset = int(ce.getAttribute(intersection, 'streetOffset') or 0)
        newOffset = oldOffset + offset
        ce.setAttribute(intersection, 'streetOffset', newOffset)
            
@noUIupdate
def prepareScene():
    print('Cleaning up old imports...')
    
    # Delete all old layers
    layers = ce.getObjectsFrom(ce.scene, ce.isLayer, ce.withName("'osm graph'"))
    ce.delete(layers)
    
    print('Importing OSM data...')
    
    osmFile = ce.toFSPath(osm)
    if not os.path.isfile(osmFile):
        raise ValueError('OSM file not found!')

    # Import OSM data
    graphLayers = ce.importFile(osmFile, osmSettings, False)
        
    for graphLayer in graphLayers:
        ce.setName(graphLayer, 'osm graph')

    cleanupGraph()
    fixIntersectionShapes()
    cleanupGraph()
    
if __name__ == '__main__':
    
    print('MMK Streetnetwork Export\n')
    #prepareScene()
   
    graph = MMKGraph()
    print('Building streetnetwork...')
    
    parseGraph("Streetnetwork", graph)
    graph.exportJson('MMK_GraphExport.json')
    
    print('Finished. Success!\n')