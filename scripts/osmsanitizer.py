import xml.etree.ElementTree as ET
import mmk_config as config

def sanitize(xml):
    for way in xml.findall('way'): 
        tags = dict([(tag.get('k'), tag.get('v')) for tag in way.findall('tag')])
        
        if not ('highway' in tags.keys()) or not (tags['highway'] in config.roads):
            xml.remove(way)

if __name__ == '__main__':
    osm = ET.parse('../data/tum.osm')
    root = osm.getroot()
    sanitize(root)
    osm.write('sanitized.osm')