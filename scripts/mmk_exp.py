'''
Created on 25.02.2017

@author: murauermax and zhechkoz

'''
from scripting import *
import simplejson as json
import datetime
import errno
import os
import math
import utm

# Get a CityEngine instance
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
   
    def reprJSON(self):
        return dict(author=self.author, date=str(self.date), project=self.project, nodeCnt=self.nodeCnt, segementCnt=self.segmentCnt, nodes=self.nodes.values(), segments=self.segments.values())
        
    def setNodeCnt(self, nodeCnt):
        self.nodeCnt = nodeCnt
    
    def setSegmentCnt(self, segmentCnt):
        self.segmentCnt = segmentCnt
        
    def appendGraphItem(self, itemType, OID, vertices, attributesDict, neighbours):
        item = MMKGraphItem(OID,itemType, neighbours)
        item.decodeAndAppendVertices(vertices)
        item.appendAttributes(attributesDict)

        if itemType == 'node':
            self.nodes[str(OID)] = item
        elif itemType == 'segment':
            self.segments[str(OID)] = item
            item.calcLength(item.vertices[0], item.vertices[1])            
        else:
            raise ValueError('GraphItem should be node or segment')    
   
    def getNode(self, OID):
        if self.nodes.has_key(str(OID)):
            return self.nodes[str(OID)]
        else:
            print('No Node with OID: ' + str(OID) + ' found')
            return None
    
    def getSegment(self, OID):
        if self.segments.has_key(str(OID)):
            return self.segments[str(OID)]
        else:
            print('No Segment with OID: ' + str(OID) + ' found')
            return None
    
    def buildDirectionInformation(self):
        for s in self.segments.values():
            pass
    
    def exportJson(self, exportName):
        dir = ce.toFSPath('/' + ce.project())
        mkdir_p(os.path.join(dir, 'export'))
        dir = ce.toFSPath('export/' +  exportName)

        with open(dir, 'w+') as file:  
            file.write(json.dumps(self, indent=4, sort_keys=True, cls=ComplexEncoder))
        print('File exported! Location: ' + dir + '\n')
      
 
class MMKGraphItem(object):
    
    def __init__(self, itemOID, itemType, neighbours = []):
        self.OID = itemOID
        self.vertices = []
        self.itemType = itemType
        self.dict = dict(OID=str(self.OID), itemType=self.itemType, vertices=self.vertices)
        
        if self.itemType != 'shape':
            self.shapes = []
            self.dict.update(shapes=self.shapes)
        
        if self.itemType == 'segment':
            if len(neighbours) != 2:
                raise ValueError('Segments should have exactly two end nodes!')

            self.start = neighbours[0]
            self.end = neighbours[1]
            self.dict.update({'start' : self.start, 'end' : self.end})
        
        if self.itemType == 'node':
            self.corrSegments = neighbours
            self.dict.update(corrSegments=self.corrSegments)

    def reprJSON(self):
        return self.dict  
    
    def calcLength(self, v1, v2):
        vabs = MMKGraphItemVertex(v2.x-v1.x, v2.y-v1.y, v2.z-v1.z)
        abs = math.sqrt(vabs.x**2 + vabs.y**2 + vabs.z**2)
        
        if self.itemType == 'segment':
            self.segmentLength = abs
            self.dict.update(segmentLength=self.segmentLength) 
        
        return abs            
               
    def appendVertex(self, x, y, z):
        vertex = MMKGraphItemVertex(x, y, z)
        self.vertices.append(vertex)
        
    def decodeAndAppendVertices(self, verticesList):
        for i in xrange(0,(len(verticesList)-1),3):
            self.appendVertex(verticesList[i], verticesList[i+1], verticesList[i+2])            
            
    def appendAttributes(self, attributesDict):
        self.dict.update(attributesDict)
        for (key, value) in attributesDict.iteritems():
            setattr(self, key, value)             

    def appendShapes(self, shapeOID, vertices):
        shape = MMKGraphItem(shapeOID,'shape')
        shape.decodeAndAppendVertices(vertices)
        
        if self.itemType != 'shape':
            self.shapes.append(shape)
        else: 
            raise ValueError('Shapes can not be appendend to shapes')
    
    def appendLane(self, laneOID):
        pass

class MMKGraphSegment(MMKGraphItem):
    def __init__(self, itemOID, neighbour):
        super(MMKGraphSegment, self).__init__(itemOID)
        
        if len(neighbours) != 2:
                raise ValueError('Segments should have exactly two end nodes!')

        self.start = neighbours[0]
        self.end = neighbours[1]
        
class MMKGraphItemVertex(object):      
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        
    def reprJSON(self):
        return dict(x=self.x ,y=self.y ,z=self.z)


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
            
        MMKGraphObj.appendGraphItem('segment', ce.getOID(o), ce.getVertices(o), attributesDict, neighboursList)
        
        shapes = ce.getObjectsFrom(o, ce.isShape)
                
        for s in shapes:
            segment = MMKGraphObj.getSegment(ce.getOID(o))
            segment.appendShapes(ce.getOID(s), ce.getVertices(s)) 
            
            
    # Parse nodes
    
    nodes = ce.getObjectsFrom(ce.scene, ce.isGraphNode)
    MMKGraphObj.setNodeCnt(len(nodes))    
    for o in nodes:
        neighbours = ce.getObjectsFrom(o, ce.isGraphSegment)
        neighboursList = []
        
        for neighbour in neighbours:
            neighboursList.append(ce.getOID(neighbour)) 
        
        attributesDict = attributeNode(o, neighboursList, MMKGraphObj)
        
        MMKGraphObj.appendGraphItem('node', ce.getOID(o), ce.getVertices(o), attributesDict, neighboursList)
        
        shapes = ce.getObjectsFrom(o, ce.isShape)
        
        for s in shapes:    
            node = MMKGraphObj.getNode(ce.getOID(o))
            node.appendShapes(ce.getOID(s), ce.getVertices(s)) 

    # Split segments into lanes
    MMKGraphObj.buildDirectionInformation()

def attributeSegment(segment):
    highway = ce.getAttribute(segment, 'highway')
    maxspeed = ce.getAttribute(segment, 'maxspeed')
    lanes = ce.getAttribute(segment, 'lanes')
    oneway = ce.getAttribute(segment, 'oneway') == 'yes'
    lanesBackward = ce.getAttribute(segment, 'lanes:backward')
    lanesForward = ce.getAttribute(segment, 'lanes:forward')
    osmID = int(ce.getAttribute(segment, 'osm_id')) # All OSM IDs are integers
    
    if osmID == None:
        print('WARNING: segment with invalid OSM ID found: ' + str(ce.getOID(segment)))
    
    if maxspeed == None or maxspeed <= 0:
        maxspeed = config.roads[highway].maxspeed
    
    if lanes == None or lanes <= 0:
        if oneway:
            lanes = 1
        else:
            lanes = config.roads[highway].lanes
    
    totalLanes = {'number' : lanes}
    if lanesBackward:
        totalLanes['backward'] = {'number' : lanesBackward}
    if lanesForward:
        totalLanes['forward'] = {'number' : lanesForward}
    
    attributesDict = {'hierarchy' : highway, 'maxspeed' : maxspeed, 'lanes' : totalLanes, 'oneway' : oneway, 'osm' : osmID}
    
    return attributesDict

def attributeNode(node, neighbours, graph):
    numConnectedSegments = len(neighbours)
    hierarchy = 'unknown'

    if numConnectedSegments == 1:
        # Reached an end node
        hierarchy = 'end'
    elif numConnectedSegments == 2:
        # Two streets connecting; not-real-junction
        hierarchy = 'connect'
    else:
        # Ordinary junction - try to determine the signals
        if ce.getAttribute(node, 'highway') == 'traffic_signals':
            hierarchy = 'traffic_lights'
        elif ce.getAttribute(node, 'highway') == 'stop':
            hierarchy = 'stop_sign'
        else:
            types = set()
            maxPriority = 0
            maxType = 'residential'
            for segmentOID in neighbours:
                segment = graph.getSegment(segmentOID)
                types.add(segment.hierarchy)
                priority = config.roads[segment.hierarchy].priority
                if priority > maxPriority:
                    maxPriority = priority
                    maxType = segment.hierarchy
                    
            # Set the hierarchy of the junction to either regulate two same-priority
            # ways; otherwise choose what the other lower priority ways have to do 
            # in order to give priority to the main road.
            if len(types) == 1: # only same-priority ways
                hierarchy = config.roads[maxType].samePriority
            else: # more than one type of priority
                hierarchy = config.roads[maxType].differentPriority
    return {'hierarchy' : hierarchy}
        
    
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

    
def clipRegion():
    # Remove any other layers created
    layers = ce.getObjectsFrom(ce.scene, ce.isLayer, ce.isGraphLayer, ce.withName('osm graph'))
    for layer in layers:
        if not ce.isGraphLayer(layer):
            ce.delete(layer)
    
    segments = ce.getObjectsFrom(ce.scene, ce.isGraphSegment)
    for segment in segments:
        segmentVerteces = ce.getVertices(segment)
        endVerteces = []
        
        for i in xrange(0, len(segmentVerteces), 3):
            vertex = MMKGraphItemVertex(abs(segmentVerteces[i]), abs(segmentVerteces[i+1]), abs(segmentVerteces[i+2]))
            endVerteces.append(vertex)

        if len(endVerteces) < 2:
            ce.delete(segment)
            continue
        
        highway = ce.getAttribute(segment, 'highway')
        if highway == None or not (highway in config.roads):
            ce.delete(segment)
            continue
        
        for vertex in endVerteces:
            if (vertex.x < config.bbminx or vertex.x > config.bbmaxx or
                vertex.z < config.bbminz or vertex.z > config.bbmaxz):
                ce.delete(segment)
                break

@noUIupdate
def prepareScene():
    print('Cleaning up old imports...')
    
    # Delete all old layers
    layers = ce.getObjectsFrom(ce.scene, ce.isLayer, ce.withName("'osm graph'"))
    ce.delete(layers)
    
    print('Importing OSM data...')
    
    osmFile = ce.toFSPath(config.osm)
    if not os.path.isfile(osmFile):
        raise ValueError('OSM file not found!')

    # Import OSM data
    graphLayers = ce.importFile(osmFile, osmSettings, False)
        
    for graphLayer in graphLayers:
        ce.setName(graphLayer, 'osm graph')
    
    # Delete not drivable roads and roads outside of the specified bounding box and cleanup
    clipRegion() # TODO: Move to osm sanitisation script!
    cleanupGraph()
    
if __name__ == '__main__':
    
    print('MMK Streetnetwork Export\n')
    #prepareScene()
   
    graph = MMKGraph()
    print('Building streetnetwork...')
    
    parseGraph("Streetnetwork", graph)
    graph.exportJson('MMK_GraphExport.json')
    
    print('Finished. Success!\n')