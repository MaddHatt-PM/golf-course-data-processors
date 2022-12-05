"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022
"""

from tkinter import BooleanVar, Misc, ttk

on = '◼'
off = '◻'

class Toggle:
    """
    UI component to turn a button into a toggle.
    """
    def __init__(self, master:Misc, command=None, boolVar:BooleanVar=None):
        if boolVar.get() is True:
            graphic = on
        else:
            graphic = off

        self.button = ttk.Button(master, command=self.on_click, text=graphic, width=5)
        self.boolVar = boolVar
        self.subcommand = command

    def on_click(self):
        """
        Callback function to handle given provided callbacks.
        """
        self.boolVar.set(not self.boolVar.get())

        if self.boolVar.get() is True:
            graphic = on
        else:
            graphic = off

        self.button.config(text=graphic)

        if self.subcommand is not None:
            self.subcommand()