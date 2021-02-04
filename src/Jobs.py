import random

class JOBS:
    def __init__(self, jobFiles, abilities):
        self.abilities = abilities
        self.jobTable = jobFiles.crowdFiles['JobTable.btb']
        self.jobFiles = {}
        
    def zeroJP(self):
        for jobFile in self.jobFiles.values():
            jobFile.patchCol([0]*jobFile.count, 1) # TOTAL
            jobFile.patchCol([0]*jobFile.count, 2) # TO NEXT LEVEL

    # HP, MP, ....
    def shuffleAffinities(self):
        for col in range(4, 12):
            data = [jobFile.readCol(col) for jobFile in self.jobFiles.values()]
            random.shuffle(data)
            for di, jobFile in zip(data, self.jobFiles.values()):
                jobFile.patchCol(di, col)

    # Specialty skill
    def randomSpecialties(self):
        candidates = list(self.supportIDs)
        random.shuffle(candidates)
        for jobFile in self.jobFiles.values():
            value = candidates.pop()
            jobFile.patchValue(value, 0, 12)

    # PRINTOUTS!
    def print(self):
        print('==============')
        print('JOB AFFINITIES')
        print('==============')
        print('')
        print('')
        stats = {
            'HP': 4,
            'MP': 5,
            'STR': 6,
            'VIT': 7,
            'INT': 8,
            'MND': 9,
            'AGI': 10,
            'DEX': 11,
        }
        header = ' '*20
        for key in stats:
            header += key.rjust(6, ' ')
        print(header)
        for job, jobFile in self.jobFiles.items():
            line = job.rjust(20, ' ')
            for col in stats.values():
                stat = jobFile.readValue(0, col)
                line += f"{stat}%".rjust(6)
            print(line)
        print('')
        print('')
        print('')


class JOBS_BD(JOBS):
    def __init__(self, jobFiles, abilities):
        super().__init__(jobFiles, abilities)

        names = self.jobTable.readTextStringAll(2)
        index = self.jobTable.readCol(1)
        indexToName = {i:n for i,n in zip(index, names)}
        for i in range(24):
            idx = str(i).rjust(2, '0')
            fileName = f"JobTable{idx}.btb"
            name = indexToName[i]
            self.jobFiles[name] = jobFiles.crowdFiles[fileName]
        
        # LOAD ALL COMMAND AND SUPPORT FOR CANDIDATES
        # (NB: loading directly from their files would lead to some useless abilities, e.g. spellcrafts)
        allAbilities = set()
        for jobFile in self.jobFiles.values():
            allAbilities.add( jobFile.readValue(0, 12) ) # Specialty
            allAbilities.update(jobFile.readCol(13)) # Commands & Support
        allAbilities = sorted(filter(lambda x: x, allAbilities))
        self.commandIDs = list(filter(lambda x: x < 1000, allAbilities))
        self.supportIDs = list(filter(lambda x: x >= 1000, allAbilities))

    # Support abilities
    def shuffleSupport(self):
        candidates = list(self.supportIDs)
        random.shuffle(candidates)
        for jobFile in self.jobFiles.values():
            abilities = jobFile.readCol(13)
            for i in range(len(abilities)):
                if abilities[i] >= 1000:
                    abilities[i] = candidates.pop()
            jobFile.patchCol(abilities, 13)

    # Shuffle commands (non-mages)
    def shuffleCommands(self):
        candidates = list(self.commandIDs)
        random.shuffle(candidates)
        for jobFile in self.jobFiles.values():
            abilities = jobFile.readCol(13)
            for i in range(len(abilities)):
                if abilities[i] and abilities[i] < 1000:
                    abilities[i] = candidates.pop()
            jobFile.patchCol(abilities, 13)

    def printAbilities(self):
        print('=============')
        print('JOB ABILITIES')
        print('=============')
        print('')
        print('')
        for job, jobFile in self.jobFiles.items():
            print(job)
            print('-'*len(job))
            print('')
            specID = jobFile.readValue(0, 12)
            print('  Specialty:', self.abilities.getName(specID))
            print('')
            print('  Abilities:')
            abilIds = jobFile.readCol(13)
            jobComm = jobFile.readCol(16)
            for level, (abilId, jobComId) in enumerate(zip(abilIds, jobComm)):
                if abilId == 0:
                    # Magic/Summon level
                    print(f'  {level+1} '.rjust(7, ' '), self.abilities.getName(jobComId))
                elif abilId < 1000:
                    # Command
                    print(f'  {level+1} '.rjust(7, ' '), self.abilities.getName(abilId).ljust(20, ' '))
                else:
                    # Support
                    print(f'  {level+1} '.rjust(7, ' '), self.abilities.getName(abilId).ljust(20, ' '), f'{self.abilities.getSupCosts(abilId)} SP')
            print('')
            print('')
        print('')
        print('')
        
    def print(self):
        super().print()
        self.printAbilities()


class JOBS_BS(JOBS):
    def __init__(self, jobFiles, abilities):
        super().__init__(jobFiles, abilities)

        names = self.jobTable.readTextStringAll(2)
        for i, name in enumerate(names):
            idx = str(i).rjust(2, '0')
            fileName = f"JobTable{idx}.btb"
            self.jobFiles[name] = jobFiles.crowdFiles[fileName]
        
        # LOAD ALL COMMAND AND SUPPORT FOR CANDIDATES
        # (NB: loading directly from their files would lead to some useless abilities, e.g. spellcrafts)
        allAbilities = set()
        for jobFile in self.jobFiles.values():
            allAbilities.add( jobFile.readValue(0, 12) ) # Specialty
            allAbilities.update(jobFile.readCol(13)) # Commands & Support
        allAbilities = sorted(filter(lambda x: x, allAbilities))
        self.commandIDs = list(filter(lambda x: x < 20000, allAbilities))
        self.supportIDs = list(filter(lambda x: x >= 20000, allAbilities))

    # Equipment
    def shuffleAptitudes(self):
        for col in range(9, 25): # NB: cols 20, 23, and 25 are all 200 and probably unused
            data = self.jobTable.readCol(col)
            random.shuffle(data)
            self.jobTable.patchCol(data, col)

    # Support abilities
    def shuffleSupport(self):
        ## TEMPORARY FIX: ALSO MODIFIES JOBID COLUMN IN SUPABIL FILE
        ## THERE SEEMS TO BE NO NEED FOR THIS IN BS
        ## TODO: TEST TO SEE WHY IT EXISTS IN BD; ANY SIDE EFFECTS IN BD/BS
        jobIds = self.abilities.supAbilFile.readCol(2)
        candidates = list(self.supportIDs)
        random.shuffle(candidates)
        for jobFile in self.jobFiles.values():
            abilities = jobFile.readCol(13)
            for i in range(len(abilities)):
                if abilities[i] >= 20000:
                    row = self.abilities.getSupRow(abilities[i])
                    jobId = jobIds[row]
                    abilId = candidates.pop()
                    abilities[i] = abilId
                    row2 = self.abilities.getSupRow(abilities[i])
                    self.abilities.supAbilFile.patchValue(jobId, row2, 2)
            jobFile.patchCol(abilities, 13)

    # Shuffle commands (non-mages)
    def shuffleCommands(self):
        candidates = list(self.commandIDs)
        random.shuffle(candidates)
        for jobFile in self.jobFiles.values():
            abilities = jobFile.readCol(13)
            for i in range(len(abilities)):
                if abilities[i] and abilities[i] < 20000:
                    abilities[i] = candidates.pop()
            jobFile.patchCol(abilities, 13)

    def printAptitudes(self):
        print('=============')
        print('JOB APTITUDES')
        print('=============')
        print('')
        print('')
        equip = {
            'Swords': 9,
            'Axes': 10,
            'Spears': 11,
            'Rods': 12,
            'Staves': 13,
            'Daggers': 14,
            'Bows': 15,
            'Katana': 16,
            'Knuckles': 17,
            'G. Swds': 18,
            'Pistols': 19,
            'Shields': 24,
            'Helms': 21,
            'Armor': 22,
        }
        aptToGrade = {
            200: 'S',
            180: 'A',
            160: 'B',
            140: 'C',
            120: 'D',
            100: 'E',
        }
        header = ' '*20
        for key in equip:
            header += key.rjust(10, ' ')
        print(header)
        for row, (job, jobFile) in enumerate(self.jobFiles.items()):
            line = job.rjust(20, ' ')
            for col in equip.values():
                value = self.jobTable.readValue(row, col)
                line += aptToGrade[value].rjust(10, ' ')
            print(line)
        print('')
        print('')
        print('')

    def printAbilities(self):
        print('=============')
        print('JOB ABILITIES')
        print('=============')
        print('')
        print('')
        for job, jobFile in self.jobFiles.items():
            print(job)
            print('-'*len(job))
            print('')
            specID = jobFile.readValue(0, 12)
            print('  Specialty:', self.abilities.getName(specID))
            print('')
            print('  Abilities:')
            abilIds = jobFile.readCol(13)
            jobComm = jobFile.readCol(14)
            craftIds = jobFile.readCol(15)
            for level, (abilId, jobComId, craftId) in enumerate(zip(abilIds, jobComm, craftIds)):
                id = max(abilId, jobComId, craftId)
                if id < 3000:
                    print(f'  {level+1} '.rjust(7, ' '), self.abilities.getName(id))
                elif id < 20000:
                    print(f'  {level+1} '.rjust(7, ' '), self.abilities.getName(id))
                else:
                    print(f'  {level+1} '.rjust(7, ' '), self.abilities.getName(id).ljust(20, ' '), f'{self.abilities.getSupCosts(id)} SP')
            print('')
            print('')
        print('')
        print('')

        
        
    def print(self):
        self.printAptitudes()
        super().print()
        self.printAbilities()
