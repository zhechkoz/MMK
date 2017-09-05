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

# Define bounding box
bbminx = 690370.0
bbmaxx = 691600.0
bbminz = 5335624.0
bbmaxz = 5336828.0

# Define center coordinates
ox = 690985
oz = 5336220

roads = ['motorway', 'motorway_link', 'trunk', 'trunk_link', 'primary', 'primary_link', 'secondary','secondary_link', 'tertiary', 'tertiary_link', 'unclassified', 'residential', 'living_street', 'unsurfaced']

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
        self.pred = []
        self.succ = []
        
    def appendPred(self, pred):
        self.pred.append(pred)
    
    def appendSucc(self, succ):
        self.succ.append(succ)
        
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

def clipRegion(ce):
    # Remove any other layers created
    layers = ce.getObjectsFrom(ce.scene, ce.isLayer, ce.isGraphLayer, ce.withName('osm graph'))
    for layer in layers:
        if not ce.isGraphLayer(layer):
            ce.delete(layer)

    maxx = bbmaxx
    minx = bbminx
    minz = -bbminz
    maxz = -bbmaxz
    
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
        if highway == None or not (highway in roads):
            ce.delete(segment)
            continue
        
        for vertex in endVerteces:
            if (vertex.x < minx or vertex.x > maxx or
                vertex.z > minz or vertex.z < maxz):
                ce.delete(segment)
                break

if __name__ == '__main__':
    clipRegion(ce)
    '''
    cc = CoordinatesConvertor()
    
    luis = ce.findByOID('3d39f005-20a5-11b2-a9aa-00e8564141bb')
    print(ce.getPosition([ce.findByOID('3d39f005-20a5-11b2-a9aa-00e8564141bb:2'), ce.findByOID('3d39f005-20a5-11b2-a9aa-00e8564141bb:1'), ce.findByOID('3d39f005-20a5-11b2-a9aa-00e8564141bb:0')]))
    osm_id = ce.getAttribute(luis, 'osm_id ')
    print("The OSM is " + str(osm_id))
    vertex = ce.getVertices(luis)
    print(cc.to_latlon(vertex[0], -vertex[2]))
    
    print(ce.getObjectsFrom(ce.findByOID('7fbbe827-1fdd-11b2-8655-00e8564141bb'), ce.isGraphNode))
    '''
    print("Finished")