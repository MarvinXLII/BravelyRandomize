# BD: only PCs: 1-4
# BS: main PCs: 1-4; Janne and Nikolai: 5-6; unknown: 7-9
class PC:
    def __init__(self, dataFiles):
        self.dataFiles = []
        for i in range(1, 7):
            fileName = f'PcLevelTable00{i}.btb'
            if not fileName in dataFiles.crowdFiles:
                break
            self.dataFiles.append(dataFiles.crowdFiles[fileName])

    def zeroEXP(self):
        for dataFile in self.dataFiles:
            dataFile.patchCol([0]*99, 1) # TOTAL
            dataFile.patchCol([0]*99, 2) # NEXT LEVEL
