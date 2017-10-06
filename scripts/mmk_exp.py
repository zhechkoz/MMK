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
            self.nodes[str(item.OID)] = item
            if self.OSMOID.has_key(str(item.osmID)):
                raise ValueError('More than one node have the same OSM ID')
        elif isinstance(item, MMKGraphSegment):
            self.segments[str(item.OID)] = item            
        else:
            raise ValueError('GraphItem should be node or segment')

        self.OSMOID.setdefault(str(item.osmID), []).append(item.OID)
   
    def getNode(self, OID):
        return self.nodes.get(str(OID), None)

    
    def getSegment(self, OID):
        return self.segments.get(str(OID), None)

    def getNodeByOSMID(self, osmID):            
        return self.getNode(self.OSMOID.get(str(osmID), [''])[0])
    
    def getSegmentsByOSMID(self, osmID):            
        ids = self.OSMOID.get(str(osmID), [])
        segments = [self.getSegment(oid) for oid in ids] 
        return segments
    
    def collectLanesFromSUMOItems(self, sumoItems):
        for (id, nodes) in sumoItems.nodes.iteritems():
            ceNode = self.getNodeByOSMID(id)
            if not ceNode:
                continue

            for node in nodes:
                ceNode.appendLanes(node.lanes)

        for (id, edges) in sumoItems.edges.iteritems():
            if len(edges) == 1:
                lanes = edges[0].lanes
                if len(id) > 1 and id[0:2] == '--':
                    # Node is negative, ie backwards direction
                    segments = self.getSegmentsByOSMID(id[2:])
                    for segment in segments:
                        segment.appendLanes(lanes, forward=False)
                elif len(id) > 0 and id[0] == '-':
                    # It could be either a backward edge or a forward edge
                    # with a negative id (according to OSM IDs can be negative)
                    if sumoItems.edges.has_key(id[1:]):
                        # There is a forward edge so the current is backward
                        segments = self.getSegmentsByOSMID(id[1:])
                        for segment in segments:
                            segment.appendLanes(lanes, forward=False)
                    else:
                        # There is no forward edge so the current is a forward
                        # edge with negative sign
                        segments = self.getSegmentsByOSMID(id)
                        for segment in segments:
                            segment.appendLanes(lanes)
                else:
                    # This is a normal forward edge
                    segments = self.getSegmentsByOSMID(id)
                    for segment in segments:
                        segment.appendLanes(lanes)
                       
            else:
                if len(id) > 1 and id[0:2] == '--':
                    # Backwards edges
                    segments = self.getSegmentsByOSMID(id[2:])
                    if len(segments) == 1:
                        for edge in edges:
                            segments[0].appendLanes(edge.lanes, forward=False)
                    else:
                        pass
                elif len(id) > 0 and id[0] == '-':
                    if sumoItems.edges.has_key(id[1:]):
                        segments = self.getSegmentsByOSMID(id[1:])
                        if len(segments) == 1:
                            for edge in edges:
                                segments[0].appendLanes(edge.lanes, forward=False)
                        else:
                            pass
                    else:
                        segments = self.getSegmentsByOSMID(id)
                        if len(segments) == 1:
                            for edge in edges:
                                segments[0].appendLanes(edge.lanes)
                        else:
                            pass
                else:
                    segments = self.getSegmentsByOSMID(id)
                    if len(segments) == 1:
                        for edge in edges:
                            segments[0].appendLanes(edge.lanes)
                    else:
                        pass        
                        
    
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
        
    def calcLength(self, v1, v2):
        vabs = MMKGraphVertex(v2.x-v1.x, v2.y-v1.y, v2.z-v1.z)
        abs = math.sqrt(vabs.x**2 + vabs.y**2 + vabs.z**2) 
        return abs
        
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


class MMKGraphLane(MMKGraphItem):
    def __init__(self, itemOID, vertices, index, length):
        super(MMKGraphLane, self).__init__(itemOID, vertices)
        self.index = index
        self.length = length
        
    def reprJSON(self):
        dict = {'length' : self.length,
                'index' : self.index
        }
        dict.update(super(MMKGraphLane, self).reprJSON())
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

class SUMOItem(MMKGraphItem):
    def __init__(self, itemOID, vertices, order, start, end):
        super(SUMOItem, self).__init__(itemOID, vertices)
        self.order = order
        self.start = start
        self.end = end
        self.lanes = []
        
    def appendLane(self, id, vertices, index, length):
        lane = MMKGraphLane(id, vertices, index, length)
        self.lanes.append(lane)


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
    
    sumoFile = ce.toFSPath(config.sumo)
    if not os.path.isfile(sumoFile):
        print('WARNING: SUMO file not found! Lane information will not be generated!')
    else:
        sumoItems = parseSUMONet(sumoFile)
        MMKGraphObj.collectLanesFromSUMOItems(sumoItems)
        

def parseSUMONet(sumoFile):
    sumo = ET.parse(sumoFile)
    root = sumo.getroot()
    SumoItems = namedtuple('SumoItems', 'nodes, edges')
    sumoItems = SumoItems({}, {})

    for edge in root.findall('edge'):
        attrib = edge.attrib

        idOrder = re.split('_|#', attrib['id']) # If no order in id set it to 0
        (osmID, order) = (idOrder[0], idOrder[1] if len(idOrder) > 1 else '0')
        (start, end) = (attrib.get('from', ''), attrib.get('to', ''))
        vertices = []
        
        if attrib.has_key('shape'):
            for vertex in attrib['shape'].split(' '):
                (x, y) = vertex.split(',')
                vertices.extend((x, 0, y))

        sumoItem = SUMOItem(osmID, vertices, order, start, end)

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

            sumoItem.appendLane(id, vertices, index, length)
        
        if len(sumoItem.OID) > 0 and sumoItem.OID[0] == ':':
            # Nodes are always internal and start with a ':'
            sumoItem.OID = sumoItem.OID[1:]
            sumoItems.nodes.setdefault(sumoItem.OID, []).append(sumoItem)
        else:
            sumoItems.edges.setdefault(sumoItem.OID, []).append(sumoItem)

    return sumoItems
    
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
                      'oneway' : oneway,
                      'osmID' : osmID
    }
    
    return attributesDict

def attributeNode(node, neighbours, graph):
    numConnectedSegments = len(neighbours)
    osmID = int(ce.getAttribute(node, 'osm_id')) # All OSM IDs are integers
    hierarchy = 'unknown'
    
    if osmID == None:
        print('WARNING: node with invalid OSM ID found: ' + str(ce.getOID(node)))

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
                
    attributesDict = {'hierarchy' : hierarchy,
                      'osmID' : osmID
    }  
    return attributesDict
        
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