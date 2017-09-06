'''
Created on Apr 23, 2017

@author: Zhechev
'''
from scripting import *
import sys
import xml.etree.cElementTree as ET
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
    def __init__(self, itemUUID, osm_id):
        self.UUID = itemUUID
        self.osm_id = int(osm_id)
        self.vertices = []
        
    def appendVertex(self, x, y, z):
        vertex = Vertex(x, y, z)
        self.vertices.append(vertex)
    
    def __str__(self):
        __repr__()
        
    def __repr__(self):
        return str(self.osm_id) + ', ' + str(self.pred) + ', ' + str(self.succ)

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
                
def cleanupGraph(ce, cleanupSettings):
    graphlayer = ce.getObjectsFrom(ce.scene, ce.isGraphLayer)
    ce.cleanupGraph(graphlayer, cleanupSettings)
    
if __name__ == '__main__':
    
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

    '''
    cc = CoordinatesConvertor()
    
    luis = ce.findByOID('3d39f005-20a5-11b2-a9aa-00e8564141bb')
    print(ce.getPosition([ce.findByOID('3d39f005-20a5-11b2-a9aa-00e8564141bb:2'), ce.findByOID('3d39f005-20a5-11b2-a9aa-00e8564141bb:1'), ce.findByOID('3d39f005-20a5-11b2-a9aa-00e8564141bb:0')]))
    osm_id = ce.getAttribute(luis, 'osm_id ')
    print("The OSM is " + str(osm_id))
    vertex = ce.getVertices(luis)
    print(cc.to_latlon(vertex[0], -vertex[2]))
   
    print(ce.getObjectsFrom(ce.findByOID('8db5030b-25bf-11b2-9c1e-00e8564141bb'), ce.isGraphSegment))
    '''
    print("Done")