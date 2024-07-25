# A_WritingProgram

A portable writing program specialised on markdown that is free<sup>2</sup>: distraction-free and free of charge.

I coded it together on a couple afternoons (and those staying up till 4AM nights) in my free time, because I like programming and I like writing, but my focus on the latter... well... could be better. 

The idea is simple: *A_WritingProgram* immerses you into your writing, meaning it just won't let you exit or minimize the window before you reached a goal you specified in advance. Following the approach of software like [FocusWriter](https://gottcode.org/focuswriter/), [ColdTurkey Writer](https://getcoldturkey.com/writer/) and I'm sure some other programs as well.

## How to use

When opening *A_WritingProgram* you'll see a configuration window that looks a little something like this:

![A_WritingProgram StartUp](https://github.com/user-attachments/assets/b87ed2e6-b3b8-4369-be22-975d3abaacb0)

In its main tab (open by default) you can...
1. Select a file to write to. (this step is non-optional, file selection must happen beforehand)
2. Give an amout of words you'll have to write / time you'll have to write for before the writing window can be closed again.
3. Choose how your number from Step 2 is interpreted: words, minutes or nothing (no blocking).
4. Start the Writer. (You won't be able to close the program until you reached your goal.)

The Writer itself looks like this. It's not spectacular, which is a good thing; for distraction-free-ness was the goal, remember?

![A_WritingProgram](https://github.com/user-attachments/assets/5450bf89-205f-4219-83b3-c21fe4fcf8dd)

## Installation

*A_WritingProgram* comes as a neat portable .exe file. You can just move it to anywhere you like and just double click to start. No installation needed. (keep in mind that, if you decide to save your settings, a ```settings.json``` will be created in the same directory)
 
*A_WritingProgram* is technically Windows-only, but can still be used on macOS or Linux based systems using [Wine](https://www.winehq.org/), which is something I do myself on my old Linux Laptop running [Xubuntu](https://xubuntu.org/).

## Settings (release version 1.1.0 or higher)

Settings are saved in a ```settings.json``` file that is created in the same directory as the one the .exe resides in. The settings should be edited through the setting tab in the writer startup. You can, however, if you want to for whatever reason, edit the settings file directly:

- ```displayHeader```: A boolean representing wheter or not to display the header "A_WritingProgram" over the TextField in the writer. Should probably be turned off on smaller screens for more writing real estate.

- ```autosaveInterval```: An int representing the interval for autosaves (in seconds). Autosaves are directly saved into your given file.

## Features of the Writer

Altough the Writer doesn't look special its input field has at least some quality of life features added in comparison to the default ```tkinter input widget``` you might want to use.

- *Undo / Redo*: Does what you'd exspect using Ctrl+Z and Ctrl+Y.

- *Markdown Syntax*: As this writer is specialised on markdown editing, you can insert the typical syntax for *italic*, **bold** and <u>underlined</u> text using Ctrl+I, Ctrl+B and Ctrl+U respectively.

- *Entire Word Removal* (a feature I was surprised to find out isn't baked into the input widget): Removing the word to the left or to the right of the cursor using Ctrl+Backspace (left) or Ctrl+Del (right).

## Some technical details

*A_WritingProgram* is written entirely in [Python](https://www.python.org/) using its built-in *tkinter* package. The coding happened primarily in [Visual Studio Code](https://code.visualstudio.com/) using its pre-installed Monokai theme.