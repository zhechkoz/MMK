'''
Created on 25.02.2017

@author: murauermax and zhechkoz

'''
from scripting import *
import simplejson as json
import xml.etree.ElementTree as ET
import datetime
import errno
import os, sys
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
            self.nodes[str(item.OID)] = item
        elif isinstance(item, MMKGraphSegment):
            self.segments[str(item.OID)] = item           
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

    def reprJSON(self):
        return dict(ID=str(self.OID), vertices=self.vertices)             
               
    def appendVertex(self, x, y, z):
        vertex = MMKGraphVertex(x, y, z)
        self.vertices.append(vertex)
        
    def decodeAndAppendVertices(self, verticesList):
        # TODO: Apply transformation for every point to match Unity CS
        for i in xrange(0,(len(verticesList)-1),3):
            self.appendVertex(verticesList[i], verticesList[i+1], verticesList[i+2])

    def decodeAttributes(self, attributesDict):
        for (key, value) in attributesDict.iteritems():
            setattr(self, key, value)

class MMKGraphSegment(MMKGraphItem):
    def __init__(self, itemOID, vertices, attributesDict, neighbours):
        super(MMKGraphSegment, self).__init__(itemOID, vertices)
        
        if len(neighbours) != 2:
                raise ValueError('Segments should have exactly two end nodes!\n' + str(self.itemOID))
        
        self.start = neighbours[0]
        self.end = neighbours[1]
        self.length = self.calcLength(self.vertices[0], self.vertices[1])
        self.shapes = []
        self.lanesForward = []
        self.lanesBackward = []
        self.decodeAttributes(attributesDict)
        self.determineNumberOfLanes()
        
    def calcLength(self, v1, v2):
        vabs = MMKGraphVertex(v2.x-v1.x, v2.y-v1.y, v2.z-v1.z)
        abs = math.sqrt(vabs.x**2 + vabs.y**2 + vabs.z**2) 
        return abs
        
    def appendShapes(self, shapeOID, vertices):
        shape = MMKGraphShape(shapeOID, vertices)
        self.shapes.append(shape)
    
    # TODO: Can be deleted because we get the lanes from SUMO?
    def determineNumberOfLanes(self):
        if not hasattr(self, 'totalLanesForward'):
            if self.oneway:
                self.totalLanesForward = self.totalLanes
            else:
                self.totalLanesForward = self.totalLanesBackward = int(self.totalLanes) / 2

    def appendLane(self, lane):
        raise Exception('Not Implemented!')
        
    def reprJSON(self):
        totalLanes = {'number' : self.totalLanes}
        totalLanes['forward'] = {'number' : self.totalLanesForward}
        if hasattr(self, 'totalLanesBackward'):
            totalLanes['backward'] = {'number' : self.totalLanesBackward}
            
        dict = {'hierarchy' : self.hierarchy, 
                'maxspeed' : self.maxspeed, 
                'lanes' : totalLanes,
                'oneway' : self.oneway,
                'osm' : self.osmID, 
                'length' : self.length, 
                'start' : self.start, 
                'end' : self.end, 
                'shapes' : self.shapes
        }

        dict.update(super(MMKGraphSegment, self).reprJSON())
        return dict
        
class MMKGraphShape(MMKGraphItem):
    def __init__(self, itemOID, vertices):
        super(MMKGraphShape, self).__init__(itemOID, vertices)
    
    def reprJSON(self):
        return super(MMKGraphShape, self).reprJSON()

class MMKGraphLane(MMKGraphItem):
    def __init__(self, itemOID, vertices, index, length):
        super(MMKGraphLane, self).__init__(itemOID, vertices)
        self.index = index
        self.length = length
        
    def reprJSON(self):
        dict = {'length' : self.length,
                'index' : self.index
        }
        dict.update(super(MMKGraphSegment, self).reprJSON())
        return dict
  
class MMKGraphNode(MMKGraphItem):
    def __init__(self, itemOID, vertices, attributesDict, neighbours):
        super(MMKGraphNode, self).__init__(itemOID, vertices)
        
        self.decodeAttributes(attributesDict)
        self.corrSegments = neighbours
        self.shapes = []
        self.lanes = []

    def appendShapes(self, shapeOID, vertices):
        shape = MMKGraphShape(shapeOID, vertices)
        self.shapes.append(shape)

    def appendLane(self, lane):
        raise Exception('Not Implemented!')

    def reprJSON(self):
        dict = {'hierarchy' : self.hierarchy, 
                'corrSegments' : self.corrSegments, 
                'shapes' : self.shapes
        }
        
        dict.update(super(MMKGraphNode, self).reprJSON())
        return dict
        

class MMKGraphVertex(object):      
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        
    def reprJSON(self):
        return dict(x=self.x, 
                    y=self.y, 
                    z=self.z
               )

class SUMOEdge(MMKGraphItem):
    def __init__(self, itemOID, vertices, order, start, end):
        super(SUMOEdge, self).__init__(itemOID, vertices)
        self.order = order
        self.start = start
        self.end = end
        self.lanes = []
        
    def appendLane(self, lane):
        self.lanes.append(lane)
    
    def __str__(self):
        __repr__()

    def __repr__(self):
        return str(super(SUMOEdge, self).reprJSON()) + ' -- ' + str(self.order) + ' -- ' + str(self.start) + ' -- ' + str(self.end)
    

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
        
    # Parse SUMO Lanes
    
    sumoFile = ce.toFSPath(config.sumo)
    if not os.path.isfile(sumoFile):
        print('SUMO file not found! Lane information will not be generated!')
        return
   
    sumo = ET.parse(sumoFile)
    root = sumo.getroot()
    sumoEdges = []

    for edge in root.findall('edge'):
        attrib = edge.attrib
        id = attrib['id'][1:] # Ignore the first ':'

        if '_' in id or '#' in id:
            (osmID, order) = id.replace('_', '#').split('#')
        else:
            osmID = id
            order = 0
            
        vertices = []
        (start, end) = (attrib.get('from', ''), attrib.get('to', ''))
        
        if attrib.has_key('shape'):
            for vertex in attrib['shape'].split(' '):
                (x, y) = vertex.split(',')
                vertices.extend((x, 0, y))

        sumoEdge = SUMOEdge(osmID, vertices, order, start, end)

        for lane in edge.findall('lane'):
            attrib = lane.attrib
            id = attrib['id']
            length = attrib.get('length', 0)
            index = attrib.get('index', 0)
            vertices = []
            
            if attrib.has_key('shape'):
                for vertex in attrib['shape'].split(' '):
                    (x, y) = vertex.split(',')
                    vertices.extend((x, 0, y))
            
            lane = MMKGraphLane(id, vertices, index, length)
            sumoEdge.appendLane(lane)
        
        sumoEdges.append(sumoEdge)
    print(sumoEdges)
    

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
        print('WARNING: segment with invalid maxspeed found: ' + str(ce.getOID(segment)))
    
    if lanes == None or lanes <= 0:
        print('WARNING: segment with invalid lanes found: ' + str(ce.getOID(segment)))
    
    attributesDict = {'hierarchy' : highway, 
                      'maxspeed' : maxspeed, 
                      'totalLanes' : lanes,
                      'oneway' : oneway,
                      'osmID' : osmID
    }
    
    if lanesBackward:
        attributesDict['totalLanesBackward'] = lanesBackward
    if lanesForward:
        attributesDict['totalLanesForward'] = lanesForward
    
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

    cleanupGraph()
    
if __name__ == '__main__':
    
    print('MMK Streetnetwork Export\n')
    #prepareScene()
   
    graph = MMKGraph()
    print('Building streetnetwork...')
    
    parseGraph("Streetnetwork", graph)
    graph.exportJson('MMK_GraphExport.json')
    
    print('Finished. Success!\n')