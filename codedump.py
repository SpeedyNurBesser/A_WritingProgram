    def cursorAtWord(self): # returns True, if the text cursor is right before or after a word
        print('Hallo')
        cursorPos = self.index(tk.INSERT)
        self.wordstart = self.index(f'{cursorPos} wordstart')
        self.wordend = self.index(f'{cursorPos} wordend')
        print(cursorPos)
        print(self.wordstart)
        print(self.wordend)
        if cursorPos == self.wordstart or cursorPos == self.wordend:
            return True
        else:
            return False
        
        
        elif self.cursorAtWord():
            print('HAllo!')
            self.insert(self.wordend, SYNTAX_BACK)
            self.insert(self.wordstart, SYNTAX_FRONT)