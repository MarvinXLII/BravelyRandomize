import random

# SHUFFLE ABILITY TABLES and update items
class MAGIC:
    def __init__(self, abilities, items):
        self.abilities = abilities
        self.items = items

        ### LOAD ALL ABILITY DATA
        self.data = {} # USE KEY AS ITEMID (PROBABLY EASIER TO MAP TO STRINGS LATER?)
        for fileName in self.abilities.magicTables:
            fileObj = self.abilities.crowdFiles[fileName]
            for row in range(fileObj.count):
                level = fileObj.readValue(row, 0)
                abilId = fileObj.readValue(row, 1)
                itemId = fileObj.readValue(row, 2)
                order = self.items.getOrder(itemId)
                icon = self.items.getIcon(itemId)
                cost = self.items.getCost(itemId)
                self.data[abilId] = {
                    'file': fileName,
                    'row': row,
                    'level': level,
                    'abilId': abilId,
                    'itemId': itemId,
                    'order': order,
                    'icon': icon,
                    'cost': cost,
                }
                self.data[abilId]['swap'] = {
                    'abilId': abilId,
                    'itemId': itemId,
                }

    def shuffleMagic(self):
                
        # Shuffle
        for level in range(1, 8):
            magic = [m for m in self.data.values() if m['level'] == level]
            # Fisher-Yates
            for i in range(len(magic)):
                j = random.randrange(i, len(magic))
                magic[i]['swap'], magic[j]['swap'] = magic[j]['swap'], magic[i]['swap']

        # Patch
        for key in self.data:
            fileObj = self.abilities.crowdFiles[self.data[key]['file']]
            row = self.data[key]['row']
            # Load "new" data
            abilId = self.data[key]['swap']['abilId']
            itemId = self.data[key]['swap']['itemId']
            # Patch ability table
            fileObj.patchValue(abilId, row, 1)
            fileObj.patchValue(itemId, row, 2)
            # Patch item table (for magic shop)
            self.items.changeOrder(itemId, self.data[key]['order'])
            self.items.changeIcon(itemId, self.data[key]['icon'])
            self.items.changeCost(itemId, self.data[key]['cost'])

        ## UPDATE RED MAGE
        redMageFile = self.abilities.crowdFiles['AbilityWBM.btb']
        abilIdCol = redMageFile.readCol(1)
        for row, key in enumerate(abilIdCol):
            # Load "new" data
            abilId = self.data[key]['swap']['abilId']
            itemId = self.data[key]['swap']['itemId']
            # Patch ability table
            redMageFile.patchValue(abilId, row, 1)
            redMageFile.patchValue(itemId, row, 2)

    def print(self):
        print('')
        print('')
        print('')
        print('====================')
        print('JOB SPELLS & SUMMONS')
        print('====================')
        print('')
        print('')
        for fileName, name in self.abilities.fileToMage.items():
            fileObj = self.abilities.crowdFiles[fileName]
            levels = fileObj.readCol(0)
            comAbilIds = fileObj.readCol(1)
            data = {i:[] for i in range(1,9)}
            for l, a in zip(levels, comAbilIds):
                data[l].append(self.abilities.getName(a))
            
            print(name)
            print('-'*len(name))
            print('')
            for level, magic in data.items():
                if magic:
                    print(f' Level {level}:  ', ', '.join(magic))
            print('')
            print('')
        print('')
        print('')



class MAGIC_BD(MAGIC):
    def __init__(self, parameterData, items):
        super().__init__(parameterData, items)
        self.detailInfo = parameterData.crowdFiles['DetailInfoMagicTable.btb']
        self.filesToCommand = {
            'AbilityWMG.btb': list(range(2001, 2007)),
            'AbilityBMG.btb': list(range(2009, 2015)),
            'AbilityTMG.btb': list(range(2025, 2031)),
            'AbilityMGS.btb': list(range(2037, 2043)),
            'AbilitySMG.btb': [2031, 2050, 2051, 2052, 2053, 2054],
            'AbilitySMU.btb': list(range(2055, 2061)),
            'AbilityWBM.btb': list(range(2064, 2068)),
        }
        # Keep Spell Fencer separate
        self.spellFencer = {}
        for a,d in self.data.items():
            if d['file'] == 'AbilityMGS.btb':
                itemId = d['itemId']
                self.spellFencer[itemId] = d
        for sf in self.spellFencer.values():
            a = sf['abilId']
            del self.data[a]

    def shuffleMagic(self):
        super().shuffleMagic()

        # Shuffle Spell Fencer
        sfFileObj = self.abilities.crowdFiles['AbilityMGS.btb']
        for key, data in self.data.items():
            fileName = data['file']
            fileObj = self.abilities.crowdFiles[fileName]
            itemId = fileObj.readValue(data['row'], 2)
            if itemId in self.spellFencer:
                if random.random() < 0.5:
                    abilId = data['swap']['abilId']
                    abilIdSF = self.spellFencer[itemId]['abilId']
                    rowSF = self.spellFencer[itemId]['row']
                    fileObj.patchValue(abilIdSF, data['row'], 1)
                    sfFileObj.patchValue(abilId, rowSF, 1)

        # Update detailInfo
        detailComList = self.detailInfo.readCol(0)
        comIdToRow = {i:r for r,i in enumerate(detailComList)}
        for fileName, commandList in self.filesToCommand.items():
            fileObj = self.abilities.crowdFiles[fileName]
            levels = fileObj.readCol(0)
            abilIds = fileObj.readCol(1)
            itemIds = fileObj.readCol(2)
            tmp = list(zip(levels, itemIds, abilIds))
            for i, comId in enumerate(commandList):
                _, iIds, aIds = list(zip(*filter(lambda x: x[0] == i+1, tmp)))
                # Get names
                names = []
                for i, a in zip(iIds, aIds):
                    if a >= 75 and a <= 92:
                        names.append( self.items.getName(i) + ' (SM)' )
                    else:
                        names.append( self.items.getName(i) )
                # Get detail row
                row = comIdToRow[comId]
                # New string
                if len(iIds) == 8 and 'SMG' in fileName:
                    string = 'Enables the remaining summons.'
                elif len(iIds) > 4:
                    string = 'Enables use of:\n' + ', '.join(names[:4]) + '\n' + ', '.join(names[4:])
                else:
                    string = 'Enables use of:\n' + ', '.join(names)
                self.detailInfo.patchTextString(string, row, 2)


class MAGIC_BS(MAGIC):
    def __init__(self, abilities, items, detailInfoData):
        super().__init__(abilities, items)
        self.detailInfo = detailInfoData.crowdFiles['DetailInfoMagicTable.btb']
        self.filesToCommand = { # A little complicated to read this from the data.....
            'AbilityWMG.btb': list(range(2001, 2008)),
            'AbilityBMG.btb': list(range(2009, 2016)),
            'AbilityTMG.btb': [2025, 2026, 2027, 2028, 2029, 2030, 2032],
            'AbilitySMG.btb': [2031, 2050, 2051, 2052, 2055],
            'AbilityWBM.btb': list(range(2064, 2068)),
            'AbilityBIS.btb': list(range(2074, 2081)),
            'AbilityWIZ.btb': [2081],
            'AbilityAST.btb': list(range(2089, 2096)),
        }

    def shuffleMagic(self):
        super().shuffleMagic()
    
        ## SHUFFLE SUMMONS
        summonerFile = self.abilities.crowdFiles['AbilitySMG.btb']
        abilId = summonerFile.readCol(1)
        itemId = summonerFile.readCol(2)
        cols = list(zip(abilId, itemId))
        groups = [ cols[i:i+2] + cols[i+8:i+10] for i in range(0, 8, 2) ]
        for group in groups:
            random.shuffle(group)
        newList = []
        for group in groups:
            newList += group[:2]
        for group in groups:
            newList += group[2:]
        abilId, itemId = zip(*newList)
        summonerFile.patchCol(abilId, 1)
        summonerFile.patchCol(itemId, 2)

        ## NEITHER SPELLCRAFT SEEMS TO WORK :(
        ## SHUFFLE SPELLCRAFT --- might need to shuffle items and/or names????
        # wizardFile = self.abilities.crowdFiles['AbilityPOS.btb']
        # abilId = wizardFile.readCol(1)
        # itemId = wizardFile.readCol(2)
        # c = list(zip(abilId, itemId))
        # random.shuffle(c)
        # abilId, itemId = list(zip(*c))
        # # wizardFile.patchCol(abilId, 1)
        # wizardFile.patchCol(itemId, 2)

        # wizardJob = self.jobFiles.crowdFiles['JobTable20.btb']
        # spellcraft = wizardJob.readCol(15)
        # spells = list(filter(lambda x: x > 0, spellcraft))
        # # random.shuffle(spells)
        # spells = spells[1:] + [spells[0]]
        # i = 0
        # while spells:
        #     if spellcraft[i] > 0:
        #         spellcraft[i] = spells.pop(0)
        #     i += 1

        # Update detailInfo
        detailComList = self.detailInfo.readCol(0)
        comIdToRow = {i:r for r,i in enumerate(detailComList)}
        for fileName, commandList in self.filesToCommand.items():
            fileObj = self.abilities.crowdFiles[fileName]
            levels = fileObj.readCol(0)
            itemIds = fileObj.readCol(2)
            tmp = list(zip(levels, itemIds))
            for i, comId in enumerate(commandList):
                _, ids = list(zip(*filter(lambda x: x[0] == i+1, tmp)))
                # Get names
                names = [self.items.getName(i) for i in ids]
                # Get detail row
                row = comIdToRow[comId]
                # New string
                if len(ids) == 8 and 'SMG' in fileName:
                    string = 'Enables the remaining summons.'
                elif len(ids) > 4:
                    string = 'Enables use of:\n' + ', '.join(names[:4]) + '\n' + ', '.join(names[4:])
                else:
                    string = 'Enables use of:\n' + ', '.join(names)
                self.detailInfo.patchTextString(string, row, 2)
