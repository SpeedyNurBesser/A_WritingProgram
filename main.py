import tkinter as tk
from tkinter import filedialog as fd
from tkinter import ttk
from tkinter import messagebox as mb
import re

AUTOSAVE_INTERVAL = 300 # in seconds
AUTOSAVE_INTERVAL = 300 * 1000

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
    def __init__(self, blockStyle=1, blockValue=1, fileLocation='test.md') -> None:

        self.fileLocation = fileLocation

        if blockStyle == 1:
            self.blockSytle = 1 # blockSytle 1 blocks * until the given amount of time (blockValue in minutes) has passed
            self.blockValue = blockValue # minutes
            self.progressValue = 0
        elif blockStyle == 2:
            self.blockSytle = 2 # blockSytle 2 blocks * until the given amount of words (blockValue) is written 
            self.blockValue = blockValue # words
            file = open(self.fileLocation, 'r')
            self.progressValue = -(len(re.sub(' +', ' ', file.read()).strip().split(" ")))
            # TODO: set value to the negative inverse of the amount of given words
            file.close()
        else:
            self.blockSytle = 0 # no blocking

        self.root = tk.Tk()
        self.root.title('A_WritingProgram - ' + self.fileLocation)

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

    def saveTextToFile(self):
        # gets the text from the textbox and saves it to the previously specified file
        file = open(self.fileLocation, 'w')
        file.write(self.textbox.get('1.0','end'))
        file.close()

    def loadTextToTBox(self):
        # loads the text from the previously specified file to the textbox
        file = open(self.fileLocation, 'r')
        self.textbox.insert('1.0', file.read())
        file.close()

    def autoSave(self):
        self.saveTextToFile()
        self.root.after(AUTOSAVE_INTERVAL, self.autoSave)

    def run(self):
        if self.blockSytle == 1: self.root.after(1000, self.updateTimeBar)
        elif self.blockSytle == 2: self.root.after(1000, self.updateWordBar)
        self.root.after(AUTOSAVE_INTERVAL, self.autoSave)
        self.root.mainloop()

    def updateTimeBar(self):
        self.progressValue += 1
        value = ((self.progressValue/60)/self.blockValue)
        self.progressBar.config(value= value)

        if value >= 1.0: self.enableQuit() # enable the quit button when goal is reached 

        self.root.after(1000, self.updateTimeBar) # recall method in a sec

    def updateWordBar(self):
        wordCount = len(re.sub(' +', ' ',self.textbox.get('1.0','end')).strip().split(" "))
        value = ((self.progressValue + wordCount)/self.blockValue)
        self.progressBar.config(value= value)

        if value >= 1.0: self.enableQuit() # enable the quit button when goal is reached 

        self.root.after(1000, self.updateWordBar) # recall method after a sec

    def SaveAndExit(self):
        self.saveTextToFile()
        self.root.destroy()

    def enableQuit(self):
        self.quitButton.config(state= 'normal')

#TODO: deactivate other monitors

class WriterStartup():
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title('A_WritingProgram')
        self.root.geometry('525x275')
        self.root.resizable(0, 0)

        # You need to select a file beforehand, create one, if you start anew: File Selection
        fileFrame = tk.Frame(self.root)

        self.fileLabel = tk.Label(fileFrame, text='You need to select a file beforehand; create one now, if you start anew: ')
        self.fileLabel.pack(pady=20, side='left')

        self.filename = ''

        selectFileButton = tk.Button(fileFrame, text='Browse', command= self.selectFile)
        selectFileButton.pack(pady=20, side='left')

        fileFrame.pack(pady=20)
        ###

        # Select your block frame
        blockFrame = tk.Frame(self.root)

        blockLabel = tk.Label(blockFrame, text='Block everything until')
        blockLabel.pack(side='left')

        self.blockValue = tk.Entry(blockFrame)
        self.blockValue.pack(side='left')

        blockFrame.pack()
        ###

        # CheckBoxes for blockStyle
        self.blockStyle = tk.StringVar()

        checkBoxFrame = tk.Frame(self.root)

        chechBoxTime = ttk.Radiobutton(checkBoxFrame, text='minutes have passed.', value=1, variable=self.blockStyle)
        chechBoxTime.pack(fill='x')

        checkBoxWord = ttk.Radiobutton(checkBoxFrame, text='words are written.', value=2, variable=self.blockStyle)
        checkBoxWord.pack(fill='x')

        checkBoxNone = ttk.Radiobutton(checkBoxFrame, text='times nothing has happened. (No Block)', value=0, variable=self.blockStyle)
        checkBoxNone.pack(fill='x')

        self.blockStyle.set(1)

        checkBoxFrame.pack()
        ###

        startButton = tk.Button(self.root, text='Start', command= self.startWriter)
        startButton.pack(pady=20)

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

    def startWriter(self):
        if self.filename != '':
            writer = Writer(fileLocation= self.filename, blockStyle= int(self.blockStyle.get()), blockValue= int(self.blockValue.get()))
            writer.run()
            self.root.destroy()
        else:
            self.fileLabel.config(text='You need to select a file!', fg='#ff3333')
        

if __name__ == '__main__':
    #Writer(blockStyle=1).run()
    WriterStartup()
    #root = tk.Tk()

    #root.geometry('500x300')
    

    #text = BetterText(root, wrap='word', font=('Times New Roman', 16), width=90)
    #text.pack()

    #root.mainloop()