
import tkinter as tk
from tkinter import Tk, Widget
from tkinter import ttk
from turtle import width

from Utilities import ui_colors


class inspector_drawers:
    '''
    Abstraction of tkinter to streamline and manage inspector drawing
    '''
    def __init__(self, frame:Tk):
        self.frame = frame
        self.items = []

        widthSize = 36
        width_definer = tk.Label(self.frame, text="", width=widthSize, height=1)
        width_definer.pack(anchor='s')

    def clear_inspector(self, *args, **kwargs):
        for item in self.items:
            item.destroy()

    def header(self, text=None, textVariable=None):
        text = tk.Label(self.frame, text=text, textVariable=None,
                         font=("Arial, 12"), anchor='w')
        text.pack(fill='x')

        self.items.append(text)
        return text

    def label(self, text=None, textVariable=None):
        text = tk.Label(self.frame, text=text, textVariable=None,
                        anchor='e')
        text.pack(fill='x', padx=5)

        self.items.append(text)
        return text

    def button(self, text=None, textVariable=None, command=None):
        button = tk.Button(self.frame, text=text, textvariable=textVariable, command=command)
        button.pack(fill='x', pady=4, padx=8)
        
        self.items.append(button)
        return button

    def empty_space(self):
        space = tk.Label(self.frame, text="")
        space.pack(fill='x')

        self.items.append(space)
        return space

    def seperator(self):
        seperator = ttk.Separator(self.frame, orient="horizontal")
        seperator.pack(fill='x')

        self.items.append(seperator)
        return seperator