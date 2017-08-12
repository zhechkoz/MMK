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

class Vertex():
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class CoordiantesConvertor():
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
  
def parseSegments(segments):
    for segment in segments:
        osm_id = ce.getAttribute(segment, 'osm_id ')
    
if __name__ == '__main__':
    cc = CoordiantesConvertor()
    
    nodes = ce.getObjectsFrom(ce.scene, ce.isGraphSegment)
    parseSegments(nodes) # Pass all segments

    '''
    luis = ce.findByOID('3d39f005-20a5-11b2-a9aa-00e8564141bb')
    print(ce.getPosition([ce.findByOID('3d39f005-20a5-11b2-a9aa-00e8564141bb:2'), ce.findByOID('3d39f005-20a5-11b2-a9aa-00e8564141bb:1'), ce.findByOID('3d39f005-20a5-11b2-a9aa-00e8564141bb:0')]))
    osm_id = ce.getAttribute(luis, 'osm_id ')
    print("The OSM is " + str(osm_id))
    #vertex = ce.getVertices(luis)
    #print(cc.to_latlon(vertex[0], -vertex[2]))
    '''
    print("Finished")