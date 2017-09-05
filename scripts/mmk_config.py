# Define bounding box
bbminx = 690370.0
bbmaxx = 691600.0
bbminz = 5335624.0
bbmaxz = 5336828.0

# Define center coordinates
ox = 690985
oz = 5336220

class Road(object):
    def __init__(self, maxspeed):
        self.maxspeed = maxspeed
      
# Roads which can be used by a car
roads = {}
roads['motorway'] = Road(130)
roads['motorway_link'] = Road(70)
roads['trunk'] = Road(90)
roads['trunk_link'] = Road(70)
roads['primary'] = Road(50)
roads['primary_link'] = Road(50)
roads['secondary'] = Road(50)
roads['secondary_link'] = Road(50)
roads['tertiary'] = Road(50)
roads['tertiary_link'] = Road(50)
roads['unclassified'] = Road(50)
roads['residential'] = Road(30)
roads['living_street'] = Road(25)
roads['unsurfaced'] = Road(20)
