'''
Created on Apr 23, 2017

@author: Zhechko Zhechev
'''
from scripting import *
import sys
import math
import utm

# get a CityEngine instance
ce = CE()

sys.path.append(ce.toFSPath('scripts'))
import mmk_config as config

# Define cleanup settings which preserve osm meta data
cleanupSettings = CleanupGraphSettings()
cleanupSettings.setIntersectSegments(False)
cleanupSettings.setMergeNodes(False)
cleanupSettings.setSnapNodesToSegments(False)
cleanupSettings.setResolveConflictShapes(True)

osmSettings = OSMImportSettings()

@noUIupdate
def nodeDistance(first, second) :
    posA = ce.getPosition(first)
    posB = ce.getPosition(second)
    dx =  posA[0]-posB[0]
    dy =  posA[1]-posB[1]
    dz =  posA[2]-posB[2]
    return math.sqrt(dx**2 + dy**2 + dz**2)
    
class Vertex(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        
    def __eq__(self, other):
        return (isinstance(other, self.__class__) and self.x == other.x and 
                self.y == other.y and self.z == other.z)

    def __ne__(self, other):
        return not self.__eq__(other)

class MMKGraphItem(object):
    def __init__(self, itemOID):
        self.OID = itemOID
        self.vertices = []

    def appendVertex(self, x, y, z):
        vertex = Vertex(x, y, z)
        self.vertices.append(vertex)
        
    def decodeAndAppendVertices(self, verticesList):
        for i in xrange(0,(len(verticesList)-1),3):
            self.appendVertex(verticesList[i], verticesList[i+1], verticesList[i+2])
    
    def __repr__(self):
        return self.OID + ' - positions: ' + str(self.vertices)        
    
    def __str__(self):
        __repr__()

class MMKGraphNode(object):
    def __init__(self, itemOID, shapes, vertex, type):
        self.OID = itemOID
        self.shapes = shapes
        self.vertex = vertex
        self.type = type

    def __repr__(self):
        return self.OID + ' - position: ' + str(self.vertex) + str(self.shapes)        
    
    def __str__(self):
        __repr__()
    
class MMKGraphSegment(object):
    def __init__(self, itemOID, fromNode, toNode, distance, lanes, maxspeed, shapes):
        self.OID = itemOID
        self.fromNode = fromNode
        self.toNode = toNode
        self.distance = distance
        self.lanes = lanes
        self.maxspeed = maxspeed
        self.shapes = shapes
    
    def __repr__(self):
        return self.OID + ' - from: ' + self.fromNode + ' to: ' + self.toNode + ' with distance: ' + str(self.distance) + ' and lanes: ' + str(self.lanes) 
    
    def __str__(self):
        __repr__()

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

def clipRegion(ce, config):
    # Remove any other layers created
    layers = ce.getObjectsFrom(ce.scene, ce.isLayer, ce.isGraphLayer, ce.withName('osm graph'))
    for layer in layers:
        if not ce.isGraphLayer(layer):
            ce.delete(layer)

    maxx = config.bbmaxx
    minx = config.bbminx
    maxz = -config.bbmaxz
    minz = -config.bbminz
    
    segments = ce.getObjectsFrom(ce.scene, ce.isGraphSegment)
    for segment in segments:    
        segmentVerteces = ce.getVertices(segment)
        endVerteces = []
        
        for i in xrange(0, len(segmentVerteces), 3):
            vertex = Vertex(segmentVerteces[i], segmentVerteces[i+1], segmentVerteces[i+2])
            endVerteces.append(vertex)

        if len(endVerteces) < 2:
            ce.delete(segment)
            continue
        
        highway = ce.getAttribute(segment, 'highway')
        if highway == None or not (highway in config.roads):
            ce.delete(segment)
            continue
        
        for vertex in endVerteces:
            if (vertex.x < minx or vertex.x > maxx or
                vertex.z > minz or vertex.z < maxz):
                ce.delete(segment)
                break

def attributeSegments(ce, config):
    segments = ce.getObjectsFrom(ce.scene, ce.isGraphSegment)
    
    for segment in segments:
        highway = ce.getAttribute(segment, 'highway')
        maxspeed = ce.getAttribute(segment, 'maxspeed')
        lanes = ce.getAttribute(segment, 'lanes')
        
        if highway == None:
            ce.setAttribute(segment, 'highway', 'residential')
        elif not (highway in config.roads):
            raise Exception('Road \''+ highway + '\'not recognosed!')
        
        if maxspeed == None or maxspeed <= 0:
            maxspeed = config.roads[highway].maxspeed
            ce.setAttribute(segment, 'maxspeed', maxspeed)
        
        if lanes == None or lanes <= 0:
            lanes = config.roads[highway].lanes
            ce.setAttribute(segment, 'lanes', lanes)
                
def attributeNodes(ce, config):
    nodes = ce.getObjectsFrom(ce.scene, ce.isGraphNode)
    
    for node in nodes:
        # Get neighbour segments
        segments = ce.getObjectsFrom(node, ce.isGraphSegment)
        segmentsCount = len(segments)
        
        if segmentsCount == 1:
            # Reached an end node
            ce.setAttribute(node, 'type', 'end')
        elif segmentsCount == 2:
            # Two streets connecting: If they are the same type we can merge them;
            # otherwise it will be a (not-real-)junction with no signals 
            if (ce.getAttribute(segments[0], 'lanes') == ce.getAttribute(segments[1], 'lanes') and
                ce.getAttribute(segments[0], 'maxspeed') == ce.getAttribute(segments[1], 'maxspeed') and
                ce.getAttribute(segments[0], 'highway') == ce.getAttribute(segments[1], 'highway')):
                ce.setAttribute(node, 'type', 'merge')
            else:
                ce.setAttribute(node, 'type', 'connect')
        else:
            # Ordinary junction - try to determine the signals
            if ce.getAttribute(node, 'highway') == 'traffic_signals':
                ce.setAttribute(node, 'type', 'traffic_lights')
                continue
            elif ce.getAttribute(node, 'highway') == 'stop':
                ce.setAttribute(node, 'type', 'stop_sign')
                continue
            else:
                types = set()
                maxPriority = 0
                maxType = 'residential'
                for segment in segments:
                    highway = ce.getAttribute(segment, 'highway')
                    types.add(highway)
                    priority = config.roads[highway].priority
                    if priority > maxPriority:
                        maxPriority = priority
                        maxType = highway
                       
                if len(types) == 1: # only same-priority ways
                    ce.setAttribute(node, 'type', config.roads[maxType].samePriority)
                else:
                    ce.setAttribute(node, 'type', config.roads[maxType].differentPriority)

def getShapes(element):
    shapes = ce.getObjectsFrom(element, ce.isShape)
    items = []
    
    for shape in shapes:
        item = MMKGraphItem(ce.getOID(shape))
        item.decodeAndAppendVertices(ce.getVertices(shape))
        items.append(item)
    
    return items    
                    
def exportStreetnetworkData(ce):
    nodes = ce.getObjectsFrom(ce.scene, ce.isGraphNode)
    
    graphNodes = []
    graphSegments = []
    
    for node in nodes:
        type = ce.getAttribute(node, 'type')
        segments = ce.getObjectsFrom(node, ce.isGraphSegment)
        
        if len(segments) <= 0 or type == 'merge':
            continue
        
        nodesShapes = getShapes(node)
        graphNodes.append(MMKGraphNode(ce.getOID(node), nodesShapes, ce.getPosition(node), ce.getAttribute(node ,'type'))) 
        for segment in segments:
            finished = ce.getAttribute(segment, 'finished')
            if finished != None and finished == 'true':
                continue
            
            oneway = ce.getAttribute(segment, 'oneway') == 'yes'
            maxspeed = ce.getAttribute(segment, 'maxspeed')
            lanes = ce.getAttribute(segment, 'lanes')
            lanesBack = ce.getAttribute(segment, 'lanes:backward')
            lanesForw = ce.getAttribute(segment, 'lanes:forward')
            shapes = []
            distance = 0
            
            nextSegment = segment
            nextNode = node
            while True:
                ce.setAttribute(nextSegment, 'finished', 'true')
                segmentsNodes = ce.getObjectsFrom(nextSegment, ce.isGraphNode)
                
                if len(segmentsNodes) < 2:
                    raise Exception('The segment ' + ce.getOID(nextSegment) + ' was not valid!')
                
                shapes += getShapes(nextSegment)
                
                oldNode = nextNode
                
                # Take the next node
                if ce.getOID(nextNode) == ce.getOID(segmentsNodes[0]): 
                    nextNode = segmentsNodes[1]
                else:
                    nextNode = segmentsNodes[0]
                
                distance += nodeDistance(oldNode, nextNode)
                
                # This is already a real junction
                if ce.getAttribute(nextNode, 'type') != 'merge':
                    break
                
                newSegments = ce.getObjectsFrom(nextNode, ce.isGraphSegment)
                
                # Take the next segment
                if ce.getOID(nextSegment) == ce.getOID(newSegments[0]): 
                    nextSegment = newSegments[1]
                else:
                    nextSegment = newSegments[0]

            segmentsNodes = ce.getObjectsFrom(nextSegment, ce.isGraphNode)
                
            if len(segmentsNodes) < 2:
                raise Exception('The segment ' + ce.getOID(nextSegment) + ' was not valid!')
         
            if ce.getOID(node) == ce.getOID(segmentsNodes[0]): 
                start = node
                end = nextNode
            else:
                start = nextNode
                end = node
            
            if lanesForw != None:
                lanes = lanesForw
            else:
                if not oneway:
                    lanes = int(lanes) / 2
            
            # Add segment from start to end
            edge = MMKGraphSegment(ce.getOID(segment)+':a', ce.getOID(start), ce.getOID(end), distance, lanes, maxspeed, shapes)
            graphSegments.append(edge)
            
            if not oneway:
                if lanesBack != None:
                    lanes = lanesBack
                
                # Add segment from end to start
                edge = MMKGraphSegment(ce.getOID(segment)+':b', ce.getOID(end), ce.getOID(start), distance, lanes, maxspeed, shapes)
                graphSegments.append(edge)

    print(graphNodes)
    print(graphSegments)
                    
def cleanupGraph(ce, cleanupSettings):
    graphlayer = ce.getObjectsFrom(ce.scene, ce.isGraphLayer)
    ce.cleanupGraph(graphlayer, cleanupSettings)

@noUIupdate
def export(ce, config):
    print('Cleaning up old imports...')
    
    # Delete all old layers
    layers = ce.getObjectsFrom(ce.scene, ce.isLayer, ce.withName("'osm graph'"))
    ce.delete(layers)
    
    print('Import OSM data...')
    
    # Import osm map
    graphLayers = ce.importFile(ce.toFSPath('data/tum.osm'), osmSettings, False )
        
    for graphLayer in graphLayers :
        ce.setName(graphLayer, 'osm graph')
    
    # Delete not drivable roads and roads outside of the specified bounding box and cleanup
    clipRegion(ce, config)
    cleanupGraph(ce, cleanupSettings)
    
    print('Attributing segments and nodes...')
    
    # Make sure all nodes and segments have correct attributes
    attributeSegments(ce, config)
    attributeNodes(ce, config)
    
    print('Exporting network...')
    
    exportStreetnetworkData(ce)
    
    print("Done")

if __name__ == '__main__':    
    export(ce, config)

    '''
    cc = CoordinatesConvertor()
    
    luis = ce.findByOID('3d39f005-20a5-11b2-a9aa-00e8564141bb')
    print(ce.getPosition([ce.findByOID('3d39f005-20a5-11b2-a9aa-00e8564141bb:2'), ce.findByOID('3d39f005-20a5-11b2-a9aa-00e8564141bb:1'), ce.findByOID('3d39f005-20a5-11b2-a9aa-00e8564141bb:0')]))
    osm_id = ce.getAttribute(luis, 'osm_id ')
    print("The OSM is " + str(osm_id))
    vertex = ce.getVertices(luis)
    print(cc.to_latlon(vertex[0], -vertex[2]))
    
    print(ce.getObjectsFrom(ce.findByOID('e0f15792-2342-11b2-806f-00e8564141bb'), ce.isGraphNode))
    '''