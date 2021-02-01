from copy import copy
import random

class TREASURES:
    def __init__(self, treasureFiles, items):
        self.items = items
        self.treasureFiles = copy(treasureFiles.crowdFiles)
        del self.treasureFiles['TreasureMessageTable.btb']

    def shuffleTreasures(self):
        candidates = []
        isSlot = {}
        for fileName, table in self.treasureFiles.items():
            itemID = table.readCol(1)
            money = table.readCol(2)
            num = table.readCol(3)
            candidates += list(filter(lambda x: any(x), zip(itemID, money, num)))
            isSlot[fileName] = {row:(any(x) and x[0] < 90000) for row, x in enumerate(zip(itemID, money, num))}
        # Filter empty slots
        candidates = list(filter(lambda x: any(x), candidates))

        # Add 1 candidate for all items not normally found in chests
        isDummy = {i:'Dummy' in self.items.getName(i) for i in self.items.ids}
        allIncluded = [c[0] for c in candidates]
        allExcluded = list(filter(lambda x: not isDummy[x], self.items.ids))
        allExcluded = sorted(set(allExcluded).difference(allIncluded))
        candidates += [(i,0,1) for i in allExcluded]

        # Filter key items
        candidates = list(filter(lambda x: x[0] < 90000, candidates))

        # Randomize
        random.shuffle(candidates)
        for fileName, table in self.treasureFiles.items():
            for row in range(table.count):
                if isSlot[fileName][row]:
                    itemID, money, num = candidates.pop()
                    table.patchValue(itemID, row, 1)
                    table.patchValue(money, row, 2)
                    table.patchValue(num, row, 3)

        # Copy chests from airship (ch 6+) to ship (ch <6); exclude chest key
        tw_20 = self.treasureFiles['TW_20.trb'] # Airship ch 6+
        tw_14 = self.treasureFiles['TW_14.trb'] # Ship ch <6
        for row in range(7):
            itemID = tw_20.readValue(row, 1)
            money = tw_20.readValue(row, 2)
            num = tw_20.readValue(row, 3)
            tw_14.patchValue(itemID, row, 1)
            tw_14.patchValue(money, row, 2)
            tw_14.patchValue(num, row, 3)

    def print(self):
        self.fileToLoc = {
            'EV_10.trb': '????????? ("SmallAirShip")',
            'EV_15.trb': 'SS Funky Francisca',
            'ND_10.trb': 'Norende Ravine',
            'ND_11.trb': 'Ruins of Centro Keep',
            'ND_12.trb': 'Lontano Villa',
            'ND_13.trb': 'Temple of Wind',
            'ND_14.trb': 'Vestment Cave',
            'ND_15.trb': 'Harena Ruins',
            'ND_16.trb': 'Grand Mill Works',
            'ND_17.trb': 'Miasma Woods',
            'ND_18.trb': 'Mount Framentum',
            'ND_19.trb': 'Temple of Water',
            'ND_20.trb': 'Witherwood',
            'ND_21.trb': 'Florem Gardens',
            'ND_22.trb': 'Twilight Ruins',
            'ND_23.trb': 'Mythril Mines',
            'ND_24.trb': 'Underflow',
            'ND_25.trb': 'Temple of Fire',
            'ND_26.trb': 'Starkfort Interior',
            'ND_27.trb': 'Grapp Keep',
            'ND_28.trb': 'Engine Room',
            'ND_29.trb': 'Central Command',
            'ND_30.trb': 'Everlast Tower & Temple of Earth',
            'ND_31.trb': 'Vampire Castle',
            'ND_32.trb': 'Dark Aurora',
            'ND_33.trb': "Dimension's Hasp",
            'TW_10.trb': 'Kindom of Caldisla',
            'TW_11.trb': 'Ancheim',
            'TW_12.trb': 'Yulyana Woods Needlworks',
            'TW_13.trb': 'Florem',
            'TW_14.trb': 'Grandship',
            'TW_16.trb': 'Hartschild',
            'TW_17.trb': 'Starkfort',
            'TW_18.trb': 'Eternia',
            'TW_19.trb': 'Gravemark Village',
            'TW_20.trb': 'Grandship (Airship, Ch. 6+)'
        }
        
        print('=========')
        print('TREASURES')
        print('=========')
        print('')
        print('')
        for fileName, location in self.fileToLoc.items():
            table = self.treasureFiles[fileName]
            itemID = table.readCol(1)
            money = table.readCol(2)
            num = table.readCol(3)
            
            print(location)
            print('-'*len(location))
            print('')
            for i, m, n in zip(itemID, money, num):
                if not any([i, m, n]):
                    continue
                if m:
                    print('  ', f"{m} pg")
                elif n > 2:
                    print('  ', self.items.getName(i), f"x{n}")
                else:
                    print('  ', self.items.getName(i))
            print('')
            print('')
        print('')
        print('')
        print('')
            
