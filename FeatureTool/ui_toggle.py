from tkinter import BooleanVar, Misc, ttk

class Toggle:
    on = '◼'
    off = '◻'

    def __init__(self, master:Misc, command=None, boolVar:BooleanVar=None):
        if boolVar.get() is True:
            graphic = Toggle.on
        else:
            graphic = Toggle.off

        self.button = ttk.Button(master, command=self.invert, text=graphic, width=3)
        self.boolVar = boolVar
        self.subcommand = command

    def invert(self):
        if self.subcommand is not None:
            self.subcommand()

        self.boolVar.set(not self.boolVar.get())

        if self.boolVar.get() is True:
            graphic = Toggle.on
        else:
            graphic = Toggle.off

        self.button.config(text=graphic)