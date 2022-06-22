
import tkinter as tk
from tkinter import BooleanVar, Button, Frame, StringVar, Tk, Widget
from tkinter import ttk
from turtle import width

from matplotlib import style
from Toggle import Toggle

from Utilities import ui_colors


class inspector_drawers:
    '''
    Abstraction of tkinter to streamline and manage inspector drawing.
    Intended for rapid UI destroying and creation with inspector panels.
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

    def labeled_entry(self, label_text="", entryVariable="") -> ttk.Entry:
        subframe = Frame(self.frame, padx=0, pady=0)
        self.items.append(subframe)

        label = tk.Label(subframe, text=label_text)
        label.grid(row=0, column=0)
        self.items.append(label)

        entry = ttk.Entry(subframe, textvariable=entryVariable)
        entry.grid(row=0, column=2, sticky='e')
        self.items.append(entry)

        subframe.pack(fill='x')
        return entry

    def button(self, text="", textVariable=None, command=None, *args, **kwargs) -> ttk.Button:
        button = ttk.Button(self.frame, text=text, textvariable=textVariable, command=command, *args, **kwargs)
        button.pack(fill='x', pady=4, padx=8)
        
        self.items.append(button)
        return button

    def labeled_toggle(self, label_text:str="", command=None, boolVar:BooleanVar=None) -> Button:
        subframe = Frame(self.frame, padx=0, pady=0)
        self.items.append(subframe)

        label = tk.Label(subframe, text=label_text)
        label.grid(row=0, column=0)
        self.items.append(label)

        button = Toggle(subframe, command, boolVar).button
        button.grid(row=0, column=1)
        self.items.append(button)

        subframe.pack(fill='x')
        return button

    def labeled_slider(self, label_text:str="") -> ttk.Scale:
        subframe = Frame(self.frame, padx=0, pady=0, bg='red')
        subframe.pack(fill='x')
        self.items.append(subframe)

        label = tk.Label(subframe, text=label_text)
        label.grid(row=0, column=0)
        self.items.append(label)

        slider = ttk.Scale(subframe, orient='horizontal')
        slider.grid(row=0, column=1, columnspan=2, sticky="NSEW")
        self.items.append(slider)

        return slider

    def empty_space(self):
        space = tk.Label(self.frame, text="")
        space.pack(fill='x')

        self.items.append(space)
        return space

    def vertical_divider(self):
        space = tk.Label(self.frame, text="")
        space.pack(fill='x', expand=True)

        self.items.append(space)
        return space

    def seperator(self):
        seperator = ttk.Separator(self.frame, orient="horizontal")
        seperator.pack(fill='x')

        self.items.append(seperator)
        return seperator