import xml.etree.ElementTree as ET
import mmk_config as config

def sanitize(xml):
    for way in xml.findall('way'): 
        tags = dict([(tag.get('k'), tag.get('v')) for tag in way.findall('tag')])
        if 'highway' in tags.keys():
            if not (tags['highway'] in config.roads):
                xml.remove(way)
            else:
                highway = tags['highway']
                maxspeed = tags.get('maxspeed', None)
                lanes = tags.get('lanes', None)
                oneway = tags.get('oneway', None) == 'yes'
                
                if not maxspeed:
                    correctMaxspeed = config.roads[highway].maxspeed
                    ET.SubElement(way, 'tag', attrib={'k' : 'maxspeed', 'v' : str(correctMaxspeed)})
                elif int(maxspeed) <= 0:
                    correctMaxspeed = config.roads[highway].maxspeed
                    for tag in way.iter('tag'):
                        if tag.get('k') == 'maxspeed':
                            tag.set('v', str(correctMaxspeed))
                            break
                
                if not lanes:
                    if oneway:
                        lanes = 1 
                    else:
                        lanes = config.roads[highway].lanes
                    
                    ET.SubElement(way, 'tag', attrib={'k' : 'lanes', 'v' : str(lanes)})
        elif 'building' in tags.keys() and tags['building'] == 'yes':
            pass
        else:
            xml.remove(way)
                    
    for relation in xml.findall('relation'): 
        tags = dict([(tag.get('k'), tag.get('v')) for tag in way.findall('tag')])
        if 'highway' in tags.keys() and not (tags['highway'] in config.roads):
            xml.remove(relation)

if __name__ == '__main__':
    osm = ET.parse('../data/tum.osm')
    root = osm.getroot()
    sanitize(root)
    osm.write('sanitized.osm')