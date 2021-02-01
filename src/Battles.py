
class BATTLES:
    def __init__(self, dataFiles):
        self.dataFile = dataFiles.crowdFiles['MonsterData.btb']

    def scaleArray(self, col, scale, maxValue):
        array = self.dataFile.readCol(col)
        array = [min(a*scale, maxValue) for a in array]
        self.dataFile.patchCol(array, col)
        
    def scaleEXP(self, scale):
        self.scaleArray(111, scale, 999999)
        self.scaleArray(112, scale, 999999)

    def scaleJP(self, scale):
        self.scaleArray(113, scale, 999)
        self.scaleArray(114, scale, 999)

    def scalePG(self, scale):
        self.scaleArray(115, scale, 999999)
        self.scaleArray(116, scale, 999999)


class BATTLES_BD(BATTLES):
    def __init__(self, dataFiles):
        super().__init__(dataFiles)
        
    def scaleEXP(self, scale):
        self.scaleArray(91, scale, 999999)

    def scaleJP(self, scale):
        self.scaleArray(92, scale, 999)

    def scalePG(self, scale):
        self.scaleArray(93, scale, 999999)
