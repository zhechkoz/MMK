'''
Created on 25.02.2017

@author: murauermax and zhechkoz

'''
from scripting import *
import os, sys, errno
import simplejson as json
import xml.etree.ElementTree as ET
import re

ce = CE() # Get a CityEngine instance

sys.path.append(ce.toFSPath('scripts'))
from mmkcegraph import *
from mmksumograph import *
from mmkgraphitem import *


# Define cleanup settings which preserve osm meta data
cleanupSettings = CleanupGraphSettings()
cleanupSettings.setIntersectSegments(False)
cleanupSettings.setMergeNodes(False)
cleanupSettings.setSnapNodesToSegments(False)
cleanupSettings.setResolveConflictShapes(True)

class MMKExporter(object):
    def __init__(self, author, osmFile, sumoFile, ox, oz, sumoox=None, sumooz=None):
        self.osmFile = osmFile
        self.sumoFile = sumoFile
        self.ox = ox
        self.oz = oz
        self.sumoox = sumoox
        self.sumooz = sumooz
        self.ceGraph = CEGraph(ce.project(), author)
        self.sumoGraph = SUMOGraph()

    def parseGraphs(self): 
        # Parse nodes and segments
        nodes = self.parseCEGraphNodes()
        segments = self.parseCEGraphSegments()
        self.ceGraph.appendNodes(nodes)
        self.ceGraph.appendSegments(segments)
        
        # Parse buildings and parkings
        buildings = self.parseCEObjectsOfKind(lambda s: ce.getAttribute(s, 'building') == 'yes')
        parkings = self.parseCEObjectsOfKind(lambda s: ce.getAttribute(s, 'amenity') == 'parking')
        self.ceGraph.buildings = buildings
        self.ceGraph.parkings = parkings 
        
        # Fix CE coordinates to line up with Unity
        self.ceGraph.translateCoordinates(self.ox, 0, self.oz)
        
        # Try to parse SUMO Lanes and Connections
        sumo = ce.toFSPath(self.sumoFile)
        if not os.path.isfile(sumo):
            print('WARNING: SUMO file not found! Lane information and connections will not be generated!')
        else:
            sumoNet = ET.parse(sumo)
            sumoRoot = sumoNet.getroot()

            edges, nodes = self.parseSUMOItems(sumoRoot)
            self.sumoGraph.nodes = nodes
            self.sumoGraph.edges = edges
            connections = self.parseSUMOConnections(sumoRoot)
            self.sumoGraph.connections = connections
            
            # Fix SUMO coordinates to line up with Unity.
            # Because of the used heuristic in collectLanesFromSUMOItems to
            # match lanes of deleted vertices to their neares neighbour, we
            # have to fix the coordinates of all SUMO items (especially lanes)
            # before collecting the lanes.
            self.determineSUMOOffset(sumoRoot)
            self.sumoGraph.translateCoordinates(self.sumoox, 0, self.sumooz)

            # Order lanes to corresponding segments and nodes
            self.sumoGraph.lanes = self.ceGraph.collectLanesFromSUMOItems(edges, nodes)

    def parseCEGraphSegments(self):
        parsedSegments = []
        segments = ce.getObjectsFrom(ce.scene, ce.isGraphSegment)    
        for o in segments:
            neighbours = ce.getObjectsFrom(o, ce.isGraphNode)
            neighboursList = [ce.getOID(neighbour) for neighbour in neighbours]
            osmID = ce.getAttribute(o, 'osm_id')

            segment = CEGraphSegment(ce.getOID(o), ce.getVertices(o), osmID, neighboursList)
            segment.initializeAttributes(ce, o)
            parsedSegments.append(segment)

            shapes = ce.getObjectsFrom(o, ce.isShape)
            for s in shapes:
                segment.appendShapes(ce.getOID(s), ce.getVertices(s), osmID)
        return parsedSegments
                
    def parseCEGraphNodes(self):
        parsedNodes = []
        nodes = ce.getObjectsFrom(ce.scene, ce.isGraphNode)    
        for o in nodes:
            neighbours = ce.getObjectsFrom(o, ce.isGraphSegment)
            neighboursList = [ce.getOID(neighbour) for neighbour in neighbours]
            osmID = ce.getAttribute(o, 'osm_id')

            node = CEGraphNode(ce.getOID(o), ce.getVertices(o), osmID, neighboursList)
            node.initializeAttributes(ce, o)
            parsedNodes.append(node)

            shapes = ce.getObjectsFrom(o, ce.isShape)
            for s in shapes:
                node.appendShapes(ce.getOID(s), ce.getVertices(s), osmID)
        return parsedNodes
    
    def parseCEObjectsOfKind(self, isObject):
        parsedItems = {}
        shapeLayers = ce.getObjectsFrom(ce.scene, ce.isShapeLayer)
        for l in shapeLayers:
            for s in ce.getObjectsFrom(l, ce.isShape):
                if isObject(s):
                    item = CEGraphItem(ce.getOID(s), ce.getVertices(s), ce.getAttribute(s, 'osm_id')) 
                    parsedItems[item.id] = item 
        return parsedItems

    def parseSUMOConnections(self, root):
        connections = []
        id = 0

        for connection in root.findall('connection'):
            connectionAttrib = connection.attrib
            fromLane = connectionAttrib['from'] + '_' + connectionAttrib['fromLane']
            toLane = connectionAttrib['to'] + '_' + connectionAttrib['toLane']
            via = connectionAttrib.get('via', None)
            trafficLight = connectionAttrib.get('tl', None)
            trafficLightIndex = connectionAttrib.get('linkIndex', None)
            direction = connectionAttrib.get('dir', None)

            connectionObject = SUMOGraphConnection(id, fromLane, toLane, via, trafficLight, trafficLightIndex, direction)
            connections.append(connectionObject)
            id += 1
        return connections

    def parseSUMOItems(self, root):
        sumoEdges, sumoNodes = ({}, {})
        junctions = {j.attrib['id'] : j.attrib for j in root.findall('junction')}

        for edge in root.findall('edge'):
            edgeAttrib = edge.attrib

            idOrder = re.split('_|#', edgeAttrib['id']) # If no order in id set it to 0
            (id, order) = (idOrder[0], int(idOrder[1]) if len(idOrder) > 1 else 0)
            isNode = (len(id) > 0 and id[0] == ':') # Nodes are always internal and start with a ':'
            id = id[1:] if isNode else id

            if isNode:
                junctionAttrib = junctions.get(id, None)
                if junctionAttrib:
                    vertices = junctionAttrib['x'] + ',' + junctionAttrib['y']
                    hierachy = junctionAttrib['type']

                sumoItem = SUMOGraphNode(id, vertices or '', hierachy or 'unknown')
                sumoNodes.setdefault(sumoItem.id, []).append(sumoItem)
            else:
                if 'shape' in edgeAttrib:
                     vertices = edgeAttrib['shape']

                (start, end) = (edgeAttrib.get('from', ''), edgeAttrib.get('to', ''))
                sumoItem = SUMOGraphEdge(id, vertices or '', order, start, end)
                sumoEdges.setdefault(sumoItem.id, []).append(sumoItem)

            for lane in edge.findall('lane'):
                laneAttrib = lane.attrib
                id = laneAttrib['id']
                length = laneAttrib.get('length', 0)
                index = laneAttrib.get('index', 0)

                if 'shape' in laneAttrib:
                    vertices = laneAttrib['shape']

                sumoItem.appendLane(id, vertices or '', index, length)

        return sumoEdges, sumoNodes
        
    def determineSUMOOffset(self, root):
        if self.sumoox and self.sumooz:
            return # Offset was set by user

        location = root.find('location')
        if location == None:
            raise ValueError('Coordinates offset to Unity of SUMO objects could not be found!\n' +
                             'Please, define it manually!')
        
        (sumoXOffset, sumoYOffset) = location.attrib['netOffset'].split(',')
        self.sumoox = float(sumoXOffset) - self.ox
        self.sumooz = float(sumoYOffset) - (-self.oz) # z coordinate is always negative to x
    
    def reprJSON(self):
        # IMPORTANT: SUMO's both coordinates has to be firstly rotatet 
        # by 180 degrees and than translated. The same is valid also 
        # for the x and y coordinates of all CE objects.
        offsets = {'offsets' : {'sumo' : {'x' : self.sumoox, 
                                          'z' : self.sumooz
                               },
                                'ce' : {'x' : self.ox, 
                                        'z' : self.oz
                               }
                  }
        }

        dict = self.ceGraph.reprJSON()
        dict.update(self.sumoGraph.reprJSON())
        dict.update(offsets)
        return dict

    @noUIupdate
    def prepareScene(self):
        self.cleanupGraph()
        self.fixIntersectionShapes()
        self.cleanupGraph()
    
    def cleanupGraph(self):
        graphlayer = ce.getObjectsFrom(ce.scene, ce.isGraphLayer)
        ce.cleanupGraph(graphlayer, cleanupSettings)

    def fixIntersectionShapes(self):
        objects = ce.getObjectsFrom(ce.scene, ce.isGraphSegment)
        intersections = []
        # http://cehelp.esri.com/help/index.jsp?topic=/com.procedural.cityengine.help/html/manual/is/create/streetshapes.html
        shapeWhiteList = ['CROSSING', 'JUNCTION', 'FREEWAY', 'FREEWAY_ENTRY']

        for o in objects:
            attrStart = ce.getAttribute(o, 'connectionStart') or ''
            attrEnd = ce.getAttribute(o, 'connectionEnd') or ''
            hasStart = any(shape in attrStart for shape in shapeWhiteList)
            hasEnd = any(shape in attrEnd for shape in shapeWhiteList)

            if hasStart != hasEnd:
                intersections.append((o, hasStart))

        for (intersection, hasStart) in intersections:
            lanes = int(ce.getAttribute(intersection, 'lanes'))
            if lanes == 1:
                continue

            oneway = ce.getAttribute(intersection, 'oneway') == 'yes'
            lanesForward = ce.getAttribute(intersection, 'lanes:forward')
            lanesBackward = int(ce.getAttribute(intersection, 'lanes:backward') or 0)
            
            # Center junction according to number of lanes
            if not lanesForward:
                if oneway:
                    lanesForward = lanesBackward = lanes
                else:
                    lanesForward = int(lanes / 2)
                    lanesBackward = lanes - lanesForward
            else:
                lanesForward = int(lanesForward)

            offset = 2 * (lanesForward - lanesBackward)
            adjacentNodes = ce.getObjectsFrom(intersection, ce.isGraphNode)
            mergeNode = adjacentNodes[0] # Find the node of the segment which is not in the junction 
            if hasStart: # According to the orientation of the segment determine the offset's sign
                lanesForward, lanesBackward = lanesBackward, lanesForward
                mergeNode = adjacentNodes[1]

            offset = -offset if lanesForward > lanesBackward else offset
            self.setOffset(intersection, offset)
            
            # For every next segment belonging to the junction apply the same offset
            self.propagateOffset(intersection, mergeNode, offset)
                
    def propagateOffset(self, currentSegment, mergeNode, offset):
        while True:
            adjacentSegments = ce.getObjectsFrom(mergeNode, ce.isGraphSegment)
            if len(adjacentSegments) != 2: # Streets always end with a roundabout (one adjacent segment)
                return

            nextSegment = adjacentSegments[0]
            if ce.getOID(nextSegment) == ce.getOID(currentSegment):
                nextSegment = adjacentSegments[1]

            if not self.equalSegments(currentSegment, nextSegment):
                return

            currentSegment = nextSegment
            self.setOffset(currentSegment, offset)
            
            adjacentNodes = ce.getObjectsFrom(currentSegment, ce.isGraphNode)
            nextNode = adjacentNodes[0]
            if ce.getOID(nextNode) == ce.getOID(mergeNode):
                nextNode = adjacentNodes[1]

            mergeNode = nextNode

    def equalSegments(self, first, second):
        firstLanes = ce.getAttribute(first, 'lanes')
        secondLanes = ce.getAttribute(second, 'lanes')
        firstForwardLanes = ce.getAttribute(first, 'lanes:forward')
        secondForwardLanes = ce.getAttribute(second, 'lanes:forward')
        firstBackwardLanes = ce.getAttribute(first, 'lanes:backward')
        secondBackwardLanes = ce.getAttribute(second, 'lanes:backward')
        firstHighway = ce.getAttribute(first, 'highway')
        secondHighway = ce.getAttribute(second, 'highway')

        return (firstLanes == secondLanes and firstForwardLanes == secondForwardLanes and
                firstBackwardLanes == secondBackwardLanes and firstHighway == secondHighway)
    
    def setOffset(self, item, offset):
        oldOffset = int(ce.getAttribute(item, 'streetOffset') or 0)
        newOffset = oldOffset + offset
        ce.setAttributeSource(item, '/ce/street/streetOffset', 'OBJECT')
        ce.setAttribute(item, 'streetOffset', newOffset)

    def exportJson(self, exportName):
        class ComplexEncoder(json.JSONEncoder):
            def default(self, obj):
                if hasattr(obj,'reprJSON'):
                    return obj.reprJSON()
                else:
                    return json.JSONEncoder.default(self, obj)

        def mkdir_p(path):
            try:
                os.makedirs(path)
            except OSError, exc:
                if exc.errno == errno.EEXIST and os.path.isdir(path):
                    pass
                elif exc.errno == 20047:
                    # Error associated with Microsoft system
                    pass

        dir = ce.toFSPath('/' + ce.project())
        mkdir_p(os.path.join(dir, 'export'))
        dir = ce.toFSPath('export')
        fileName = os.path.join(dir, exportName)

        with open(fileName, 'w+') as file:  
            file.write(json.dumps(self, indent=4, sort_keys=True, cls=ComplexEncoder))
        print('File exported! Location: ' + fileName + '\n')
      
if __name__ == '__main__':

    # Define SUMO and OSM data location
    osm = 'data/tum-sanitized.osm'
    sumo = 'data/tum-sanitized.net.xml'

    # Define export center coordinates; These has to be the same
    # as in the "Export Models..." dialoge in CityEngine.
    ox = -690985
    oz = 5336220
    
    # If the program cannot find the SUMO objetcts' offsets, then the
    # following two values has to be defined by the user and
    # passed to the exporter object.
    sumoox = 0
    sumooz = 0

    print('MMK Streetnetwork Export')
    exporter = MMKExporter('TUM - MMK', osm, sumo, ox, oz)
    
    # The following statement has to be executed if this is
    # the FIRST TIME the exporter is executed on a scene.
    # The scene will be cleaned up again and the junctions's 
    # offset will be adjusted to correspondent to the SUMO.
    exporter.prepareScene()

    print('Building streetnetwork...')

    exporter.parseGraphs()
    exporter.exportJson('MMK_GraphExport.json')

    print('Finished. Success!\n')
