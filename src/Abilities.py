import random

class ABILITIES:
    def __init__(self, abilityFiles):
        self.crowdFiles = abilityFiles.crowdFiles
        self.comAbilFile = self.crowdFiles['CommandAbility.btb']
        self.supAbilFile = self.crowdFiles['SupportAbility.btb']
        self.jobComFile = self.crowdFiles['JobCommand.btb']
        self.jobComIds = self.jobComFile.readCol(0)
        self.comAbilIds = self.comAbilFile.readCol(0)
        self.supAbilIds = self.supAbilFile.readCol(0)
        self.supAbilIdToRow = {i:r for r,i in enumerate(self.supAbilIds)}

    def getJobName(self, fileName):
        return self.fileToMage[fileName]

    def getSupRow(self, supAbilId):
        return self.supAbilIdToRow[supAbilId]
    
    def getSupCosts(self, id):
        assert id in self.supAbilIdToName, f"{id} not in supAbilIdToName"
        row = self.supAbilIds.index(id)
        return self.supAbilFile.readValue(row, self.costCol)

    def shuffleSupportCosts(self):
        costs = self.supAbilFile.readCol(self.costCol)
        random.shuffle(costs)
        self.supAbilFile.patchCol(costs, self.costCol)
        

        

class ABILITIES_BD(ABILITIES):
    def __init__(self, abilityFiles):
        super().__init__(abilityFiles)
        self.costCol = 5

        self.jobComNames = self.jobComFile.readTextStringAll(1)
        self.jobComIdToName = {i:n for i,n in zip(self.jobComIds, self.jobComNames)}

        self.comAbilNames = self.comAbilFile.readTextStringAll(4)
        self.comAbilIdToName = {}
        for i, n in zip(self.comAbilIds, self.comAbilNames):
            if not i in self.comAbilIdToName: # Skip repeats!
                self.comAbilIdToName[i] = n

        self.supAbilNames = self.supAbilFile.readTextStringAll(3)
        self.supAbilIdToName = {i:n for i,n in zip(self.supAbilIds, self.supAbilNames)}

        self.fileToMage = {
            'AbilityWMG.btb': 'White Mage',
            'AbilityBMG.btb': 'Black Mage',
            'AbilityWBM.btb': 'Red Mage',
            'AbilityTMG.btb': 'Time Mage',
            'AbilityMGS.btb': 'Spell Fencer',
            'AbilitySMG.btb': 'Summoner',
            'AbilitySMU.btb': 'Inquirer',
        }

        self.magicTables = [
            'AbilityWMG.btb',
            'AbilityBMG.btb',
            'AbilityTMG.btb',
            'AbilityMGS.btb',
        ]

    def getName(self, id):
        if id >= 2000 and id < 2100:
            return self.jobComIdToName[id]
        elif id < 1000:
            return self.comAbilIdToName[id]
        elif id >= 1000:
            return self.supAbilIdToName[id]
        return None


class ABILITIES_BS(ABILITIES):
    def __init__(self, abilityFiles):
        super().__init__(abilityFiles)
        self.costCol = 6
                
        self.jobComNames = self.jobComFile.readTextStringAll(2)
        self.jobComIdToName = {i:n for i,n in zip(self.jobComIds, self.jobComNames)}

        self.comAbilNames = self.comAbilFile.readTextStringAll(4)
        self.comAbilIdToName = {}
        for i, n in zip(self.comAbilIds, self.comAbilNames):
            if not i in self.comAbilIdToName: # Skip repeats!
                self.comAbilIdToName[i] = n

        self.supAbilNames = self.supAbilFile.readTextStringAll(4)
        self.supAbilIdToName = {i:n for i,n in zip(self.supAbilIds, self.supAbilNames)}

        self.fileToMage = {
            'AbilityBMG.btb': 'Black Mage',
            'AbilityWMG.btb': 'White Mage',
            'AbilityTMG.btb': 'Time Mage',
            'AbilitySMG.btb': 'Summoner',
            'AbilityWBM.btb': 'Red Mage',
            'AbilityBIS.btb': 'Bishop',
            # 'AbilityPOS.btb': 'Spellcraft', (spellcrafts)
            'AbilityWIZ.btb': 'Wizard',
            'AbilityAST.btb': 'Astrologian',
            'AbilityFOX.btb': 'Yokai',
        }

        self.magicTables = [
            'AbilityBMG.btb',
            'AbilityWMG.btb',
            'AbilityTMG.btb',
            'AbilityBIS.btb',
            'AbilityWIZ.btb',
            'AbilityAST.btb',
        ]

    def getName(self, id):
        if id >= 2000 and id < 2200:
            return self.jobComIdToName[id]
        elif id >= 10000 and id < 20000:
            return self.comAbilIdToName[id]
        elif id >= 20000:
            return self.supAbilIdToName[id]
        return None

