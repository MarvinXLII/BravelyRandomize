import random
import os
import shutil
import sys

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
    def readString(self, size=1):
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
        mainDir = os.getcwd()
        os.chdir(self.settings['rom'])
        self.paramaterIndex = FILE('Common_en/Paramater/index.fs')
        self.paramaterCrowd = FILE('Common_en/Paramater/crowd.fs')
        self.treasureIndex = FILE('Common_en/TreasureTable/index.fs')
        self.treasureCrowd = FILE('Common_en/TreasureTable/crowd.fs')
        self.shopIndex = FILE('Common_en/Shop/index.fs')
        self.shopCrowd = FILE('Common_en/Shop/crowd.fs')
        self.battleIndex = FILE('Common_en/Battle/index.fs')
        self.battleCrowd = FILE('Common_en/Battle/crowd.fs')
        os.chdir(mainDir)

        ## BUILD DATA CLASSES FOR EASY DATA ACCESS AND MANIPULATION
        self.paramater = DATA(self.paramaterIndex, self.paramaterCrowd)
        self.treasureTable = DATA(self.treasureIndex, self.treasureCrowd)
        self.shop = DATA(self.shopIndex, self.shopCrowd)
        self.battle = DATA(self.battleIndex, self.battleCrowd)

        ## BUILD NEW OBJECTS TO MAKE USE OF THIS DATA
        self.pcs = PCS(self.paramater)
        self.jobs = JOBS(self.paramater, self.shop)
        self.treasures = TREASURES(self.treasureTable, self.paramater)
        self.enemies = ENEMIES(self.battle)
        
    def randomize(self):
        random.seed(self.settings['seed'])
        if self.settings['jobs-commands']:
            self.jobs.shuffleCommands()
            self.jobs.shuffleSpells()
        if self.settings['jobs-specialties']:
            self.jobs.randomSpecialty() # MUST BE AFTER COMMAND/SUPPORT SHUFFLE
        if self.settings['jobs-sa-costs']:
            self.jobs.shuffleSupportAbilityCosts()
        if self.settings['jobs-stats']:
            self.jobs.shuffleStats()
        if self.settings['treasures']:
            self.treasures.shuffleTreasures()


    # Simpler to rescale enemy data rather than adjust shop costs for pg
    def qualityOfLife(self):
        # self.pcs.cutEXP(2)
        # self.pcs.zeroEXP()
        # self.jobs.cutJP(2)
        # self.jobs.zeroJP()
        self.enemies.scaleEXP(self.settings['qol-exp'])
        self.enemies.scaleJP(self.settings['qol-jp'])
        self.enemies.scalePG(self.settings['qol-pg'])

    def printLogs(self, path):
        temp = sys.stdout
        sys.stdout = open(os.path.join(path, 'spoiler.log'), 'w')
        self.jobs.printStats()
        # self.jobs.printMagics()
        self.jobs.printAbilities()
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
        
        writeFile(self.paramaterCrowd)
        writeFile(self.treasureCrowd)
        writeFile(self.shopCrowd)
        writeFile(self.battleCrowd)

class ENEMIES:
    def __init__(self, battle):
        self.battle = battle

    def scaleArray(self, array, scale, maxValue):
        newArray = [ min(a * scale, maxValue) for a in array ]
        return newArray
        
    def scaleEXP(self, scale):
        exp = self.battle.readData('MonsterData.btb', 91)
        newExp = self.scaleArray(exp, scale, 999999)
        self.battle.patchData(newExp, 'MonsterData.btb', 91)

    def scaleJP(self, scale):
        jp = self.battle.readData('MonsterData.btb', 92)
        newJP = self.scaleArray(jp, scale, 999)
        self.battle.patchData(newJP, 'MonsterData.btb', 92)

    def scalePG(self, scale):
        pg = self.battle.readData('MonsterData.btb', 93)
        newPG = self.scaleArray(pg, scale, 999999)
        self.battle.patchData(newPG, 'MonsterData.btb', 93)
        

class PCS:
    def __init__(self, paramater):
        self.paramater = paramater
        self.subFiles = [f"PcLevelTable00{i}.btb" for i in range(1, 5)]

    def zeroEXP(self):
        for subFile in self.subFiles:
            self.paramater.patchData([0]*99, subFile, 1) # TOTAL EXP
            self.paramater.patchData([0]*99, subFile, 2) # EXP FOR NEXT LEVEL

    def cutEXP(self, divisor):
        divisor *= 5
        for subFile in self.subFiles:
            exp = self.paramater.readData(subFile, 2)
            exp = [ round(e/divisor)*5 for e in exp ] # End with 0 or 5
            total = [exp[0]]*len(exp)
            for i in range(1, len(exp)):
                total[i] = total[i-1] + exp[i]
            self.paramater.patchData(total, subFile, 1)
            self.paramater.patchData(exp, subFile, 2)
        

# The main purpose of this class is to FIND address of data
# and help me view data as a table (i.e. rows and columns)
class DATA:
    def __init__(self, indexFileObj, crowdFileObj):
        self.indexFileObj = indexFileObj
        self.crowdFileObj = crowdFileObj
        self.index = {}
        self.crowd = {}
        self.subFileToBase = {}

        # JUST NEED OFFSETS FROM INDEX
        self.indexFileObj.address = 0
        indexOffset = self.indexFileObj.read()
        while True:
            base = self.indexFileObj.read()
            size = self.indexFileObj.read()
            stringCRC32 = self.indexFileObj.read()
            subFileName = self.indexFileObj.readString()
            self.subFileToBase[subFileName] = base
            if indexOffset == 0:
                break
            self.indexFileObj.address = indexOffset
            indexOffset = self.indexFileObj.read()

        for subFileName, base in self.subFileToBase.items():
            self.crowdFileObj.address = base + 8
            self.crowd[subFileName] = {}
            self.crowd[subFileName]['dataAddress'] = base + self.crowdFileObj.read()
            self.crowd[subFileName]['dataSize'] = self.crowdFileObj.read()
            # Labels for each row of table
            self.crowd[subFileName]['labelAddress'] = base + self.crowdFileObj.read()
            self.crowd[subFileName]['labelSize'] = self.crowdFileObj.read()
            # Both names and descriptions
            self.crowd[subFileName]['nameAddress'] = base + self.crowdFileObj.read()
            self.crowd[subFileName]['nameSize'] = self.crowdFileObj.read()
            # Entry data
            self.crowd[subFileName]['stride'] = self.crowdFileObj.read()
            self.crowd[subFileName]['number'] = self.crowdFileObj.read()
            # Load labels
            if self.crowd[subFileName]['labelSize'] > 0:
                self.crowd[subFileName]['labels'] = []
                self.crowdFileObj.address = self.crowd[subFileName]['labelAddress']
                while self.crowdFileObj.address < self.crowd[subFileName]['labelAddress'] + self.crowd[subFileName]['labelSize']:
                    string = self.crowdFileObj.readString()
                    self.crowd[subFileName]['labels'].append(string)
            # Load names and decriptions
            if self.crowd[subFileName]['nameSize'] > 0:
                self.crowd[subFileName]['names'] = []
                self.crowdFileObj.address = self.crowd[subFileName]['nameAddress']
                while self.crowdFileObj.address < self.crowd[subFileName]['nameAddress'] + self.crowd[subFileName]['nameSize']:
                    string = self.crowdFileObj.readString(size=2)
                    self.crowd[subFileName]['names'].append(string)

                
    def getAddress(self, key, row, col):
        base = self.crowd[key]['dataAddress']
        stride = self.crowd[key]['stride']
        offset = col*4 + stride*row
        return base + offset
                    
    # Read a single value of data
    def readValue(self, key, row, col):
        address = self.getAddress(key, row, col)
        return self.crowdFileObj.readValue(address)
    
    # Read a "column" of data
    def readData(self, key, col, row=None, rowLabel=None, numEntries=None):
        # Identify which row to start from
        if rowLabel:
            row = self.crowd[key]['labels'].index(rowLabel)
        elif not row:
            row = 0
        # Identify number of entries to read (i.e. how many rows to read from)
        if not numEntries:
            numEntries = self.crowd[key]['number']
        numEntries = min(numEntries, self.crowd[key]['number'])
        # Read column of data
        address = self.getAddress(key, row, col)
        stride = self.crowd[key]['stride']
        return self.crowdFileObj.readArray(address, numEntries, stride)
        
    # Patch a single value of data
    def patchValue(self, value, key, row, col):
        address = self.getAddress(key, row, col)
        self.crowdFileObj.patch(value, address)

    def patchData(self, data, key, col, row=None, rowLabel=None):
        # Identify which row to start from
        if rowLabel:
            row = self.crowd[key]['labels'].index(rowLabel)
        elif not row:
            row = 0
        # Patch column of data
        address = self.getAddress(key, row, col)
        stride = self.crowd[key]['stride']
        self.crowdFileObj.patchArray(data, address, stride)

    # row and col denote offset
    def patchNameString(self, string, key, row, col):
        offset = self.readValue(key, row, col)
        base = self.crowd[key]['nameAddress']
        self.crowdFileObj.patchString(string, base+offset, size=2)


class JOBS:
    def __init__(self, paramater, shops):
        self.paramater = paramater
        self.shops = shops
        self.jobFiles = []
        for i in range(24):
            j = str(i).rjust(2, '0')
            self.jobFiles.append(f'JobTable{j}.btb')
        self.shopMagicFiles = filter(lambda x: 'TW' in x, self.shops.subFileToBase.keys())
        self.shopMagicFiles = filter(lambda x: 'Magic' in x, self.shopMagicFiles)
        self.shopMagicFiles = list(filter(lambda x: '99' not in x, self.shopMagicFiles))
        
        self.jobNames = [
            'Freelancer', 'Knight', 'Black Mage', 'White Mage', 'Monk', 'Ranger',
            'Ninja', 'Time Mage', 'Spell Fencer', 'Swordmaster', 'Pirate', 'Dark Knight',
            'Templar', 'Vampire', 'Arcanist', 'Summoner', 'Conjurer', 'Valkyrie',
            'Spiritmaster', 'Salve-Maker', 'Red Mage', 'Thief', 'Merchant', 'Performer',
        ]

        # List mage subfiles
        self.mageNames = ['Black Mage', 'Spell Fencer', 'Summoner', 'Conjurer',
                          'Time Mage', 'Red Mage', 'White Mage']
        self.mageSubFiles = ['AbilityBMG.btb', 'AbilityMGS.btb', 'AbilitySMG.btb','AbilitySMU.btb',
                         'AbilityTMG.btb','AbilityWBM.btb','AbilityWMG.btb']

        # Load all abilities
        self.commandIds = self.paramater.readData('CommandAbility.btb', 0)
        self.commandNames = self.paramater.crowd['CommandAbility.btb']['names'][::2]
        self.comIdToName = {i:n for n, i in zip(self.commandNames, self.commandIds)} # ID TO NAME IS UNIQUE
        self.comIdToName[361] = 'Genome Ability'
        for i in range(75, 94): # add SF to SpellFencer names
            self.comIdToName[i] = self.comIdToName[i] + '*'
        self.comNameToId = {n:i for i,n in self.comIdToName.items()}
        self.supportIds = self.paramater.readData('SupportAbility.btb', 0)
        self.supportNames = self.paramater.crowd['SupportAbility.btb']['names'][::2]
        self.supNameToId = {n:i for n, i in zip(self.supportNames, self.supportIds)}
        self.supIdToName = {i:n for n, i in zip(self.supportNames, self.supportIds)}
        self.supportCosts = self.paramater.readData('SupportAbility.btb', 5)
        self.supIdToCosts = {i:c for i, c in zip(self.supportIds, self.supportCosts)}

        # Load command titles
        self.commandTitles = self.paramater.crowd['JobCommand.btb']['names'][::2]
        self.commandTitleId = self.paramater.readData('JobCommand.btb', 0)
        self.commandIconId = self.paramater.readData('JobCommand.btb', 4)
        self.titleIdToTitle = {i:t for i,t in zip(self.commandTitleId, self.commandTitles)}
        self.titleIdToTitle[0] = None
        self.titleIdToIcon = {t:i for t, i in zip(self.commandTitleId, self.commandIconId)}
        
        # Load all job commands and stats
        self.jobStats = {}
        self.jobTitles = {}
        self.jobCommands = {}
        self.jobSpecialty = {}
        self.isSpellCaster = {}
        self.isCommand = {i:False for i in self.commandIds} # Will need to filter commands
        for jobName, subFile in zip(self.jobNames, self.jobFiles):
            self.jobSpecialty[jobName] = self.paramater.readValue(subFile, 0, 12)
            self.jobCommands[jobName] = self.paramater.readData(subFile, 13)
            self.jobTitles[jobName] = self.paramater.readData(subFile, 16)
            self.isSpellCaster[jobName] = 0 in self.jobCommands[jobName]
            for i in self.jobCommands[jobName]:
                if i in self.isCommand:
                    self.isCommand[i] = True
            self.jobStats[jobName] = {
                'HP': self.paramater.readData(subFile, 4),
                'MP': self.paramater.readData(subFile, 5),
                'STR': self.paramater.readData(subFile, 6),
                'VIT': self.paramater.readData(subFile, 7),
                'INT': self.paramater.readData(subFile, 8),
                'MND': self.paramater.readData(subFile, 9),
                'DEX': self.paramater.readData(subFile, 10),
                'AGI': self.paramater.readData(subFile, 11),
            }

        # Load spell/fencer/summon commands
        self.isMagic = {i:False for i in self.commandIds} # Filter magic spells
        self.isFencer = {i:False for i in self.commandIds} # Filter fencing spells
        self.isSummon = {i:False for i in self.commandIds} # Filter summons
        self.mageSpells = {}
        self.spellIdToItem = {}
        def loadSpells(name, subFile, boolDict):
            spellId = self.paramater.readData(subFile, 1)
            itemId = self.paramater.readData(subFile, 2)
            for s, i in zip(spellId, itemId):
                self.spellIdToItem[s] = i
            self.mageSpells[name] = spellId
            for spell in spellId:
                boolDict[spell] = True

        loadSpells('Spell Fencer', 'AbilityMGS.btb', self.isFencer)
        loadSpells('Summoner', 'AbilitySMG.btb', self.isSummon)
        loadSpells('Conjurer', 'AbilitySMU.btb', self.isSummon)
        loadSpells('Black Mage', 'AbilityBMG.btb', self.isMagic)
        loadSpells('White Mage', 'AbilityWMG.btb', self.isMagic)
        loadSpells('Red Mage', 'AbilityWBM.btb', self.isMagic)
        loadSpells('Time Mage', 'AbilityTMG.btb', self.isMagic)
        
        # Icon stuff
        self.supportJobIds = self.paramater.readData('SupportAbility.btb', 2)
        self.supportIconCommands = self.paramater.readData('SupportAbility.btb', 66)
        self.supJobIdToIcon = {sup:com for sup, com in zip(self.supportJobIds, self.supportIconCommands)}
        

    def shuffleCommands(self):

        # Assign support skills to mages first
        candidates = list(self.supportIds)
        random.shuffle(candidates)
        names = filter(lambda x: self.isSpellCaster[x], self.jobNames)
        for name in names:
            commands = self.jobCommands[name]
            for i, c in enumerate(commands):
                if c > 0:
                    commands[i] = candidates.pop()

        # Assign skills to remaining jobs
        commands = sorted(set(filter(lambda x: self.isCommand[x], self.commandIds)))        
        candidates += commands
        random.shuffle(candidates)
        names = filter(lambda x: not self.isSpellCaster[x], self.jobNames)
        n = len(self.jobCommands[self.jobNames[0]])
        for name in names:
            for i in range(n):
                self.jobCommands[name][i] = candidates.pop()

        # Patch all job commands
        for name, subFile in zip(self.jobNames, self.jobFiles):
            self.paramater.patchData(self.jobCommands[name], subFile, 13)

        # Update support ability icons
        commandToJobId = {}
        for i, name in enumerate(self.jobNames):
            for command in self.jobCommands[name]:
                commandToJobId[command] = i

        jobIds = [0] * len(self.supportIds)
        icons = [0] * len(self.supportIds)
        for i, s in enumerate(self.supportIds):
            if s in commandToJobId:
                jobIds[i] = commandToJobId[s]
                icons[i] = self.supJobIdToIcon[commandToJobId[s]]

        self.paramater.patchData(jobIds, 'SupportAbility.btb', 2)
        self.paramater.patchData(jobIds, 'SupportAbilityAL.btb', 2)
        self.paramater.patchData(icons, 'SupportAbility.btb', 66)
        self.paramater.patchData(icons, 'SupportAbilityAL.btb', 66)

            

    # OMIT SUMMONS
    def shuffleSpells(self):

        mageFiles = []
        mageNames = []
        mageTitles = []
        for jobName, subFile in zip(self.jobNames, self.jobFiles):
            if self.isSpellCaster[jobName]:
                mageFiles.append(subFile)
                mageNames.append(jobName)
                mageTitles.append(self.jobTitles[jobName])
        magicByJob = [list(filter(lambda x: x > 0, m)) for m in mageTitles]

        # Shuffle levels first
        for magic in magicByJob:
            random.shuffle(magic)

        # Shuffle across jobs at each level
        for i in range(6):
            level = []
            for m in magicByJob:
                if i < len(m): # Only 4 entries for Red Mage
                    level.append(m[i])
            random.shuffle(level)
            for m in magicByJob:
                if i < len(m):
                    m[i] = level.pop()
                
        # Update self.jobTitles via mageTitles
        oldToNewCommand = {}
        for i, name in enumerate(mageNames):
            titles = mageTitles[i]
            magicLevels = magicByJob[i]
            for i, ti in enumerate(titles):
                if ti > 0:
                    # titles[i] = magicLevels.pop(0)
                    old = titles[i]
                    new = magicLevels.pop(0)
                    oldToNewCommand[old] = new
                    titles[i] = new

        # Patch titles
        for name, subFile in zip(mageNames, mageFiles):
            self.paramater.patchData(self.jobTitles[name], subFile, 16)

        # Update title descriptions ?????????????
        commands = self.paramater.readData('JobTable.btb', 4)
        newToOldCommand = {n:o for o, n in oldToNewCommand.items()}
        for i, ti in enumerate(commands):
            if ti in oldToNewCommand:
                commands[i] = oldToNewCommand[ti]
        for i, ti in enumerate(self.commandTitleId):
            if ti in newToOldCommand:
                self.commandIconId[i] = self.titleIdToIcon[newToOldCommand[ti]]
        self.paramater.patchData(commands, 'JobTable.btb', 4)
        self.paramater.patchData(self.commandIconId, 'JobCommand.btb', 4)

        # Overwrite all magic command strings
        for i, comId in enumerate(self.commandTitleId):
            if comId in oldToNewCommand: # Check if it is a magic/summon command
                self.paramater.patchNameString('Cast magic/summons.', 'JobCommand.btb', i, 3)
        
        # wm = self.mageSpells['White Mage']
        # bm = self.mageSpells['Black Mage']
        # tm = self.mageSpells['Time Mage']
        # sf = self.mageSpells['Spell Fencer']
        # rm = self.mageSpells['Red Mage']
        # prevItems = [self.spellIdToItem[i] for i in wm + bm + tm]
        
        # ########################
        # # Assign spells groups #
        # ########################

        # slots = {
        #     'White Mage': [True]*18,
        #     'Black Mage': [True]*18,
        #     'Time Mage': [True]*18,
        # }
        # candidates = wm + bm + tm

        # def assignGroupToMage(group):
        #     spellIds = [self.comNameToId[i] for i in group]
        #     # Pick a mage with enough vacant slots
        #     mage, weights = random.sample(list(slots.items()), 1)[0]
        #     while sum(weights) <= len(group): # redo if not enough vacant slots
        #         mage, weights = random.sample(list(slots.items()), 1)[0]
        #     # Pick 3 unique slots
        #     idx = set([])
        #     while len(idx) < len(group):
        #         idx.add( random.choices(population=range(18), weights=weights)[0] )
        #     # Assign spells to these slots
        #     idx = sorted(idx)
        #     for i in idx:
        #         weights[i] = False
        #         spell = spellIds.pop(0)
        #         self.mageSpells[mage][i] = spell
        #         candidates.remove(spell)

        # groups = [
        #     ['Cure', 'Cura', 'Curaga'],
        #     ['Raise','Arise'],
        #     ['Blindna', 'Poisona', 'Esuna','Esunaga'],
        #     ['Aero','Aerora', 'Aeroga'],
        #     ['Shell','Reflect'],
        #     ['Fire','Fira','Firaga'],
        #     ['Blizzard','Blizzara','Blizzaga'],
        #     ['Thunder','Thundara','Thundaga'],
        #     ['Quake','Quara','Quaga'],
        #     ['Slow','Slowga'],
        #     ['Haste','Hastega'],
        #     ['Veil','Veilga'],
        #     ['Gravity','Graviga'],
        #     ['Regen','Reraise'],
        #     ['Comet', 'Meteor']
        # ]
        # random.shuffle(groups)
        # for group in groups:
        #     assignGroupToMage(group)

        # # Assign remaining spells
        # random.shuffle(candidates)
        # for mage, weights in slots.items():
        #     for i, w in enumerate(weights):
        #         if not w: continue # Slot already replaced
        #         self.mageSpells[mage][i] = candidates.pop()

        # # Shuffle SpellFencer 
        # # THIS IS EXTREMELY BIASED. NOT SURE HOW TO DO IT WELL
        # # Done like this to ensure Fire < Fira < Firaga.
        # for i in range(17, 0, -1):
        #     minval = (i // 6) * 6
        #     j = random.randint(minval, i)
        #     sf[i], sf[j] = sf[j], sf[i]

        # # Red Mage
        # rm[:12] = wm[:12]
        # rm[12:] = bm[:12]

        # # Patch spells and items
        # for name, subFile in zip(self.mageNames, self.mageSubFiles):
        #     spells = self.mageSpells[name]
        #     items = [self.spellIdToItem[i] for i in spells]
        #     self.paramater.patchData(spells, subFile, 1)
        #     self.paramater.patchData(items, subFile, 2)

        # ###########################
        # # Patch mage descriptions #
        # ###########################

        # def getString(spellIds):
        #     nameList = [self.comIdToName[i] for i in spellIds]
        #     nameList[-1] = 'and ' + nameList[-1]
        #     if len(nameList) > 4:
        #         nameList[3] = '\n' + nameList[3]
        #     return 'Enables use of\n' + ', '.join(nameList) + '.'
        
        # # White mage
        # spells = self.mageSpells['White Mage']
        # spellNames = [self.comIdToName[i] for i in spells]
        # for i in range(6):
        #     string = getString(spells[i*3:(i+1)*3])
        #     self.paramater.patchNameString(string, 'DetailInfoMagicTable.btb', i, 2)

        # # Black Mage
        # spells = self.mageSpells['Black Mage']
        # spellNames = [self.comIdToName[i] for i in spells]
        # for i, row in enumerate(range(6, 12)):
        #     string = getString(spells[i*3:(i+1)*3])
        #     self.paramater.patchNameString(string, 'DetailInfoMagicTable.btb', row, 2)

        # # Time Mage
        # spells = self.mageSpells['Time Mage']
        # spellNames = [self.comIdToName[i] for i in spells]
        # for i, row in enumerate(range(12, 18)):
        #     string = getString(spells[i*3:(i+1)*3])
        #     self.paramater.patchNameString(string, 'DetailInfoMagicTable.btb', row, 2)

        # # Spell Fencer
        # spells = self.mageSpells['Spell Fencer']
        # spellNames = [self.comIdToName[i] for i in spells]
        # for i, row in enumerate(range(19, 25)):
        #     string = getString(spells[i*3:(i+1)*3])
        #     self.paramater.patchNameString(string, 'DetailInfoMagicTable.btb', row, 2)

        # # Red Mage
        # spells = self.mageSpells['Red Mage']
        # spellNames = [self.comIdToName[i] for i in spells]
        # for i, row in enumerate(range(36, 40)):
        #     w = spells[i*3:(i+1)*3]
        #     b = spells[12+i*3:12+(i-1)*3]
        #     string = getString(w+b)
        #     self.paramater.patchNameString(string, 'DetailInfoMagicTable.btb', row, 2)

        # ####################
        # # Patch item icons #
        # ####################

        # itemId = self.paramater.readData('ItemTable.btb', 0, row=486, numEntries=101)
        # icons = self.paramater.readData('ItemTable.btb', 11, row=486, numEntries=101)
        # prevToIcon = {p:i for p, i in zip(itemId, icons)}
        
        # newItems = [self.spellIdToItem[i] for i in wm + bm + tm]
        # newToPrev = {n:p for n, p in zip(newItems, prevItems)}
        # prevToNew = {p:n for n, p in zip(newItems, prevItems)}

        # newIcons = []
        # for i in itemId:
        #     if i in newToPrev:
        #         newIcons.append(prevToIcon[newToPrev[i]])
        #     else:
        #         newIcons.append(prevToIcon[i])
        # self.paramater.patchData(newIcons, 'ItemTable.btb', 11, row=486)

        # ###############
        # # Update shop #
        # ###############

        # for shopFile in self.shopMagicFiles:
        #     items = self.shops.readData(shopFile, 0)
        #     newItems = [prevToNew[i] for i in items]
        #     random.shuffle(newItems)
        #     self.shops.patchData(newItems, shopFile, 0)
        

    def randomSpecialty(self):

        candidates = list(self.supportIds)
        candidates.remove(self.supNameToId['Genome Drain'])
        random.shuffle(candidates)
        for name in self.jobNames:
            if self.comNameToId['Genome Ability'] in self.jobCommands[name]:
                self.jobSpecialty[name] = self.supNameToId['Genome Drain']
            else:
                self.jobSpecialty[name] = candidates.pop()

        # Patch all specialties
        for name, subFile in zip(self.jobNames, self.jobFiles):
            self.paramater.patchValue(self.jobSpecialty[name], subFile, 0, 12)

    def shuffleSupportAbilityCosts(self):
        random.shuffle(self.supportCosts)
        for cost, supId in zip(self.supportCosts, self.supIdToCosts.keys()):
            self.supIdToCosts[supId] = cost
        self.paramater.patchData(self.supportCosts, 'SupportAbility.btb', 5)
        self.paramater.patchData(self.supportCosts, 'SupportAbilityAL.btb', 5)
            
        

    def zeroJP(self):
        for jobFile in self.jobFiles:
            self.paramater.patchData([0]*14, jobFile, 1)
            self.paramater.patchData([0]*14, jobFile, 2)

    def cutJP(self, divisor):
        divisor *= 5
        for jobFile in self.jobFiles:
            jp = self.paramater.readData(jobFile, 2)
            jp = [ round(j/divisor)*5 for j in jp ]
            total = [jp[0]]*len(jp)
            for i in range(1, len(jp)):
                total[i] = total[i-1] + jp[i]
            self.paramater.patchData(total, jobFile, 1)
            self.paramater.patchData(jp, jobFile, 2)


    def shuffleStats(self):
        statNames = list(self.jobStats[self.jobNames[0]].keys()) # HP, MP, ...
        for stat in statNames:
            # Fisher-Yates on all stat arrays, looping over jobNames
            for i in range(23, 0, -1):
                j = random.randint(0, i)
                nameA = self.jobNames[i]
                nameB = self.jobNames[j]
                statsOfJobA = self.jobStats[nameA][stat]
                statsOfJobB = self.jobStats[nameB][stat]
                self.jobStats[nameA][stat], self.jobStats[nameB][stat] = statsOfJobB, statsOfJobA

        # Patch stats
        for name, subFile in zip(self.jobNames, self.jobFiles):
            stats = self.jobStats[name]
            for i, key in enumerate(stats.keys()):
                self.paramater.patchData(stats[key], subFile, i+4)


    def printStats(self):
        print('====================')
        print('JOB STAT AFFINITIES')
        print('====================')
        print('')
        print('')

        jobNames = sorted(self.jobNames)
        statNames = list(self.jobStats[jobNames[0]].keys())
        line = ' '*16
        for s in statNames:
            line += s.rjust(6, ' ')
        print(line)
        print('')
        for name in jobNames:
            line = '  '+name.ljust(14, ' ')
            for stat in self.jobStats[name].values():
                line += f"{stat[0]}%".rjust(6, ' ')
            print(line)
        print('')
        print('')
            
        

    def printMagics(self):
        print('============')
        print('MAGIC LEVELS')
        print('============')
        print('')
        print('')

        def printMage(mage):
            titleId = list(filter(lambda x: x > 0, self.jobTitles[mage]))
            numLevels = len(titleId)
            numSpells = len(self.mageSpells[mage])
            numPerLevel = int(numSpells / numLevels)
            print(mage)
            print('-'*len(mage))
            print('')
            for i in range(numLevels):
                titleString = self.titleIdToTitle[titleId[i]]
                spells = self.mageSpells[mage][i*numPerLevel:(i+1)*numPerLevel]
                spellNames = ', '.join([self.comIdToName[i] for i in spells])
                print('  ', titleString.ljust(20, ' '), spellNames)
            print('')
            print('')

        printMage('White Mage')
        printMage('Black Mage')
        printMage('Red Mage')
        printMage('Time Mage')
        printMage('Spell Fencer')
        printMage('Summoner')
        printMage('Conjurer')

                
    def printAbilities(self):
        # SETUP FOR MAGIC PRINTOUTS
        
        print('=============')
        print('JOB ABILITIES')
        print('=============')
        print('')
        print('')
        jobNames = sorted(self.jobNames)
        for name in jobNames:
            if name in self.mageSpells:
                spells = list(self.mageSpells[name])
            print(name)
            print('-'*len(name))
            print('')
            print('  Specialty:', self.supIdToName[self.jobSpecialty[name]])
            print('')
            print('  Abilities:')
            for i, (comId, titleId) in enumerate(zip(self.jobCommands[name], self.jobTitles[name])):
                if comId in self.comIdToName:
                    print(f'    {i+1})'.rjust(7, ' '), self.comIdToName[comId])
                elif comId in self.supIdToName:
                    print(f'    {i+1})'.rjust(7, ' '), self.supIdToName[comId].ljust(20, ' '), self.supIdToCosts[comId], 'SA')
                else:
                    print(f'    {i+1})'.rjust(7, ' '), self.titleIdToTitle[titleId])
                    
            print('')
            print('')
        print('')
        print('')
        print('')
        print('')
                    


class TREASURES:
    def __init__(self, treasures, paramater):
        self.treasures = treasures
        self.paramater = paramater

        # Misc stuff needed
        # -- isDummy dict to map ID to bool (use for filtering allExcluded)
        itemIds = self.paramater.readData('ItemTable.btb', 0)
        itemNames = self.paramater.crowd['ItemTable.btb']['names'][::2]
        self.isDummy = {itemId: 'Dummy' in name for itemId, name in zip(itemIds, itemNames)}
        self.itemIdToName = {itemId:name for itemId, name in zip(itemIds, itemNames)}

        # Load data from traesures
        self.entries = {}
        for subFile in self.treasures.crowd.keys():
            if subFile == 'TreasureMessageTable.btb':
                continue
            itemId = self.treasures.readData(subFile, 1)
            money = self.treasures.readData(subFile, 2)
            numItems = self.treasures.readData(subFile, 3)
            self.entries[subFile] = list(zip(itemId, money, numItems))

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


    def shuffleTreasures(self):

        candidates = []
        for treasureList in self.entries.values():
            candidates += list(filter(lambda x: any(x), treasureList))

        # Add 1 entry of all items not normally found in chests
        allIncluded = [c[0] for c in candidates]
        allExcluded = self.paramater.readData('ItemTable.btb', 0)
        allExcluded = list(filter(lambda x: not self.isDummy[x], allExcluded)) # Filter dummy items
        allExcluded = sorted(list(set(allExcluded).difference(allIncluded))) # Filter included items
        allExcluded = [(i,0,1) for i in allExcluded]
        candidates += allExcluded

        # Filter all items and slots not allowed (e.g. key items, asterisks)
        candidates = list(filter(lambda x: x[0] < 90000, candidates))

        # Randomize
        random.shuffle(candidates)
        for treasureList in self.entries.values():
            for i, treasure in enumerate(treasureList):
                if treasure[0] >= 90000: continue # Skip key items & asterisks
                if any(treasure): # Skip empty slots
                    treasureList[i] = candidates.pop()

        # Copy chests from airship (ch 6+) to ship
        self.entries['TW_14.trb'][:7] = self.entries['TW_20.trb'][:7]

        for subFile, treasureList in self.entries.items():
            itemId, money, numItems = zip(*treasureList)
            self.treasures.patchData(itemId, subFile, 1)
            self.treasures.patchData(money, subFile, 2)
            self.treasures.patchData(numItems, subFile, 3)

    def print(self):

        print('=========')
        print('TREASURES')
        print('=========')
        print('')
        for subFile, treasureList in self.entries.items():
            print(self.fileToLoc[subFile]+':')
            for itemId, money, numItems in treasureList:
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


