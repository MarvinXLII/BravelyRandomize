import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from release import RELEASE
import hjson
import random
import os
import shutil
import hashlib
import sys
sys.path.append('src')
from Utilities import get_filename
from Classes import ROM

MAIN_TITLE = f"Bravely Randomize v{RELEASE}"

# Source: https://www.daniweb.com/programming/software-development/code/484591/a-tooltip-class-for-tkinter
class CreateToolTip(object):
    '''
    create a tooltip for a given widget
    '''
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)

    def enter(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                      background='white', relief='solid', borderwidth=1,
                      wraplength=200,
                      font=("times", "12", "normal"),
                      padx=4, pady=6,
        )
        label.pack(ipadx=1)

    def close(self, event=None):
        if self.tw:
            self.tw.destroy()


class GuiApplication:
    def __init__(self, settings=None):
        self.master = tk.Tk()
        self.master.geometry('680x400')
        self.master.title(MAIN_TITLE)
        self.initialize_gui()
        self.initialize_settings(settings)
        self.master.mainloop()


    def initialize_gui(self):

        self.warnings = []
        self.togglers = []
        self.settings = {}
        self.settings['release'] = tk.StringVar()

        with open(get_filename('./json/sha.json'), 'r') as file:
            self.sha256 = hjson.loads(file.read())

        with open(get_filename('./json/gui.json'), 'r') as file:
            fields = hjson.loads(file.read())

        labelfonts = ('Helvetica', 14, 'bold')
        lf = tk.LabelFrame(self.master, text='ROM Folder', font=labelfonts)
        lf.grid(row=0, columnspan=2, sticky='nsew', padx=5, pady=5, ipadx=5, ipady=5)

        self.settings['rom'] = tk.StringVar()
        self.settings['rom'].set('')

        pathToPak = tk.Entry(lf, textvariable=self.settings['rom'], width=65, state='readonly')
        pathToPak.grid(row=0, column=0, columnspan=2, padx=(10,0), pady=3)

        pathLabel = tk.Label(lf, text='Path to "romfs" folder')
        pathLabel.grid(row=1, column=0, sticky='w', padx=5, pady=2)

        pathButton = tk.Button(lf, text='Browse ...', command=self.getRomPath, width=20) # needs command..
        pathButton.grid(row=1, column=1, sticky='e', padx=5, pady=2)

        lf = tk.LabelFrame(self.master, text="Seed", font=labelfonts)
        lf.grid(row=0, column=2, columnspan=2, sticky='nsew', padx=5, pady=5, ipadx=5, ipady=5)
        self.settings['seed'] = tk.IntVar()
        self.randomSeed()

        box = tk.Spinbox(lf, from_=0, to=1e8, width=9, textvariable=self.settings['seed'])
        box.grid(row=2, column=0, sticky='e', padx=60)

        seedBtn = tk.Button(lf, text='Random Seed', command=self.randomSeed, width=12, height=1)
        seedBtn.grid(row=3, column=0, columnspan=1, sticky='we', padx=30, ipadx=30)

        self.randomizeBtn = tk.Button(lf, text='Randomize', command=self.randomize, height=1)
        self.randomizeBtn.grid(row=4, column=0, columnspan=1, sticky='we', padx=30, ipadx=30)

        # Tabs setup
        tabControl = ttk.Notebook(self.master)
        tabNames = list(fields.keys())
        tabs = {name: ttk.Frame(tabControl) for name in tabNames}
        for name, tab in tabs.items():
            tabControl.add(tab, text=name)
        tabControl.grid(row=2, column=0, columnspan=20, sticky='news')

        # Tab label
        for name, tab in tabs.items():
            labelDict = fields[name]
            for i, (key, value) in enumerate(labelDict.items()):
                row = i//2
                column = i%2
                # Setup LabelFrame
                lf = tk.LabelFrame(tab, text=key, font=labelfonts)
                lf.grid(row=row, column=column, padx=10, pady=5, ipadx=30, ipady=5, sticky='news')
                # Loop over buttons
                # -- maybe do this in a separate function that returns the button?
                # -- then apply its grid here
                row = 0
                for vj in value:
                    name = vj['name']

                    if vj['type'] == 'checkbutton':
                        self.settings[name] = tk.BooleanVar()
                        buttons = []
                        toggleFunction = self.toggler(buttons, name)
                        button = ttk.Checkbutton(lf, text=vj['label'], variable=self.settings[name], command=toggleFunction)
                        button.grid(row=row, padx=10, sticky='we')
                        self.buildToolTip(button, vj)
                        row += 1
                        if 'indent' in vj:
                            self.togglers.append(toggleFunction)
                            for vk in vj['indent']:
                                self.settings[vk['name']] = tk.BooleanVar()
                                button = ttk.Checkbutton(lf, text=vk['label'], variable=self.settings[vk['name']], state=tk.DISABLED)
                                button.grid(row=row, padx=30, sticky='w')
                                self.buildToolTip(button, vk)
                                buttons.append((self.settings[vk['name']], button))
                                row += 1

                    elif vj['type'] == 'spinbox':
                        text = f"{vj['label']}:".ljust(20, ' ')
                        ttk.Label(lf, text=text).grid(row=row, column=0, padx=10, sticky='w')
                        spinbox = vj['spinbox']
                        self.settings[name] = tk.IntVar()
                        self.settings[name].set(spinbox['default'])
                        box = tk.Spinbox(lf, from_=spinbox['min'], to=spinbox['max'], width=3, textvariable=self.settings[name], state='readonly')
                        box.grid(row=row, column=2, padx=10, sticky='we')
                        self.buildToolTip(box, vj)
                        row += 1

                    elif vj['type'] == 'radiobutton':
                        self.settings[name] = tk.BooleanVar()
                        buttons = []
                        toggleFunction = self.toggler(buttons, name)
                        button = ttk.Checkbutton(lf, text=vj['label'], variable=self.settings[name], command=toggleFunction)
                        button.grid(row=row, padx=10, sticky='we')
                        self.buildToolTip(button, vj)
                        self.togglers.append(toggleFunction)
                        row += 1
                        keyoption = name+'-option'
                        self.settings[keyoption] = tk.StringVar()
                        self.settings[keyoption].set(None)
                        for ri in vj['radio']:
                            radio = tk.Radiobutton(lf, text=ri['label'], variable=self.settings[keyoption], value=ri['value'], padx=15, state=tk.DISABLED)
                            radio.grid(row=row, padx=14, sticky='w')
                            self.buildToolTip(radio, ri)
                            buttons.append((self.settings[keyoption], radio))
                            row += 1

        # For warnings/text at the bottom
        self.canvas = tk.Canvas()
        self.canvas.grid(row=6, column=0, columnspan=20, pady=10)

    def checkPath(self, path):
        # Ensure romfs directory
        dirName = os.path.basename(os.path.normpath(path))
        if dirName == 'romfs' or dirName == 'RomFS':
            return True
        return False

    def checkROM(self, path):
        # Check all files are correct
        for name, sha256 in self.sha256.items():
            fileName = os.path.join(path, name)
            if not os.path.isfile(fileName):
                return False
            with open(fileName, 'rb') as file:
                data = bytearray(file.read())
            checksum = hashlib.sha256(data)
            if checksum.hexdigest() != sha256:
                return False
        return True

    def getRomPath(self, path=None):
        self.clearBottomLabels()
        if not path:
            path = filedialog.askdirectory()
        # Exited askdirectory
        if path == ():
            return
        # Check directory name
        if not self.checkPath(path):
            self.settings['rom'].set('')
            self.bottomLabel('Mrgrgrgrgr!', 'red', 0)
            self.bottomLabel('Selected folder must be "romfs" or "RomFS".', 'red', 1)
            return
        # SHA256 checks
        if not self.checkROM(path):
            self.settings['rom'].set('')
            self.bottomLabel('Mrgrgrgrgr!', 'red', 0)
            self.bottomLabel('Must use unmodified files from a North American release.', 'red', 1)
            return
        # Set path to valid rom
        self.settings['rom'].set(path)

    def toggler(self, lst, key):
        def f():
            if self.settings[key].get():
                try: lst[0][1].select()
                except: pass
                for vi, bi in lst:
                    bi.config(state=tk.NORMAL)
            else:
                for vi, bi in lst:
                    if type(vi.get()) == bool: vi.set(False)
                    if type(vi.get()) == str: vi.set(None)
                    bi.config(state=tk.DISABLED)
        return f

    def buildToolTip(self, button, field):
        if 'help' in field:
            CreateToolTip(button, field['help'])

    def turnBoolsOff(self):
        for si in self.settings.values():
            if type(si.get()) == bool:
                si.set(False)
            
    def initialize_settings(self, settings):
        self.settings['release'].set(RELEASE)
        if settings is None:
            self.turnBoolsOff()
            return
        for key, value in settings.items():
            if key == 'release': continue
            if key not in self.settings: continue
            self.settings[key].set(value)
        for toggle in self.togglers:
            toggle()
        self.getRomPath(path=self.settings['rom'].get())

    def bottomLabel(self, text, fg, row):
        L = tk.Label(self.canvas, text=text, fg=fg)
        L.grid(row=row, columnspan=20)
        self.warnings.append(L)
        self.master.update()

    def clearBottomLabels(self):
        while self.warnings != []:
            warning = self.warnings.pop()
            warning.destroy()
        self.master.update()
        
    def randomSeed(self):
        self.settings['seed'].set(random.randint(0, 1e8))

    def randomize(self, settings=None):
        if settings is None:
            settings = { key: value.get() for key, value in self.settings.items() }
        self.clearBottomLabels()
        self.bottomLabel('Randomizing....', 'blue', 0)
        try:
            randomize(settings)
            self.clearBottomLabels()
            self.bottomLabel('Randomizing...done! Good luck!', 'blue', 0)
        except:
            self.clearBottomLabels()
            self.bottomLabel('Mrgrgrgrgr! Randomizing failed.', 'red', 0)
            self.bottomLabel('Randomizing failed.', 'red', 1)


def randomize(settings):

    #########
    # SETUP #
    #########

    if sys.executable.endswith('BravelyRandomize.exe'):
        pwd = os.path.dirname(sys.executable)
    else:
        pwd = os.getcwd()

    outdir = os.path.join(pwd, f"seed_{settings['seed']}")
    if os.path.isdir(outdir):
        shutil.rmtree(outdir)
    os.mkdir(outdir)

    #############
    # Randomize #
    #############

    rom = ROM(settings)
    rom.randomize()
    rom.qualityOfLife()
    rom.printLogs(outdir)
    rom.write(outdir)

    #################
    # Dump Settings #
    #################

    with open(f"{outdir}/settings.json", 'w') as file:
        hjson.dump(settings, file)


if __name__ == '__main__':
    if len(sys.argv) > 2:
        print('Usage: python gui.py <settings.json>')
    elif len(sys.argv) == 2:
        with open(sys.argv[1], 'r') as file:
            settings = hjson.load(file)
        GuiApplication(settings)
    else:
        GuiApplication()
