import tkinter as tk
from tkinter import filedialog as fd
from tkinter import ttk
import re
import os
import json
import webbrowser

SETTINGS_FILENAME = 'settings.json' # if i for some reason happen to want to call the file "config" in the future

class BetterText(tk.Text):
    def __init__(self, parent, *args, **kwargs):
        tk.Text.__init__(self, parent, *args, **kwargs)

        # Undo/Redo
        self.changes = [''] # changes saves a copy of every altered version of your document
        self.steps = int() # steps saves the current step in undo time
        # binding the apropriate Controls to undo and redo
        self.bind('<Control-z>', self.undo)
        self.bind('<Control-y>', self.redo)
        self.bind('<Key>', self.add_changes) # every time a button is pressed, i.e. the text is altered, a new copy of text is saved in changes


        # Markdown shortcuts
        self.bind('<Control-i>', self.italicText) # italizes text 
        self.bind('<Control-b>', self.boldText) # bold(s)? text -> prints text in bold
        self.bind('<Control-u>', self.underlinedText) # underlines text

        # Word Removal:
        # Delete word to the left of cursor (Ctrl + BackSpace)
        # Delete word to the right of cursor (Ctrl + Delete)
        self.bind('<Control-BackSpace>', self.wordRemovalLeft)
        self.bind('<Control-Delete>', self.wordRemovalRight)

    # Word Removal
    def wordRemovalLeft(self, event=None):
        cursorPos = self.index(tk.INSERT)
        self.delete(f'{cursorPos} - 1 chars wordstart', cursorPos)
        self.insert(cursorPos, ' ') # inserts a space, as the regular backSpace still triggers

    def wordRemovalRight(self, event=None):
        cursorPos = self.index(tk.INSERT)
        self.delete(cursorPos, f"{self.index(f'{cursorPos} wordend')} - 1 chars") # removes one char, as the regular del key still fires

    # Undo/Redo
    def undo(self, event=None):
        if self.steps != 0:
            self.steps -= 1
            self.delete('1.0','end')
            self.insert('end', self.changes[self.steps])

    def redo(self, event=None):
        if self.steps < len(self.changes):
            self.delete('1.0','end')
            self.insert('end', self.changes[self.steps])
            self.steps += 1

    def add_changes(self, event=None):
        if self.get('1.0','end') != self.changes[-1]:
            self.changes.append(self.get('1.0','end'))
            self.steps += 1

    # markdown shortcuts
    def postItalicText(self, event=None):
        # delete last typed character (tab) (for explanation see italicText method)
        cursorPos = self.index(tk.INSERT)
        self.delete(f'{cursorPos} - 1 chars', cursorPos)

    def italicText(self, event=None): # *italic*
        # italize text
        self.markText(SYNTAX_FRONT='*', SYNTAX_BACK='*')
        self.after(1, self.postItalicText)
        # Ctrl+I is interpreted as Tab; to circumvent this a function is called 1 ms after the text has been marked that instantly deletes the tab again; this only works, because the Tab is always only send after the function (-> method) call
        
    def boldText(self, event=None): # **bold**
        self.markText(SYNTAX_FRONT='**', SYNTAX_BACK='**')

    def underlinedText(self, event=None): # <u>underline</u>
        self.markText(SYNTAX_FRONT='<u>', SYNTAX_BACK='</u>')

    def isMarked(self, SYNTAX_FRONT, SYNTAX_BACK):
        selectionRange = self.tag_ranges('sel')

        foregoingTextPos = (f'{selectionRange[0]} - {len(SYNTAX_FRONT)} chars', selectionRange[0])
        foregoingText = self.get(foregoingTextPos[0], foregoingTextPos[1])

        firstCharPos = (selectionRange[0], f'{selectionRange[0]} + {len(SYNTAX_FRONT)} chars')
        firstChars = self.get(firstCharPos[0], firstCharPos[1])

        followingTextPos = (selectionRange[1], f'{selectionRange[1]} + {len(SYNTAX_BACK)} chars')
        followingText = self.get(followingTextPos[0], followingTextPos[1])

        lastCharPos = (f'{selectionRange[1]} - {len(SYNTAX_BACK)} chars', selectionRange[1])
        lastChars = self.get(lastCharPos[0], lastCharPos[1])

        if SYNTAX_FRONT == foregoingText and SYNTAX_BACK == followingText:
            return (True, foregoingTextPos, followingTextPos)
        
        elif SYNTAX_FRONT == firstChars and SYNTAX_BACK == lastChars:
            return (True, firstCharPos, lastCharPos)

        else:
            return (False, None)

    def markText(self, SYNTAX_FRONT='*', SYNTAX_BACK='*'):
        # marks text using a given syntax (markdown syntax (*italic*))
        # if any text is selected, toggle marks on selected text
        # else insert SYNTAX at textCursor

        if self.tag_ranges('sel'): # if any text is selected
            isMarked = self.isMarked(SYNTAX_FRONT, SYNTAX_BACK)
            selection = self.selection_get() # store the selected text

            if isMarked[0] == True: # check if text is already marked
                # syntax found -> delete syntax
                # note: deletes back-syntax before front-syntax; for otherwise the positions would change
                self.delete(isMarked[2][0], isMarked[2][1])
                self.delete(isMarked[1][0], isMarked[1][1])
            else: # no syntax found -> add syntax
                selection = f'{SYNTAX_FRONT}{selection}{SYNTAX_BACK}' # add Syntax to stored selection
                self.insert(self.tag_ranges('sel')[1], selection)  # insert new stored selection right after the real selection
                self.delete(self.tag_ranges('sel')[0], self.tag_ranges('sel')[1]) # delete original selection
            
            # unselects everything
            self.tag_remove('sel', '1.0', 'end')

        else:
            cursorPos = self.index(tk.INSERT)
            self.insert(cursorPos, f'{SYNTAX_FRONT}{SYNTAX_BACK}')
            self.mark_set('insert', f'{self.index(tk.INSERT)} - {len(SYNTAX_BACK)} chars') # applies new position (between front and back Syntax) to cursor

class Writer(): # a tkinter window for distraction-free writing
    def __init__(self, blockStyle=1, blockValue=1, fileLocation='test.md', autosaveInterval=300, displayHeader=True) -> None:

        self.fileLocation = fileLocation

        if blockStyle == 1:
            self.blockSytle = 1 # blockSytle 1 blocks * until the given amount of time (blockValue in minutes) has passed
            self.blockValue = blockValue # minutes
            self.progressValue = 0
        elif blockStyle == 2:
            self.blockSytle = 2 # blockSytle 2 blocks * until the given amount of words (blockValue) is written 
            self.blockValue = blockValue # words

            # sets the progress value as (the amount of words of the unedited file (old words))
            # every time the progressBar is updated it's current value is calculated as the here defined the current number of words (i.e. newly written words and old words) - progressValue
            # as we only want the newly written words to count as progress and we can't really filter, if a word is new or old, to get the number of new words we just subtract the number of old words from the total
            # if we otherwise open a file with already 1000 words inside, and set our blockValue as 1000 the goal would instantly be reached
            file = open(self.fileLocation, 'r', encoding='utf-8')
            self.progressValue = len(re.sub(' +', ' ', file.read()).split(" "))
            file.close()
        else:
            self.blockSytle = 0 # no blocking

        self.root = tk.Tk()
        self.root.title('A_WritingProgram - ' + self.fileLocation)

        self.autosaveInterval = autosaveInterval * 1000

        if displayHeader:
            self.titleLabel = tk.Label(self.root, text='A_WritingProgram', font='Calibri, 24')
            self.titleLabel.pack(pady=(50, 0))

        # puts the root window into a distraction-free state, if the blocking is enabled
        if self.blockSytle != 0:
            def on_closing(): pass # a function handling the closing of the window; as the function just passes the window is made unclosable
            self.root.protocol('WM_DELETE_WINDOW', on_closing) # makes the window unclosable
            self.root.attributes('-fullscreen', True) # puts the window instantly in fullscreen mode
            self.root.attributes('-toolwindow', 1) # removes the minimize and maximize buttons
            self.root.attributes('-topmost', True) # keeps the window always on top
            self.root.resizable(0,0) # disables the ability to resize the window

        # either displays a progressBar and a disabled quit button or a weird useless label
        if self.blockSytle != 0:
            # displays the user's writing progress (time passed / words typed) in percentage points
            self.progressBar = ttk.Progressbar(self.root, orient='horizontal', length=300, mode='determinate', maximum=1)
            s = ttk.Style(self.progressBar)
            s.theme_use('alt')
            self.progressBar.pack(padx=20, pady=(25, 5))

            # adds QuitButton
            self.quitButton = tk.Button(self.root, text='Save & Exit', command=self.SaveAndExit, state='disabled', border=0)
            self.quitButton.pack(padx=20, pady=(0, 50))
        else: 
            self.label = tk.Label(self.root, text="So you are the kind of person to use a distraction-free writing software without using the features that make the software distraction-free? Interesting decision...\n...\n...\n...\n Just out of interest, you do realize that without the distraction-free features this piece of software is just barely, if at all, better than the MS Editor, do you?").pack(padx=20, pady=20)

        # the input box for your text, quite literally the most obvious (& important) part
        self.textbox = BetterText(self.root, wrap='word', font=('Times New Roman', 16), width=90)
        self.textbox.pack(fill=tk.Y, expand=True)
        self.loadTextToTBox()

        self.run()

    def saveTextToFile(self):
        # gets the text from the textbox and saves it to the previously specified file
        file = open(self.fileLocation, 'w', encoding='utf-8')
        file.write(self.textbox.get('1.0','end'))
        file.close()

    def loadTextToTBox(self):
        # loads the text from the previously specified file to the textbox
        file = open(self.fileLocation, 'r', encoding='utf-8')
        self.textbox.insert('1.0', file.read())
        file.close()

    def autoSave(self):
        print('Trying to autosave...')
        try:
            self.saveTextToFile()
        except:
            print('Autosave failed.')
        else:
            print('Autosave finished.')
        finally:
            self.root.after(self.autosaveInterval, self.autoSave)

    def run(self):
        if self.blockSytle == 1: self.root.after(1000, self.updateTimeBar)
        elif self.blockSytle == 2: self.root.after(1000, self.updateWordBar)
        self.root.after(self.autosaveInterval, self.autoSave)
        self.root.mainloop()

    def updateTimeBar(self):
        self.progressValue += 1
        value = ((self.progressValue/60)/self.blockValue)
        self.progressBar.config(value= value)

        if value >= 1.0: self.enableQuit() # enable the quit button when goal is reached 

        self.root.after(1000, self.updateTimeBar) # recall method in a sec

    def updateWordBar(self):
        wordCount = len(re.sub(' +', ' ',self.textbox.get('1.0','end')).strip().split(" "))
        value = ((wordCount - self.progressValue)/self.blockValue)
        self.progressBar.config(value= value)

        if value >= 1.0: self.enableQuit() # enable the quit button when goal is reached 

        self.root.after(1000, self.updateWordBar) # recall method after a sec

    def SaveAndExit(self):
        self.saveTextToFile()
        self.root.destroy()

    def enableQuit(self):
        self.quitButton.config(state= 'normal')

class WriterConfigurator():
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title('A_WritingProgram')
        self.root.geometry('525x275')
        self.root.resizable(0, 0)

        self.tabControl = ttk.Notebook(self.root)
        self.mainTab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.mainTab, text='Main')
        self.settingsTab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.settingsTab, text='Settings')
        self.aboutTab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.aboutTab, text='About')
        self.tabControl.pack(expand = 1, fill ="both") 

        # Main Tab
        fileFrame = tk.Frame(self.mainTab)

        self.fileLabel = tk.Label(fileFrame, text='You need to select a file beforehand; create one now, if you start anew: ')
        self.fileLabel.pack(pady=20, side='left')

        self.filename = ''

        selectFileButton = tk.Button(fileFrame, text='Browse', command= self.selectFile)
        selectFileButton.pack(pady=20, side='left')

        fileFrame.pack()
        ###

        # set blockValue
        blockFrame = tk.Frame(self.mainTab)

        blockLabel = tk.Label(blockFrame, text='Block everything until')
        blockLabel.pack(side='left')

        self.blockValue = tk.Entry(blockFrame)
        self.blockValue.pack(side='left')

        blockFrame.pack()
        ###

        # CheckBoxes for blockStyle
        self.blockStyle = tk.StringVar()

        checkBoxFrame = tk.Frame(self.mainTab)

        chechBoxTime = ttk.Radiobutton(checkBoxFrame, text='minutes have passed.', value=1, variable=self.blockStyle)
        chechBoxTime.pack(fill='x')

        checkBoxWord = ttk.Radiobutton(checkBoxFrame, text='words are written.', value=2, variable=self.blockStyle)
        checkBoxWord.pack(fill='x')

        checkBoxNone = ttk.Radiobutton(checkBoxFrame, text='times nothing has happened. (No Block)', value=0, variable=self.blockStyle)
        checkBoxNone.pack(fill='x')

        self.blockStyle.set(1)

        checkBoxFrame.pack()

        startButton = tk.Button(self.mainTab, text='Start', command= self.startWriter)
        startButton.pack(pady=20)

        ######
        # Settings Tab

        settingsNote = tk.Label(self.settingsTab, text="You can't change any settings while writing (that would be a distraction).") 
        settingsNote.pack(pady=20)

        settingsFrame = tk.Frame(self.settingsTab)

        autosaveFrame = tk.Frame(settingsFrame)
        autosaveLabel = tk.Label(autosaveFrame, text='Interval for Autosaves:')
        autosaveLabel.pack(side=tk.LEFT)
        self.autosaveIntervalEntry = tk.Entry(autosaveFrame)
        self.autosaveIntervalEntry.pack(side=tk.LEFT)
        autosaveUnit = tk.Label(autosaveFrame, text='seconds')
        autosaveUnit.pack(side=tk.LEFT)
        autosaveFrame.pack(fill='x')

        self.headerVar = tk.IntVar()
        self.headerCheckbox = ttk.Checkbutton(settingsFrame, text='Show "A_WritingProgram" header', variable=self.headerVar)
        self.headerCheckbox.pack(pady=10, fill='x')

        settingsFrame.pack()

        self.errorLabel = tk.Label(self.settingsTab, fg='#ff3333', text='')
        self.errorLabel.pack(pady=20)

        self.loadSettingsFromFile()


        buttonFrame = tk.Frame(self.settingsTab)

        applySettingsButton = tk.Button(buttonFrame, text='Apply', command=self.applySettings)
        applySettingsButton.pack(side=tk.LEFT, padx=25)

        saveSettingsButton = tk.Button(buttonFrame, text='Apply & Save', command=self.applyAndSaveSettings)
        saveSettingsButton.pack(side=tk.LEFT, padx=25)

        buttonFrame.pack()

        ##############
        # About Tab

        aboutLabel1 = tk.Label(self.aboutTab, text="A_WritingProgram is a portable, distraction-free software for writing (i.e. a writing program).")
        aboutLabel1.pack(padx=10, pady=20,anchor='w')

        aboutLabel2 = tk.Label(self.aboutTab, text="I put it together on a couple of free afternoons (that sometimes dragged on till 4AM).")
        aboutLabel2.pack(padx=10, pady=0,anchor='w')

        aboutLabel3 = tk.Label(self.aboutTab, text="Why? Just because. I kinda like doing stuff. If you find this useful, use it.")
        aboutLabel3.pack(padx=10, pady=0,anchor='w')

        aboutLabel4 = tk.Label(self.aboutTab, text="Anyway, bye...\n- Ole370")
        aboutLabel4.pack(padx=10, pady=10,anchor='w')

        aboutSeparator = ttk.Separator(self.aboutTab, orient='horizontal')
        aboutSeparator.pack(fill='x')

        projectLink = tk.Label(self.aboutTab, text="GitHub Project", fg="#3066DD", cursor="hand2")
        projectLink.pack(padx=10, pady=10,anchor='w')
        projectLink.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/SpeedyNurBesser/A_WritingProgram"))


        aboutLabel5 = tk.Label(self.aboutTab, text="(P.S. You can star the GitHub Project if you like.)")
        aboutLabel5.pack(padx=10, pady=10,anchor='w')


        self.root.mainloop()
    
    def selectFile(self):
        filetypes = (
            ('Markdown files', '*.md'),
            ('Text files', '*.txt *.md'),
            ('All files', '*.*')
            )
        
        self.filename = fd.askopenfile(
            title= 'Select a file',
            initialdir= '/',
            filetypes= filetypes
        ).name

        self.fileLabel.config(text=self.filename, fg='#000000')

    def inputIsValid(self):
        if self.filename == '':
            self.fileLabel.config(text='You need to select a file!', fg='#ff3333')
            return False
        
        blockValue  = self.blockValue.get()

        if blockValue == '':
            self.fileLabel.config(text='''"Block everything until..." can't be empty!''', fg='#ff3333')
            return False
        
        try:
            blockValue = int(blockValue)
        except:
            self.fileLabel.config(text='''"Block everything until..." must be an integer!''', fg='#ff3333')
            return False
        
        if blockValue <= 0:
            self.fileLabel.config(text='''"Block everything until..." can't be zero or lower!''', fg='#ff3333')
            return False
        
        return True

    def startWriter(self):
        # Everyone loves GuardClauses!
        if not self.inputIsValid():
            return
        
        writer = Writer(
            fileLocation= self.filename,
            blockStyle= int(self.blockStyle.get()),
            blockValue= int(self.blockValue.get()),
            autosaveInterval= self.autosaveInterval,
            displayHeader= self.displayHeader
            )
    
    def setDefaultSettings(self):
        # defaultSettings
        self.headerVar.set(1)
        self.autosaveIntervalEntry.delete(0, 'end')
        self.autosaveIntervalEntry.insert(1, '300')
        self.applySettings()

    def loadSettingsFromFile(self):
        #directory = os.path.dirname(os.path.abspath(__file__))
        #directory = directory + '\settings.json'

        # I'm a bit more caucious than usually
        if os.path.exists(SETTINGS_FILENAME):
            try:
                file = open(SETTINGS_FILENAME, 'r')
            except:
                print(f'Could not open "{SETTINGS_FILENAME}"; loading default settings.')
                self.setDefaultSettings()
                return None

            try:
                settings = json.load(file)
            except:
                print(f'Could not load "{SETTINGS_FILENAME}"; loading default settings instead.')
                self.setDefaultSettings()
            else:
                try:
                    self.autosaveIntervalEntry.insert(1, settings["autosaveInterval"])
                    if settings["displayHeader"]:
                        self.headerVar.set(1)
                    else:
                        self.headerVar.set(0)
                    self.applySettings()
                except:
                    print(f'"{SETTINGS_FILENAME}" seems to be not initialized correctly; loading default settings instead.')
                    self.setDefaultSettings()
            finally:
                    file.close()
     
        else:
            print('No settings found, loading default settings.')
            self.setDefaultSettings()

    def settingsAreValid(self):
        # a checkbutton can't be un-valid
        # a entry, however, can be
        value = self.autosaveIntervalEntry.get()

        if value == '':
            self.errorLabel.config(text='''"Interval for Autosaves..." can't be empty!''', fg='#ff3333')
            return False
        
        try:
            value = int(value)
        except:
            self.errorLabel.config(text='''"Interval for Autosaves..." must be an integer!''', fg='#ff3333')
            return False

        
        if value <= 0:
            self.errorLabel.config(text='''"Interval for Autosaves..." can't be zero or lower!''', fg='#ff3333')
            return False
        
        self.errorLabel.config(text='', fg='#ff3333')
        return True

    def writeSettingsToFile(self):
        if not self.settingsAreValid():
            return

        try:
            file = open(SETTINGS_FILENAME, "w")
        except:
            self.errorLabel.config(text=f'Could not open {SETTINGS_FILENAME}!', fg='#ff3333')
            return
        else:
            settingDict = {"displayHeader": bool(self.headerVar.get()), "autosaveInterval": int(self.autosaveIntervalEntry.get())}
            settingDict = json.dumps(settingDict)

            try:
                file.write(settingDict)
            except:
                self.errorLabel.config(text=f'Could not write to {SETTINGS_FILENAME}!', fg='#ff3333')
                return
        finally:
            file.close()

    def applySettings(self):
        # sets the real settings var that will be parsed as parameters to equal the user input
        if not self.settingsAreValid():
            return
        
        self.autosaveInterval = int(self.autosaveIntervalEntry.get())
        self.displayHeader = bool(self.headerVar.get())

    def applyAndSaveSettings(self):
        self.writeSettingsToFile()
        self.applySettings()

if __name__ == '__main__':
    WriterConfigurator()

    #TODO: possible future settings:
    # - dark mode (i like #272D2D)
    # - initial directory for file search
    # - set progressbar style ('winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative')
    # - set font
    # - typical writing features (hemingway mode, typewriter mode, etc.) (maybe that's not distraction-free / bloads the app?)

    #TODO: deactivate other monitors on multi monitor setups