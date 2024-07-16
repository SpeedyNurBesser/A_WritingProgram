import tkinter as tk
from tkinter import filedialog as fd
from tkinter import ttk
from tkinter import messagebox as mb
import re

AUTOSAVE_INTERVAL = 300 # in seconds

class BetterText(tk.Text):
    def __init__(self, parent, *args, **kwargs):
        tk.Text.__init__(self, parent, *args, **kwargs)


        # Undo/Redo
        # changes saves a copy of every altered version of your document
        self.changes = ['']
        # steps saves the current step in undo time
        self.steps = int()
        # binding the apropriate Controls to undo and redo
        self.bind('<Control-z>', self.undo)
        self.bind('<Control-y>', self.redo)
        # adding to changes list, when the text is altered, i.e. a button is pressed 
        self.bind('<Key>', self.add_changes)

        # Markdown shortcuts
        self.bind('<Control-i>', self.italicText) # italizes text 
        self.bind('<Control-b>', self.boldText) # bold(s)? text
        self.bind('<Control-u>', self.underlinedText) # underlines text
        self.bind('<Control-h>', self.highlightText) # highlight text

#TODO: add markdown shortcut stuff (Ctrl+I -> *word*)
#TODO: add Ctrl + Backspace entire word removal.

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

    def postItalicText(self, event=None):
        # delete last typed character (tab)
        cursorPos = self.index(tk.INSERT)
        self.delete(f'{cursorPos} - 1 chars', cursorPos)

    def italicText(self, event=None): # *italic*
        # italize text
        self.markText(SYNTAX_FRONT='*', SYNTAX_BACK='*')
        self.after(1, self.postItalicText)
        # Ctrl+I is interpreted as Tab; to circumvent this a function is called 1 ms after the text has been marked that instantly deletes the tab again; this only works, because the Tab is always send after the function call
        
    def boldText(self, event=None): # **bold**
        self.markText(SYNTAX_FRONT='**', SYNTAX_BACK='**')

    def underlinedText(self, event=None): # <u>underline</u>
        self.markText(SYNTAX_FRONT='<u>', SYNTAX_BACK='</u>')

    def highlightText(self, event=None): # ==highlight==
        self.markText(SYNTAX_FRONT='==', SYNTAX_BACK='==')

    def markText(self, SYNTAX_FRONT='*', SYNTAX_BACK='*'):
        if self.tag_ranges('sel'):
            selection = self.selection_get()
            selection = f'{SYNTAX_FRONT}{selection}{SYNTAX_BACK}'
            self.insert(self.tag_ranges('sel')[1], selection)
            self.delete(self.tag_ranges('sel')[0], self.tag_ranges('sel')[1])
            self.tag_remove('sel', '1.0', 'end')
        else:
            cursorPos = self.index(tk.INSERT)
            self.insert(cursorPos, f'{SYNTAX_FRONT}{SYNTAX_BACK}')
            self.mark_set('insert', self.calcCursorMove(move=-(len(SYNTAX_BACK)), position=self.index(tk.INSERT))) # applies new position (inside Syntax) to cursor


    def calcCursorMove(self, move=-1, position='1.0'): # calculates the new position the text cursor should have when moved by a given value to the left (negative int) or the right (positive int); starting from a given position
        cursorPos = position.split('.') # splits the given cursor position into a line string [0] and a char string [1]
        cursorPos[1] = str(int(cursorPos[1]) + move) # modifies the char position
        cursorPos = '' + str(cursorPos[0]) + '.' + str(cursorPos[1]) # applies the needed position format: 'line.char' to cursorPos variable
        return cursorPos

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
        self.root.title('Writer - ' + self.fileLocation)

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
            self.progressBar = ttk.Progressbar(self.root, orient='horizontal', length=1000, mode='determinate', maximum=1)
            self.progressBar.pack(padx=20, pady=(25, 5))
            self.quitButton = tk.Button(self.root, text='Save & Exit', command=self.SaveAndExit, state='disabled', border=0)
            self.quitButton.pack(padx=20, pady=(0, 50))

        else: self.label = tk.Label(self.root, text="So you are the kind of person to use a distraction-free writing software without using the features that make the software distraction-free? Interesting decision...\n...\n...\n...\n Just out of interest, you do realize that without the distraction-free features this piece of software is just barely, if at all, better than the MS Editor, do you?").pack(padx=20, pady=20)

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
        self.root.after(AUTOSAVE_INTERVAL*1000, self.autoSave)

    def run(self):
        if self.blockSytle == 1: self.root.after(1000, self.updateTimeBar)
        elif self.blockSytle == 2: self.root.after(1000, self.updateWordBar)
        self.root.after(AUTOSAVE_INTERVAL*1000, self.autoSave)
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

#TODO: stylize the progress bar; it honestly doesn't really look good rn
#TODO: deactivate other monitors
#TODO: undo/redo

class WriterStartup():
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title('A_WritingProgram')
        self.root.geometry('525x275')
        self.root.resizable(0, 0)

        # You need to select a file beforehand, create one, if you start anew: File Selection
        fileFrame = tk.Frame(self.root)

        self.fileLabel = tk.Label(fileFrame, text='You need to select a file beforehand; create one, if you start anew: ')
        self.fileLabel.pack(pady=20, side='left')

        self.filename = 'test.md'

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

        self.fileLabel.config(text=self.filename)

    def startWriter(self):
        writer = Writer(fileLocation= self.filename, blockStyle= int(self.blockStyle.get()), blockValue= int(self.blockValue.get()))
        writer.run()
        self.root.destroy()

if __name__ == '__main__':
    #Writer(blockStyle=0).run()
    #WriterStartup()
    root = tk.Tk()

    text = BetterText(root, wrap='word', font=('Times New Roman', 16), width=90)
    text.pack()

    root.mainloop()