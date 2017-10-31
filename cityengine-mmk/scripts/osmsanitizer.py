'''
Created on 27.09.2017

@author: zhechkoz

'''
import argparse
import xml.etree.ElementTree as ET
from collections import namedtuple

Road = namedtuple('Road', 'maxspeed lanes')

roads = {'motorway' : Road(maxspeed = 130, lanes = 6),
         'motorway_link' : Road(maxspeed = 70, lanes = 4),
         'trunk' : Road(maxspeed = 90, lanes = 4),
         'trunk_link' : Road(maxspeed = 70, lanes = 4),
         'primary' : Road(maxspeed = 50, lanes = 4),
         'primary_link' : Road(maxspeed = 50, lanes = 4),
         'secondary' : Road(maxspeed = 50, lanes = 4),
         'secondary_link' : Road(maxspeed = 50, lanes = 4),
         'tertiary' : Road(maxspeed = 50, lanes = 2),
         'tertiary_link' : Road(maxspeed = 50, lanes = 2),
         'unclassified' : Road(maxspeed = 50, lanes = 2),
         'residential' : Road(maxspeed = 50, lanes = 2),
         'living_street' : Road(maxspeed = 25, lanes = 2),
         'unsurfaced' : Road(maxspeed = 20, lanes = 2),
         'service' : Road(maxspeed = 20, lanes = 2)
}

def sanitize(xml):
    for way in xml.findall('way'): 
        tags = dict([(tag.get('k'), tag.get('v')) for tag in way.findall('tag')])

        if 'highway' in tags:
            if not (tags['highway'] in roads):
                xml.remove(way)
            else:
                highway = tags['highway']
                maxspeed = tags.get('maxspeed', None)
                lanes = tags.get('lanes', None)
                oneway = tags.get('oneway', None) == 'yes'
                
                if not maxspeed:
                    correctMaxspeed = roads[highway].maxspeed
                    ET.SubElement(way, 'tag', attrib={'k' : 'maxspeed', 'v' : str(correctMaxspeed)})
                elif int(maxspeed) <= 0:
                    correctMaxspeed = roads[highway].maxspeed
                    for tag in way.iter('tag'):
                        if tag.get('k') == 'maxspeed':
                            tag.set('v', str(correctMaxspeed))
                            break
                
                if not lanes:
                    if oneway:
                        lanes = 1 
                    else:
                        lanes = roads[highway].lanes
                    
                    ET.SubElement(way, 'tag', attrib={'k' : 'lanes', 'v' : str(lanes)})
        elif 'building' in tags and tags['building'] == 'yes':
            pass
        elif 'amenity' in tags and tags['amenity'] == 'parking':
            pass
        else:
            xml.remove(way)
                    
    for relation in xml.findall('relation'): 
        tags = dict([(tag.get('k'), tag.get('v')) for tag in way.findall('tag')])
        if 'highway' in tags and not (tags['highway'] in roads):
            xml.remove(relation)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Remove unnecessary way and relation tags in the OSM export file.')
    parser.add_argument('osmFile', help='Path and name to the OSM export file.')

    args = parser.parse_args()
    
    osm = ET.parse(args.osmFile)
    root = osm.getroot()
    sanitize(root)
    osm.write(args.osmFile[:-4] + '-sanitized.osm')
