from Classes import TABLE, CROWD
from Battles import BATTLES, BATTLES_BD
from Items import ITEMS, ITEMS_BD
from Pc import PC
from Jobs import JOBS_BD, JOBS_BS
from Abilities import ABILITIES_BD, ABILITIES_BS
from Shop import SHOP, SHOP_BD
from Magic import MAGIC_BD, MAGIC_BS
from Treasures import TREASURES
import os
import shutil
import random
import sys
import hjson

class ROM:
    def __init__(self, settings):
        self.settings = settings
        self.seed = self.settings['seed']
        self.pathIn = self.settings['rom']
        self.pathOut = os.path.join(os.getcwd(), f"patch_{self.settings['game']}_{self.seed}")
        if os.path.isdir(self.pathOut):
            shutil.rmtree(self.pathOut)
        os.mkdir(self.pathOut)

    def fail(self):
        shutil.rmtree(self.pathOut)

    def printSettings(self):
        filename = os.path.join(self.pathOut, 'settings.json')
        with open(filename, 'w') as file:
            hjson.dump(self.settings, file)

    def loadCrowd(self, path):
        src = os.path.join(self.pathIn, path)
        dest = os.path.join(self.pathOut, 'romfs', path)
        shutil.copytree(src, dest)
        return CROWD(dest)

    def loadTable(self, fileName):
        src = os.path.join(self.pathIn, fileName)
        dest = os.path.join(self.pathOut, 'romfs', fileName)
        base = os.path.dirname(dest)
        if not os.path.isdir(base):
            os.makedirs(base)
        shutil.copy(src, dest)
        return TABLE(dest)

    def randomize(self):
        # Shuffles magic among mages
        if self.settings['jobs-magic']:
            print('Shuffling spells')
            random.seed(self.seed)
            self.magic.shuffleMagic()

        # Shuffle support ability costs
        if self.settings['jobs-support-costs']:
            print('shuffling support ability costs')
            random.seed(self.seed)
            self.abilities.shuffleSupportCosts()

        # Shuffle affinities (HP, MP, ...)
        if self.settings['jobs-stat-affinities']:
            print('shuffling job stat affinities')
            random.seed(self.seed)
            self.jobs.shuffleAffinities()

        # Shuffle specialties
        if self.settings['jobs-specialties']:
            print('randomizing job specialties')
            random.seed(self.seed)
            self.jobs.randomSpecialties()

        
        # Shuffle command abilities
        if self.settings['jobs-commands']:
            print('shuffling job commands')
            random.seed(self.seed)
            self.jobs.shuffleCommands()

    def qualityOfLife(self):

        if self.settings['qol-mastered-jobs']:
            print('Jobs will be Mastered!')
            self.jobs.zeroJP()

        if 'no-exp'in self.settings:
            if self.settings['no-exp']:
                print('Start at level 99!')
                self.pcs.zeroEXP()

        if self.settings['qol-teleport-stones']:
            print('Teleport Stones will be free!')
            self.items.changeCostByName('Teleport Stone', 0)

        # BATTLE STUFF
        print('Rescaling experience gained by', self.settings['qol-exp'])
        self.battles.scaleEXP(self.settings['qol-exp'])
        print('Rescaling JP gained by', self.settings['qol-jp'])
        self.battles.scaleJP(self.settings['qol-jp'])
        print('Rescaling pg gained by', self.settings['qol-pg'])
        self.battles.scalePG(self.settings['qol-pg'])
        

class BS(ROM):
    def __init__(self, settings):
        super().__init__(settings)

        # Load data
        self.itemTable = self.loadTable('Common_en/Parameter/Item/ItemTable.btb')
        self.abilityData = self.loadCrowd('Common_en/Parameter/Ability')
        self.jobData = self.loadCrowd('Common_en/Parameter/Job')
        self.shopData = self.loadCrowd('Common_en/Shop')
        self.pcData = self.loadCrowd('Common_en/Parameter/Pc')
        self.battleData = self.loadCrowd('Common_en/Battle')
        self.detailInfoData = self.loadCrowd('Common_en/Parameter/DetailInfo')

        # Manip data
        self.pcs = PC(self.pcData)
        self.items = ITEMS(self.itemTable)
        self.battles = BATTLES(self.battleData)
        self.abilities = ABILITIES_BS(self.abilityData)
        self.shops = SHOP(self.shopData)
        self.jobs = JOBS_BS(self.jobData, self.abilities)
        self.magic = MAGIC_BS(self.abilities, self.items, self.detailInfoData)

    def dumpFiles(self):
        self.jobData.dump()
        self.abilityData.dump() # ABILITIES & SUPPORT
        self.shopData.dump()
        self.itemTable.dump()
        self.pcData.dump()
        self.battleData.dump()
        self.detailInfoData.dump()

    def randomize(self):
        super().randomize()
        
        # Shuffle equipment grades (S, A, ...)
        if self.settings['jobs-equip-aptitudes']:
            print('Shuffling job equipment aptitudes')
            random.seed(self.seed)
            self.jobs.shuffleAptitudes()
            
    def printLogs(self):
        temp = sys.stdout
        sys.stdout = open(os.path.join(self.pathOut, 'spoiler.log'), 'w', encoding='utf-8')
        self.jobs.print()
        self.magic.print()
        sys.stdout = temp
        



class BD(ROM):
    def __init__(self, settings):
        super().__init__(settings)

        # Load data
        self.parameterData = self.loadCrowd('Common_en/Paramater')
        self.treasureData = self.loadCrowd('Common_en/TreasureTable')
        self.battleData = self.loadCrowd('Common_en/Battle')
        self.shopData = self.loadCrowd('Common_en/Shop')
        
        # Manip data
        self.pcs = PC(self.parameterData)
        self.items = ITEMS_BD(self.parameterData)
        self.battles = BATTLES_BD(self.battleData)
        self.abilities = ABILITIES_BD(self.parameterData)
        self.treasures = TREASURES(self.treasureData, self.items)
        self.shops = SHOP_BD(self.shopData, self.parameterData)
        self.jobs = JOBS_BD(self.parameterData, self.abilities)
        self.magic = MAGIC_BD(self.abilities, self.items)

    def dumpFiles(self):
        self.treasureData.dump()
        self.parameterData.dump()
        self.battleData.dump()
        self.shopData.dump()

    def randomize(self):
        super().randomize()

        # Shuffle treasures
        if self.settings['treasures']:
            print('Shuffling treasures')
            random.seed(self.seed)
            self.treasures.shuffleTreasures()
            
        # Shuffle support abilities
        if self.settings['jobs-support']:
            print('shuffling job support')
            random.seed(self.seed)
            self.jobs.shuffleSupport()
        
    def printLogs(self):
        temp = sys.stdout
        sys.stdout = open(os.path.join(self.pathOut, 'spoiler.log'), 'w', encoding='utf-8')
        self.jobs.print()
        self.magic.print()
        self.treasures.print()
        sys.stdout = temp
