'''
Created on 03.11.2017

@author: zhechkoz

'''
import sys
import datetime

class CEGraph(object):
    def __init__(self, project, author):
        self.author = author
        self.date = datetime.date.today()
        self.project = project
        self.nodes = {}
        self.segments = {}
        self.OSMOID = {}
        self.buildings = {}
        self.parkings = {}
    
    def appendNodes(self, items):
        for item in items:
            self.nodes[item.id] = item
            if item.osmID in self.OSMOID:
                raise ValueError('More than one node have the same OSM ID: ' + item.osmID)
            self.OSMOID.setdefault(item.osmID, []).append(item.id)
        
    def appendSegments(self, items):
        for item in items:
            self.segments[item.id] = item
            self.OSMOID.setdefault(item.osmID, []).append(item.id)
    
    def getNode(self, OID):
        return self.nodes.get(OID, None)

    def getSegment(self, OID):
        return self.segments.get(OID, None)

    def getNodeByOSMID(self, osmID):
        return self.getNode(self.OSMOID.get(osmID, [''])[0])

    def getSegmentsByOSMID(self, osmID):
        ids = self.OSMOID.get(osmID, [])
        segments = [self.getSegment(oid) for oid in ids]
        return segments

    def collectLanesFromSUMOItems(self, SUMOedges, SUMOnodes):
        validLanes = {}
        for (id, nodes) in SUMOnodes.iteritems():
            osmID = int(id)
            ceNode = self.getNodeByOSMID(osmID)

            if not ceNode:
                # Node was deleted during CE cleanup process so
                # try to find the nearest node which exists and append the
                # lanes information. 
                # IMPORTANT: User may have to correct the CE model to correspond
                # to SUMO shapes manually.
                missingNode = nodes[0]
                minDistance = sys.maxint
                for node in self.nodes.values():
                    abs = missingNode.vertices[0].distanceTo(node.vertices[0]) 
                    if abs < minDistance:
                        minDistance = abs
                        ceNode = node

            for node in nodes:
                validLanes.update(node.lanes)
                ceNode.appendLanes(node.lanes.keys())
                ceNode.hierarchy = node.hierarchy

        for (id, edges) in SUMOedges.iteritems():
            if len(id) > 1 and id[0:2] == '--':
                # Edge's OSM ID is negative and direction is negative, so
                # this is a backwards segment
                osmID = int(id[2:])
                forward = False
            elif len(id) > 0 and id[0] == '-':
                # If there is an edge with a positive sign then this is a
                # backwards direction segment, else this is a forward 
                # segment with a negative OSM ID (according to OSM IDs can be negative)
                forward = not SUMOedges.has_key(id[1:])
                osmID = int(id) if forward else int(id[1:])
            elif len(id) > 0:
                # Normal forward edge
                osmID = int(id)
                forward = True
            else:
                print("Not valid OSM ID format found " + str(id))
                continue

            segments = self.getSegmentsByOSMID(osmID)

            if len(segments) == 0:
                print('WARNING: Segment with OSM ID ' + str(id) + ' found in SUMO is missing!')
                continue

            for segment in segments:
                    for edge in edges:
                        validLanes.update(edge.lanes)
                        segment.appendLanes(edge.lanes.keys(), forward=forward)
        return validLanes

    def translateCoordinates(self, dx, dy, dz):
        for subList in [self.nodes.values(), self.segments.values(), self.buildings.values(), self.parkings.values()]:
            for item in subList:
                item.transform(dx, dy, dz)

    def reprJSON(self):
        dict = {'author' : self.author,
                'date' : str(self.date),
                'project' : self.project
        }
        dict.update({'nodes' : self.nodes.values()} if self.nodes else {})
        dict.update({'segments' : self.segments.values()} if self.segments else {})
        
        sceneObjects = {}
        sceneObjects.update({'buildings' : self.buildings.values()} if self.buildings else {})
        sceneObjects.update({'parkings' : self.parkings.values()} if self.parkings else {})
        dict.update({'sceneObjects' : sceneObjects} if sceneObjects else {})
        
        return dict
