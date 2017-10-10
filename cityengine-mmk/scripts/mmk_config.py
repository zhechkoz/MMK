'''
Created on 01.09.2017

@author: zhechkoz

'''
# Define OSM data location
osm = 'data/tum.osm'
sumo = 'data/tum.net.xml'

# Define center coordinates
ox = 690985
oz = 5336220

sumoox = 606
sumooz = 596

class Road(object):
    def __init__(self, priority, maxspeed, lanes, samePriority, differentPriority):
        self.priority = priority
        self.maxspeed = maxspeed
        self.lanes = lanes
        self.samePriority = samePriority
        self.differentPriority = differentPriority
      
# Roads which can be used by a car
roads = {}
roads['motorway'] = Road(1, 130, 6, 'traffic_lights', 'traffic_lights')
roads['motorway_link'] = Road(2, 70, 4, 'traffic_lights', 'traffic_lights')
roads['trunk'] = Road(3, 90, 4, 'traffic_lights', 'traffic_lights')
roads['trunk_link'] = Road(4, 70, 4, 'traffic_lights', 'traffic_lights')
roads['primary'] = Road(5, 50, 4, 'traffic_lights', 'stop_sign')
roads['primary_link'] = Road(6 ,50, 4, 'traffic_lights', 'stop_sign')
roads['secondary'] = Road(7, 50, 4, 'traffic_lights', 'stop_sign')
roads['secondary_link'] = Road(8, 50, 4, 'traffic_lights', 'stop_sign')
roads['tertiary'] = Road(9, 50, 2, 'traffic_lights', 'stop_sign')
roads['tertiary_link'] = Road(10, 50, 2, 'traffic_lights', 'stop_sign')
roads['unclassified'] = Road(11, 50, 2, 'stop_sign', 'stop_sign')
roads['residential'] = Road(12, 50, 2, 'stop_sign', 'stop_sign')
roads['living_street'] = Road(13, 25, 2, 'stop_sign', 'stop_sign')
roads['unsurfaced'] = Road(14, 20, 2, 'stop_sign', 'stop_sign')
