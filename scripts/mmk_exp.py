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

class Vertex(object):
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        
class MMKGraphItem(object):
    def __init__(self, itemUUID, osm_id):
        self.UUID = itemUUID
        self.osm_id = int(osm_id)
        self.vertices = []
        self.pred = []
        self.succ = []
        
    def appendPred(pred):
        self.pred.append(pred)
    
    def appendSucc(succ):
        self.succ.append(succ)
        
    def appendVertex(self, x, y, z):
        vertex = Vertex(x, y, z)
        self.vertices.append(vertex)
    
    def __str__(self):
        __repr__()
        
    def __repr__(self):
        return str(self.osm_id) + ', ' + str(self.pred) + ', ' + str(self.succ)

class CoordiantesConvertor(object):
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
    items = []
    for segment in segments:
        if (ce.getAttribute(segment, 'highway') == 'residential' or
            ce.getAttribute(segment, 'highway') == 'secondary' or
            ce.getAttribute(segment, 'highway') == 'primary' or
            ce.getAttribute(segment, 'highway') == 'motorway'):
            
            item = MMKGraphItem(ce.getOID(segment), ce.getAttribute(segment, 'osm_id'))
            verticesList=ce.getVertices(segment)
            
            for i in xrange(0, (len(verticesList)-1),3):
                item.appendVertex(verticesList[i], verticesList[i+1], verticesList[i+2]) 
            
            items.append(item)
            
    osm = ET.parse('C:\\Users\\Zhechev\\Documents\\IDP\\MMK\\scripts\\tum.osm')
    wayEndpoints = {}
    
    for item in items:
        way = osm.find("./way[@id='" + str(item.osm_id) + "']")
        if way == None:
            print('Warning: ' + str(item.osm_id) + ' is not valid and will be omitted!')
            continue

        # Find all nodes in the current way
        nodes = way.findall('nd')
       
        # OSM format guarantees 2 nodes per valid way element
        firstNode = nodes[0].get('ref')
        lastNode = nodes[-1].get('ref')
        
        # Collect the two endpoints
        wayEndpoints[item.osm_id] = (firstNode, lastNode)
    
    for i in xrange(0, len(items)):
        for j in xrange(i+1, len(items)):
            #
            if ((items[i].vertices[0].x == items[j].vertices[0].x and items[i].vertices[0].y == items[j].vertices[0].y and
                items[i].vertices[0].z == items[j].vertices[0].z) or
                (items[i].vertices[1].x == items[j].vertices[1].x and items[i].vertices[1].y == items[j].vertices[1].y and
                items[i].vertices[1].z == items[j].vertices[1].z)):
                
                firstEndPoints = wayEndpoints.get(items[i].osm_id, None)
                secondEndPoints = wayEndpoints.get(items[j].osm_id, None)
                
                if not firstEndPoints or not secondEndPoints:
                    print('Error: No data about segment ' + str(items[i].osm_id) + ' or ' + str(items[j].osm_id))
                    continue
                
                if wayEndpoints[items[i].osm_id][0] == wayEndpoints[items[j].osm_id][1]:
                    items[i].appendPred(items[j].osm_id)
                    items[j].appendSucc(items[i].osm_id)
                elif wayEndpoints[items[i].osm_id][1] == wayEndpoints[items[j].osm_id][0]:
                    items[i].appendSucc(items[j].osm_id)
                    items[j].appendPred(items[i].osm_id)
                else:
                    print('Error: Segments are not neighbours in map world!')
              
    print(items)           
   
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