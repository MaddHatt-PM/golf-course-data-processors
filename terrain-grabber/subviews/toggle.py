from tkinter import BooleanVar, Misc, ttk

on = '◼'
off = '◻'

class Toggle:

    def __init__(self, master:Misc, command=None, boolVar:BooleanVar=None):
        if boolVar.get() is True:
            graphic = on
        else:
            graphic = off

        self.button = ttk.Button(master, command=self.invert, text=graphic, width=5)
        self.boolVar = boolVar
        self.subcommand = command

    def invert(self):
        self.boolVar.set(not self.boolVar.get())

        if self.boolVar.get() is True:
            graphic = on
        else:
            graphic = off

        self.button.config(text=graphic)

        if self.subcommand is not None:
            self.subcommand()