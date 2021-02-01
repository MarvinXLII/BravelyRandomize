class ITEMS:
    def __init__(self, dataFile):
        self.dataFile = dataFile.crowdFiles['ItemTable.btb']
        self.ids = self.dataFile.readCol(0)              ## NB: IDs are unique
        self.names = self.dataFile.readTextStringAll(4)  ##     names are not! (e.g. Antidote item and spell!)
        self.idToName = {i:n for i,n in zip(self.ids, self.names)}
        self.idToRow = {i:r for r,i in enumerate(self.ids)}
        self.cols = {
            'order': 3,
            'icon': 11,
            'cost': 19,
            'sell': 20,
        }

    def getName(self, id):
        return self.idToName[id]

    def getRow(self, id):
        return self.idToRow[id]

    def getOrder(self, id):
        row = self.idToRow[id]
        col = self.cols['order']
        return self.dataFile.readValue(row, col)

    def getIcon(self, id):
        row = self.idToRow[id]
        col = self.cols['icon']
        return self.dataFile.readValue(row, col)

    def getCost(self, id):
        row = self.idToRow[id]
        col = self.cols['cost']
        return self.dataFile.readValue(row, col)
    
    def changeCostByName(self, name, value):
        assert self.names.count(name) != 0, f"{name} does not exist in the item table."
        assert self.names.count(name) == 1, f"{name} is not unique in the item table."
        id = self.ids[self.names.index(name)]
        self.changeCost(id, value)

    def changeCost(self, id, value):
        row = self.idToRow[id]
        col1 = self.cols['cost']
        col2 = self.cols['sell']
        self.dataFile.patchValue(value, row, col1)
        self.dataFile.patchValue(int(value/2), row, col2)

    def changeOrder(self, id, value):
        row = self.idToRow[id]
        col = self.cols['order']
        self.dataFile.patchValue(value, row, col)
        
    def changeIcon(self, id, value):
        row = self.idToRow[id]
        col = self.cols['icon']
        self.dataFile.patchValue(value, row, col)


class ITEMS_BD(ITEMS):
    def __init__(self, dataFile):
        super().__init__(dataFile)
        self.cols = {
            'order': 3,
            'icon': 11,
            'cost': 17,
            'sell': 18,
        }
