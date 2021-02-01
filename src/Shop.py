class SHOP:
    def __init__(self, dataFiles):
        self.dataFiles = dataFiles
        allMagic  = list(range(50000, 50012)) # White Mage (omit Lvl. 7 Raise All)
        allMagic += list(range(50100, 50112)) # Black Mage (omit Lvl. 7 Flare)
        allMagic += list(range(50200, 50212)) # Time Mage (omit Lvl. 7 Quickga)
        allMagic += list(range(50400, 50412)) # Bishop (omit Lvl. 7 Fate)
        allMagic += list(range(50500, 50508)) # Wizard
        allMagic += list(range(50600, 50612)) # Astrologian (omit Lvl. 7 Status Barrier)

        for fileName, dataFile in self.dataFiles.crowdFiles.items():
            if fileName == 'ShopMasterTable_Magic.spb':
                continue
            if fileName == 'ND_31_Magic.spb':
                pass # DON'T CHANGE THE SHOP WITH LEVEL 7 SPELLS
            elif 'Magic.spb' in fileName:
                counts = [0]*len(allMagic)
                dataFile.updateData(allMagic, counts)


class SHOP_BD:
    def __init__(self, dataFiles, parameterFiles):
        self.dataFiles = dataFiles.crowdFiles
        itemFile = parameterFiles.crowdFiles['ItemTable.btb']
        ids = itemFile.readCol(0)
        allMagic = filter(lambda x: x >= 50000, ids)
        allMagic = list(filter(lambda x: x < 50218, allMagic) )

        for fileName, dataFile in self.dataFiles.items():
            if fileName == 'ShopMasterTable_Magic.spb':
                continue
            elif 'Magic.spb' in fileName:
                counts = [0]*len(allMagic)
                dataFile.updateData(allMagic, counts)
                
