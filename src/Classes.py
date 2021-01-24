import random
import os
import shutil
import sys
from copy import deepcopy

class FILE:
    def __init__(self, filename):
        self.path = os.path.dirname(filename)
        self.filename = os.path.basename(filename)
        with open(filename, 'rb') as file:
            self.data = bytearray(file.read())
        self.address = 0

    def read(self, size=4):
        value = int.from_bytes(self.data[self.address:self.address+size], byteorder='little')
        self.address += size
        return value

    def readValue(self, address, size=4):
        return int.from_bytes(self.data[address:address+size], byteorder='little')
    
    def readArray(self, address, num, stride, size=4):
        data = []
        for i in range(num):
            data.append(self.readValue(address + i*stride, size=size))
        return data
    
    # Size is typically 1 or 2
    def readString(self, address=None, size=1):
        if address: ## THIS IS TEMPORARY, REMOVE IN THE FUTURE
            self.address = address
        string = ''
        n = self.read(size=size)
        while n > 0:
            string += chr(n)
            n = self.read(size=size)
        while self.readValue(self.address, size=size) == 0:
            self.address += 1
            if self.address >= len(self.data):
                break
        return string

    def patch(self, value, address, size=4):
        self.data[address:address+size] = value.to_bytes(size, byteorder='little')

    def patchArray(self, data, address, stride, size=4):
        for i, d in enumerate(data):
            self.patch(d, address + i*stride)                    

    # Size mandatory here; use size of entry, not size of string
    def patchString(self, string, address, size=1):
        self.address = address
        origStringLength = len(self.readString(size=size))
        assert len(string) <= origStringLength, f'String {string} will not fit in entry'
        self.data[address:address+origStringLength] = bytearray([0]*origStringLength)
        stringArray = map(ord, string)
        self.patchArray(stringArray, address, size, size=size)



class ROM:
    def __init__(self, settings):
        self.settings = settings

        pwd = os.getcwd()
        os.chdir(settings['rom'])
        self.battle = BATTLE('Common_en/Battle')
        self.parameter = PARAMETER('Common_en/Paramater')
        self.treasures = TREASURES('Common_en/TreasureTable', self.parameter)
        os.chdir(pwd)

    def patch(self):
        self.battle.patch()
        self.parameter.patch()
        self.treasures.patch()
        
    def randomize(self):
        random.seed(self.settings['seed'])
        if self.settings['jobs-abilities']:
            self.parameter.shuffleAbilities()
        if self.settings['jobs-spells']:
            self.parameter.shuffleSpells()
        if self.settings['jobs-specialties']:
            self.parameter.randomSpecialty() # MUST BE AFTER COMMAND/SUPPORT SHUFFLE
        if self.settings['jobs-sa-costs']:
            self.parameter.shuffleSupportCost()
        if self.settings['jobs-stats']:
            self.parameter.shuffleStats()
        if self.settings['treasures']:
            self.treasures.shuffleTreasures()


    # Simpler to rescale enemy data rather than adjust shop costs for pg
    def qualityOfLife(self):
        self.battle.scaleEXP(self.settings['qol-exp'])
        self.battle.scaleJP(self.settings['qol-jp'])
        self.battle.scalePG(self.settings['qol-pg'])
        if self.settings['qol-teleport-stones']:
            self.parameter.changeItemCost('Teleport Stone', 0)

        ## TESTING OPTIONS
        if 'no-jp' in self.settings:
            if self.settings['no-jp']:
                self.parameter.zeroJP()
        if 'no-exp' in self.settings:
            if self.settings['no-exp']:
                self.parameter.zeroEXP()
                

    def printLogs(self, path):
        temp = sys.stdout
        sys.stdout = open(os.path.join(path, 'spoiler.log'), 'w')
        self.parameter.printStats()
        self.parameter.printAbilities()
        self.treasures.print()
        sys.stdout = temp
        
    # Only write crowd files
    def write(self, path):
        def writeFile(fileData):
            fullPath = os.path.join(path, 'romfs', fileData.path)
            os.makedirs(fullPath, exist_ok=True)
            filename = os.path.join(fullPath, fileData.filename)
            with open(filename, 'wb') as file:
                file.write(fileData.data)
        
        writeFile(self.parameter.crowdFile)
        writeFile(self.treasures.crowdFile)
        writeFile(self.battle.crowdFile)


class DATA:
    def __init__(self, path):
        self.indexFile = FILE(os.path.join(path, 'index.fs'))
        self.crowdFile = FILE(os.path.join(path, 'crowd.fs'))
        
        self.index = {}
        self.crowd = {}

        # Read index.fs
        self.indexFile.address = 0
        offset = self.indexFile.read()
        while True:
            base = self.indexFile.read()
            size = self.indexFile.read()
            strCRC32 = self.indexFile.read()
            fileName = self.indexFile.readString()
            self.index[fileName] = base
            if offset == 0:
                break
            self.indexFile.address = offset
            offset = self.indexFile.read()

        # Read crowd.fs file header
        for fileName, base in self.index.items():
            self.crowdFile.address = base + 8
            self.crowd[fileName] = {
                'dataBase' : base + self.crowdFile.read(),
                'dataSize' : self.crowdFile.read(),
                'commandBase' : base + self.crowdFile.read(),
                'commandSize' : self.crowdFile.read(),
                'stringBase' : base + self.crowdFile.read(),
                'stringSize' : self.crowdFile.read(),
                'stride' : self.crowdFile.read(),
                'number' : self.crowdFile.read(),
            }

    def getAddress(self, fileName, row, col):
        base = self.crowd[fileName]['dataBase']
        stride = self.crowd[fileName]['stride']
        offset = col*4 + stride*row
        return base + offset

    def readValue(self, fileName, row, col):
        address = self.getAddress(fileName, row, col)
        return self.crowdFile.readValue(address)

    def patchValue(self, value, fileName, row, col):
        address = self.getAddress(fileName, row, col)
        self.crowdFile.patch(value, address)

    def readData(self, fileName, col, row=None, num=None):
        if not row:
            row = 0
        if not num:
            num = self.crowd[fileName]['number']
        num = min(num, self.crowd[fileName]['number'])
        # Read column of data
        address = self.getAddress(fileName, row, col)
        stride = self.crowd[fileName]['stride']
        return self.crowdFile.readArray(address, num, stride)

    def patchData(self, data, fileName, col, row=None):
        if not row:
            row = 0
        # Patch column of data
        address = self.getAddress(fileName, row, col)
        stride = self.crowd[fileName]['stride']
        self.crowdFile.patchArray(data, address, stride)

    def readCommand(self, fileName, row, col):
        offset = self.getAddress(fileName, row, col)
        base = self.crowd[fileName]['commandBase']
        return self.crowdFile.readString(address=base+offset, size=1)
        
    def patchCommand(self, string, fileName, row, col):
        offset = self.getAddress(fileName, row, col)
        base = self.crowd[fileName]['commandBase']
        self.crowdFile.patchString(string, base+offset, size=1)

    def readString(self, fileName, row, col):
        offset = self.readValue(fileName, row, col)
        base = self.crowd[fileName]['stringBase']
        return self.crowdFile.readString(address=base+offset, size=2)
        
    def patchString(self, string, fileName, row, col):
        offset = self.readValue(fileName, row, col)
        base = self.crowd[fileName]['stringBase']
        self.crowdFile.patchString(string, base+offset, size=2)

    def readStringList(self, fileName, col):
        strings = []
        for i in range(self.crowd[fileName]['number']):
            strings.append(self.readString(fileName, i, col))
        return strings
        

class BATTLE(DATA):
    def __init__(self, path):
        super().__init__(path)
        self.exp = self.readData('MonsterData.btb', 91)
        self.jp = self.readData('MonsterData.btb', 92)
        self.pg = self.readData('MonsterData.btb', 93)

    def patch(self):
        self.patchData(self.exp, 'MonsterData.btb', 91)
        self.patchData(self.jp, 'MonsterData.btb', 92)
        self.patchData(self.pg, 'MonsterData.btb', 93)

    def scaleArray(self, array, scale, maxValue):
        return [ min(a*scale, maxValue) for a in array ]
        
    def scaleEXP(self, scale):
        self.exp = self.scaleArray(self.exp, scale, 999999)

    def scaleJP(self, scale):
        self.jp = self.scaleArray(self.jp, scale, 999)

    def scalePG(self, scale):
        self.pg = self.scaleArray(self.pg, scale, 999999)


class TREASURES(DATA):
    def __init__(self, path, parameter):
        super().__init__(path)

        # Useful lists from parameter
        self.itemId = parameter.itemId
        self.itemNames = parameter.itemNames
        self.itemIdToName = {i:n for i, n in zip(self.itemId, self.itemNames)}

        # Load data
        self.slots = {}
        for fileName in self.crowd.keys():
            if fileName == 'TreasureMessageTable.btb':
                continue
            itemId = self.readData(fileName, 1)
            money = self.readData(fileName, 2)
            num = self.readData(fileName, 3)
            self.slots[fileName] = list(zip(itemId, money, num))

        # Subfile locations:
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
            
    def patch(self):
        for fileName, slotList in self.slots.items():
            itemId, money, num = zip(*slotList)
            self.patchData(itemId, fileName, 1)
            self.patchData(money, fileName, 2)
            self.patchData(num, fileName, 3)

    def shuffleTreasures(self):

        candidates = []
        for slotList in self.slots.values():
            candidates += list(filter(lambda x: any(x), slotList))
            
        # Add 1 candidate for all items not normally found in chests
        isDummy = {i:'Dummy' in self.itemIdToName[i] for i in self.itemId}
        allIncluded = [c[0] for c in candidates]
        allExcluded = list(filter(lambda x: not isDummy[x], self.itemId))     # Filter dummy items
        allExcluded = sorted(list(set(allExcluded).difference(allIncluded))) # Filter included items
        candidates += [(i,0,1) for i in allExcluded]

        # Filter all key items
        candidates = list(filter(lambda x: x[0] < 90000, candidates))

        # Randomize
        random.shuffle(candidates)
        for slotList in self.slots.values():
            for i, slot in enumerate(slotList):
                if slot[0] >= 90000: continue # Skip key item slots
                if any(slot): # Skip empty slots
                    slotList[i] = candidates.pop()

        # Copy chests from airship (ch 6+) to ship EXCLUDING chest key
        self.slots['TW_14.trb'][:7] = self.slots['TW_20.trb'][:7]


    def print(self):
        print('=========')
        print('TREASURES')
        print('=========')
        print('')
        for fileName, slotList in self.slots.items():
            print(self.fileToLoc[fileName])
            print('-'*len(self.fileToLoc[fileName]))
            print('')
            for itemId, money, numItems in slotList:
                if money:
                    print('  ', f"{money} pg")
                elif numItems > 2:
                    print('  ', self.itemIdToName[itemId], f"x{numItems}")
                elif itemId:
                    print('  ', self.itemIdToName[itemId])
            print('')
            print('')
        print('')
        print('')
        print('')
        print('')
        
        

class PARAMETER(DATA):
    def __init__(self, path):
        super().__init__(path)

        # File Lists
        self.pcFiles = [f"PcLevelTable00{i}.btb" for i in range(1, 5)]
        self.jobFiles = []
        for i in range(24):
            j = str(i).rjust(2, '0')
            self.jobFiles.append(f'JobTable{j}.btb')

        # Names that cannot be loaded
        self.jobNames = [
            'Freelancer', 'Knight', 'Black Mage', 'White Mage', 'Monk', 'Ranger',
            'Ninja', 'Time Mage', 'Spell Fencer', 'Swordmaster', 'Pirate', 'Dark Knight',
            'Templar', 'Vampire', 'Arcanist', 'Summoner', 'Conjurer', 'Valkyrie',
            'Spiritmaster', 'Salve-Maker', 'Red Mage', 'Thief', 'Merchant', 'Performer',
        ]

        self.comIds = self.readData('CommandAbility.btb', 0)
        self.comNames = self.readStringList('CommandAbility.btb', 4)
        self.supIds = self.readData('SupportAbility.btb', 0)
        self.supJobIds = self.readData('SupportAbility.btb', 2)
        self.supCosts = self.readData('SupportAbility.btb', 5)
        self.supIcons = self.readData('SupportAbility.btb', 66)
        self.supNames = self.readStringList('SupportAbility.btb', 3)
        self.jobComLabelId = self.readData('JobCommand.btb', 0)
        self.jobComIconId = self.readData('JobCommand.btb', 4)
        self.jobComLabels = self.readStringList('JobCommand.btb', 1)
        self.jobTableComId = self.readData('JobTable.btb', 4)

        self.jobSpec = {}
        self.jobAbil = {}
        self.jobStats = {}
        self.jobSpells = {}
        self.isSpellCaster = {}
        for name, fileName in zip(self.jobNames, self.jobFiles):
            self.jobSpec[name] = self.readValue(fileName, 0, 12)
            self.jobAbil[name] = self.readData(fileName, 13)
            self.jobSpells[name] = self.readData(fileName, 16)
            self.isSpellCaster[name] = not all(self.jobAbil[name])
            self.jobStats[name] = {
                'HP': self.readData(fileName, 4),
                'MP': self.readData(fileName, 5),
                'STR': self.readData(fileName, 6),
                'VIT': self.readData(fileName, 7),
                'INT': self.readData(fileName, 8),
                'MND': self.readData(fileName, 9),
                'AGI': self.readData(fileName, 10),
                'DEX': self.readData(fileName, 11),
            }

        ## LOAD VARIOUS STRINGS
        self.comNames = self.readStringList('CommandAbility.btb', 4) ## START WITH "STRONG STRIKE"
        self.supNames = self.readStringList('SupportAbility.btb', 3) ## START WITH "ABSORP P. DAMAGE"
        
        ## BUILD DICTS FOR SIMPLER CODE AND PRINTOUTS
        self.supIdToCost = {i:c for i,c in zip(self.supIds, self.supCosts)}
        self.supNameToId = {n:i for n,i in zip(self.supNames, self.supIds)}
        self.comNameToId = {n:i for n,i in zip(self.comNames, self.comIds)}
        self.comIdToName = {i:n for n,i in zip(self.comNames, self.comIds)}

        ## ITEMS (FOR COSTS AND PRINTOUTS)
        self.itemCosts = self.readData('ItemTable.btb', 17)
        self.itemSell = self.readData('ItemTable.btb', 18)
        self.itemId = self.readData('ItemTable.btb', 0)
        self.itemNames = self.readStringList('ItemTable.btb', 4)
        self.itemNameToId = {n:i for n, i in zip(self.itemNames, self.itemId)}
        self.itemNameToRow = {n:i for i, n in enumerate(self.itemNames)}

    def patch(self):
        # SUPPORT ABILITIES
        self.patchData(self.supJobIds, 'SupportAbility.btb', 2)
        self.patchData(self.supJobIds, 'SupportAbilityAL.btb', 2)
        self.patchData(self.supCosts, 'SupportAbility.btb', 5)
        self.patchData(self.supCosts, 'SupportAbilityAL.btb', 5)
        self.patchData(self.supIcons, 'SupportAbility.btb', 66)
        self.patchData(self.supIcons, 'SupportAbilityAL.btb', 66)
        # UPDATED FOR MAGIC
        self.patchData(self.jobTableComId, 'JobTable.btb', 4)
        self.patchData(self.jobComIconId, 'JobCommand.btb', 4)
        # JOB STUFF
        for name, fileName in zip(self.jobNames, self.jobFiles):
            # SPECIALTIES 
            self.patchValue(self.jobSpec[name], fileName, 0, 12)
            # Abilities
            self.patchData(self.jobAbil[name], fileName, 13)
            # Spells
            self.patchData(self.jobSpells[name], fileName, 16)
            # STATS
            stats = self.jobStats[name]
            for i, s in enumerate(stats.values()):
                self.patchData(s, fileName, i+4)
        # ITEM STUFF
        self.patchData(self.itemCosts, 'ItemTable.btb', 17)
        self.patchData(self.itemSell, 'ItemTable.btb', 18)
                
    # START AT LEVEL 99 (INCLUDED FOR TESTING)
    def zeroEXP(self):
        for pcFile in self.pcFiles:
            self.patchData([0]*99, pcFile, 1) # TOTAL EXP
            self.patchData([0]*99, pcFile, 2) # EXP FOR NEXT LEVEL

    # START WITH ALL ABILITIES (INCLUDED FOR TESTING)
    def zeroJP(self):
        for fileName in self.jobFiles:
            self.patchData([0]*14, fileName, 1) # TOTAL JP
            self.patchData([0]*14, fileName, 2) # JP FOR NEXT LEVEL

    # ITEM COSTS
    def changeItemCost(self, itemName, cost):
        idx = self.itemNameToRow[itemName]
        self.itemCosts[idx] = cost
        self.itemSell[idx] = int(cost/2)
            
    def shuffleSupportCost(self):
        random.shuffle(self.supCosts)
        self.supIdToCost = {i:c for i,c in zip(self.supIds, self.supCosts)}

    def randomSpecialty(self):
        candidates = list(self.supIds)
        candidates.remove(self.supNameToId['Genome Drain'])
        random.shuffle(candidates)
        for name in self.jobNames:
            if self.comNameToId['Genome Ability'] in self.jobAbil[name]:
                self.jobSpec[name] = self.supNameToId['Genome Drain']
            else:
                self.jobSpec[name] = candidates.pop()

    def shuffleStats(self):
        statNames = self.jobStats[self.jobNames[0]].keys()
        for stat in statNames:
            for i in range(23, 0, -1):
                j = random.randint(0, i)
                nA = self.jobNames[i]
                nB = self.jobNames[j]
                sA = self.jobStats[nA][stat]
                sB = self.jobStats[nB][stat]
                self.jobStats[nA][stat], self.jobStats[nB][stat] = self.jobStats[nB][stat], self.jobStats[nA][stat]
        ## MAKE FREELANCER ALWAYS 100%
        self.jobStats['Freelancer'] = {
            'HP': [100]*14,
            'MP': [100]*14,
            'STR': [100]*14,
            'VIT': [100]*14,
            'INT': [100]*14,
            'MND': [100]*14,
            'AGI': [100]*14,
            'DEX': [100]*14,
        }

    def shuffleAbilities(self):

        # Assign support skills to mages first
        candidates = list(self.supIds)
        random.shuffle(candidates)
        for name in self.jobNames:
            if not self.isSpellCaster[name]: # Skip non-mages
                continue
            abilities = self.jobAbil[name]
            for i, c in enumerate(abilities):
                if c > 0:
                    abilities[i] = candidates.pop()

        # Append all non-magic attacks to candidates
        nonmagic = []
        for name in self.jobNames:
            if self.isSpellCaster[name]: # Skip mages
                continue
            nonmagic += self.jobAbil[name]
        nonmagic = sorted(set(nonmagic).difference(self.supIds)) # filter supIds
        candidates += nonmagic
        random.shuffle(candidates)

        # Assign abilities to remaining jobs
        for name in self.jobNames:
            if self.isSpellCaster[name]: # Skip mages
                continue
            abilities = self.jobAbil[name]
            for i in range(14):
                self.jobAbil[name][i] = candidates.pop()

        # Map abilities to jobIds
        abilIdToJob = {}
        for i, name in enumerate(self.jobNames):
            for abilId in self.jobAbil[name]:
                abilIdToJob[abilId] = i

        # Current map of support job Id to support icons
        supJobIdToIcon = {j:i for j,i in zip(self.supJobIds, self.supIcons)}
        
        # Update jobIds and icons for support abilities
        for i, s in enumerate(self.supIds):
            if s in abilIdToJob:
                jobId = abilIdToJob[s]
                self.supJobIds[i] = jobId
                self.supIcons[i] = supJobIdToIcon[jobId]


    def shuffleSpells(self):

        # LOAD DATA
        nameToFile = {
            'Black Mage': 'AbilityBMG.btb',
            'Spell Fencer': 'AbilityMGS.btb',
            'Time Mage': 'AbilityTMG.btb',
            # 'Red Mage': 'AbilityWBM.btb',
            'White Mage': 'AbilityWMG.btb',
        }
        data = {n:{} for n in nameToFile.keys()}
        for i, (name, fileName) in enumerate(nameToFile.items()):
            spellsList = self.jobSpells[name]
            groupIds = list(filter(lambda x: x > 0, spellsList))
            for i, gId in enumerate(groupIds):
                data[name][i+1] = {'group':gId, 'spells':[]}
            # Load ability table
            level = self.readData(fileName, 0)
            magId = self.readData(fileName, 1)
            itemId = self.readData(fileName, 2)
            x = zip(level, magId, itemId)
            for lvl, mag, item in x:
                data[name][lvl]['spells'].append((mag, item))

        # Store vanilla data
        vanilla = deepcopy(data)
                
        mageNames = list(nameToFile.keys())
        def shuffleGroups(level):
            for i in range(len(mageNames)-1, 0, -1):
                mageA = mageNames[i]
                mageB = random.choice(mageNames[:i])
                data[mageA][level], data[mageB][level] = data[mageB][level], data[mageA][level]

        while True:
            shuffleGroups(1)
            # Ensure white mage has spells that can be bought in Caldisla
            if data['White Mage'][1]['group'] in [2001, 2009, 2037, 2064]:
                break
        shuffleGroups(2)
        shuffleGroups(3)
        shuffleGroups(4)
        shuffleGroups(5)
        shuffleGroups(6)

        # Write data
        for name, fileName in nameToFile.items():
            # Write group IDs
            lvl = 1
            for i in range(14):
                if self.jobSpells[name][i] > 0:
                    self.jobSpells[name][i] = data[name][lvl]['group']
                    lvl += 1

            # Write ability tables
            lst = []
            for lvl in range(1, 7):
                lst += data[name][lvl]['spells']
            spells, items = zip(*lst)
            self.patchData(spells, fileName, 1)
            self.patchData(items, fileName, 2)
        
        # GET MAPPING FROM OLD<->NEW group
        oldToNew = {}; newToOld = {}
        for name in nameToFile.keys():
            for lvl in range(1,7):
                old = vanilla[name][lvl]['group']
                new = data[name][lvl]['group']
                oldToNew[old] = new
                newToOld[new] = old
        
        for i, ti in enumerate(self.jobTableComId):
            if ti in oldToNew:
                self.jobTableComId[i] = oldToNew[ti]
        labelToIcon = {l:i for l,i in zip(self.jobComLabelId, self.jobComIconId)}
        for i, ti in enumerate(self.jobComLabelId):
            if ti in newToOld:
                self.jobComIconId[i] = labelToIcon[newToOld[ti]]

        for i, comId in enumerate(self.jobComLabelId):
            if comId in oldToNew:
                self.patchString('Cast magic.', 'JobCommand.btb', i, 3)

        # UPDATE RED MAGE DESCRIPTIONS

        # get list of white mage + black mages spells / level
        rm = {}
        for lvl in range(1, 5):
            rm[lvl] = []
            rm[lvl] += data['White Mage'][lvl]['spells']
            rm[lvl] += data['Black Mage'][lvl]['spells']

        for i, row in enumerate(range(36, 40)):
            lvl = i+1
            spellNames = [self.comIdToName[x[0]] for x in rm[lvl]]
            spellNames[-1] = 'and '+spellNames[-1]
            string = 'Enables use of\n' + ', '.join(spellNames) + '.'
            self.patchString(string, 'DetailInfoMagicTable.btb', row, 2)
        
        

    def printAbilities(self):
        # Setup
        labelIdToLabel = {i:l for i,l in zip(self.jobComLabelId, self.jobComLabels)}
        supIdToName = {i:n for i,n in zip(self.supIds, self.supNames)}
        supIdToCost = {i:c for i,c in zip(self.supIds, self.supCosts)}
        comIdToName = {i:n for i,n in zip(self.comIds, self.comNames)}
        
        print('=============')
        print('JOB ABILITIES')
        print('=============')
        print('')
        print('')
        jobNames = [ # ORDER TO MATCH MENU
            'Freelancer', 'Monk', 'White Mage', 'Black Mage', 'Knight', 'Thief', 'Merchant', 'Spell Fencer',
            'Time Mage', 'Ranger', 'Summoner', 'Valkyrie', 'Red Mage', 'Salve-Maker', 'Performer', 'Pirate',
            'Ninja', 'Swordmaster', 'Arcanist', 'Spiritmaster','Templar', 'Dark Knight', 'Vampire', 'Conjurer',
        ]
        for name in jobNames:
            print(name)
            print('-'*len(name))
            print('')
            print('  Specialty:', supIdToName[self.jobSpec[name]])
            print('')
            print('  Abilities:')
            for i, (comId, labelId) in enumerate(zip(self.jobAbil[name], self.jobSpells[name])): # REMEMBER: jobSpells also used for job "titles"
                if comId in comIdToName:
                    print(f'    {i+1})'.rjust(7, ' '), comIdToName[comId])
                elif comId in supIdToName:
                    print(f'    {i+1})'.rjust(7, ' '), supIdToName[comId].ljust(20, ' '), supIdToCost[comId], 'SA')
                else:
                    print(f'    {i+1})'.rjust(7, ' '), labelIdToLabel[labelId])
                    
            print('')
            print('')
        print('')
        print('')
        print('')
        print('')
        

    def printStats(self):
        print('====================')
        print('JOB STAT AFFINITIES')
        print('====================')
        print('')
        print('')

        jobNames = [ # ORDER TO MATCH MENU
            'Freelancer', 'Monk', 'White Mage', 'Black Mage', 'Knight', 'Thief', 'Merchant', 'Spell Fencer',
            'Time Mage', 'Ranger', 'Summoner', 'Valkyrie', 'Red Mage', 'Salve-Maker', 'Performer', 'Pirate',
            'Ninja', 'Swordmaster', 'Arcanist', 'Spiritmaster','Templar', 'Dark Knight', 'Vampire', 'Conjurer',
        ]
        statNames = ['HP', 'MP', 'STR', 'VIT', 'INT', 'MND', 'DEX', 'AGI']
        line = ' '*16
        for s in statNames:
            line += s.rjust(6, ' ')
        print(line)
        print('')
        for name in jobNames:
            line = '  '+name.ljust(14, ' ')
            stats = list(self.jobStats[name].values())
            line += f"{stats[0][0]}%".rjust(6, ' ')
            line += f"{stats[1][0]}%".rjust(6, ' ')
            line += f"{stats[2][0]}%".rjust(6, ' ')
            line += f"{stats[3][0]}%".rjust(6, ' ')
            line += f"{stats[4][0]}%".rjust(6, ' ')
            line += f"{stats[5][0]}%".rjust(6, ' ')
            line += f"{stats[7][0]}%".rjust(6, ' ')
            line += f"{stats[6][0]}%".rjust(6, ' ')
            print(line)
        print('')
        print('')
            
        
