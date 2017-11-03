'''
Created on 11.03.2017

@author: zhechkoz

'''
class SUMOGraph(object):
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.connections = []
        self.lanes = {}
    
    def translateCoordinates(self, dx, dy, dz):
        for subList in [self.nodes.values(), self.edges.values()]:
            for items in subList:
                for item in items:
                    item.transform(dx, dy, dz)

        for item in self.lanes.values():
            item.transform(dx, dy, dz)
    
    def reprJSON(self):
        dict = { 'connections' : self.connections,
                 'lanes' : self.lanes.values()
        }
        return dict

class SUMOGraphConnection(object):
    def __init__(self, id, fromLane, toLane, via):
        self.id = id
        self.fromLane = fromLane
        self.toLane = toLane
        self.via = via.split(' ') if via else []

    def reprJSON(self):
        dict = { 'id' : self.id,
                 'fromLane' : self.fromLane,
                 'toLane' : self.toLane
        }

        dict.update({'via' : self.via} if self.via else {})
        return dict
        