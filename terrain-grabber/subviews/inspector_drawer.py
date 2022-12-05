"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022
"""

from typing import Callable
from functools import partial
import tkinter as tk
from tkinter import BooleanVar, Button, Canvas, DoubleVar, Frame, StringVar, Tk, Variable
from tkinter import ttk

from .toggle import Toggle
from utilities import UIColors

TREE_PREVIEW_SIZE = 250,250*1.618

class InspectorDrawer:
    '''
    Abstraction of tkinter to streamline and manage inspector drawing.
    Intended for rapid UI destroying and creation with inspector panels.
    '''
    def __init__(self, frame:Tk):
        self.frame = frame
        self.items = []
        
        # widthSize = 36
        # width_definer = tk.Label(self.frame, text="", width=widthSize, height=1)
        # width_definer.pack(anchor='s')
        # width_definer.place(relx=0, rely=0)

    def clear_inspector(self, *args, **kwargs):
        """Clear all components currently rendered by InspectorDrawer"""
        for item in self.items:
            item.destroy()

    def header(self, text=None, textVariable=None):
        """Create a label that is left aligned with a larger font"""
        text = tk.Label(self.frame, text=text, textVariable=None,
                         font=("Arial, 12"), anchor='w')
        text.pack(fill='x')

        self.items.append(text)
        return text

    def label(self, text:str=None):
        """Create a label that is right aligned"""
        lines = text.splitlines()

        for line in lines:
            text = tk.Label(self.frame, text=line, anchor='e')
            text.pack(fill='x', padx=5, pady=0)
            self.items.append(text)

        return text

    def labeled_entry(self, label_text="", entry_variable:StringVar=None, validate_command=None, pady=0, width=8) -> ttk.Entry:
        """
        Create a pair of UI components.\n
        1. Left aligned: a label.
        2. Right aligned: a textinput.
        """
        subframe = Frame(self.frame, padx=0, pady=0)
        self.items.append(subframe)

        label = tk.Label(subframe, text=label_text)
        label.grid(row=0, column=0)
        self.items.append(label)

        entry = ttk.Entry(subframe, textvariable=entry_variable, validate='key', validatecommand=validate_command, width=width)
        entry.grid(row=0, column=2, sticky='e',pady=pady)
        self.items.append(entry)

        subframe.grid_columnconfigure(1, weight=3)
        subframe.pack(fill='x')
        return entry

    def button(self, text="", textVariable=None, command=None, *args, **kwargs) -> ttk.Button:
        """
        Create a button that fills it's horizontal space.
        """
        button = ttk.Button(self.frame, text=text, textvariable=textVariable, command=command, *args, **kwargs)
        button.pack(fill='x', pady=4, padx=8)
        
        self.items.append(button)
        return button

    def labeled_toggle(self, boolVar:BooleanVar, label_text:str="", command=None ) -> Button:
        """
        Create a pair of UI components.\n
        1. Left aligned: a label.
        2. Right aligned: a toggle with callbacks for on/off.
        """
        subframe = Frame(self.frame, padx=0, pady=0)
        self.items.append(subframe)

        label = tk.Label(subframe, text=label_text, anchor='w', padx=6)
        label.grid(row=0, column=0, sticky='ew')
        self.items.append(label)

        button = Toggle(subframe, command, boolVar).button
        button.grid(row=0, column=1)
        self.items.append(button)

        space = tk.Label(subframe, text="")
        space.grid(row=0, column=2)
        self.items.append(space)

        subframe.grid_columnconfigure(0, weight=1)
        subframe.pack(fill='x')
        return button

    def labeled_slider(self, label_text:str="", from_:float=0.0, to:float=1.0, tkVar:DoubleVar=None, width=8) -> ttk.Scale:
        """
        Create a pair of UI components.\n
        1. Left aligned: a label.
        2. Right aligned: a slider.
        """
        subframe = Frame(self.frame, padx=0, pady=0)
        subframe.pack(fill='x')
        self.items.append(subframe)

        label = tk.Label(subframe, text=label_text, padx=0)
        subframe.grid_columnconfigure(0, weight=5)
        label.grid(row=0, column=0, sticky='w')
        self.items.append(label)

        slider = ttk.Scale(subframe, orient='horizontal', length=80, from_=from_, to=to, variable=tkVar)
        slider.grid(row=0, column=1, columnspan=1, sticky="NSEW")
        subframe.grid_columnconfigure(1, weight=5)
        self.items.append(slider)

        entry = ttk.Entry(subframe, textvariable=tkVar, validate='key', width=width)
        entry.grid(row=0, column=2)
        # subframe.grid_columnconfigure(2, weight=1)
        self.items.append(entry)

        return slider

    def empty_space(self) -> tk.Label:
        """
        Create an empty label to space out elements.
        """
        space = tk.Label(self.frame, text="")
        space.pack(fill='x')

        self.items.append(space)
        return space

    def vertical_divider(self) -> tk.Label:
        """
        Create a divider of empty space that pushes elements packed before and after.
        Can be coupled with multiple dividers with elements inbetween for more layout options.
        """
        space = tk.Label(self.frame, text="")
        space.pack(fill='x', expand=True)

        self.items.append(space)
        return space

    def seperator(self) -> ttk.Separator:
        """
        Create a graphical seperator that fills it's horiontal space.
        """
        seperator = ttk.Separator(self.frame, orient="horizontal")
        seperator.pack(fill='x', pady=5)

        self.items.append(seperator)
        return seperator

    def labeled_dropdown(self, current_var, value_data:list, value_names:list, default_index:int, label_text:str, change_commands=None) -> ttk.Combobox:
        """
        Create a pair of UI components.\n
        1. Left aligned: a label.
        2. Right aligned: a dropdown with given information.
        """
        subframe = Frame(self.frame, padx=0, pady=0)
        subframe.pack(fill='x')
        self.items.append(subframe)

        label = tk.Label(subframe, text=label_text, padx=6)
        label.grid(row=0, column=0, sticky='w')
        subframe.grid_columnconfigure(0, weight=1)
        self.items.append(label)

        dropdown = ttk.Combobox(subframe)
        dropdown['values'] = value_names
        dropdown['state'] = 'readonly'
        index = 0
        for i in range(len(value_data)):
            if value_data[i] == current_var:
                index = i
                break

        dropdown.current(index)
        dropdown.grid(row=0, column=1)

        def on_change(output_var, *args, **kwargs):
            output_var = value_data[dropdown.current()]

            if change_commands is not None:
                change_commands(output_var)

        closure = partial(on_change, current_var)

        dropdown.bind('<<ComboboxSelected>>', closure)

        self.items.append(dropdown)
        return dropdown

    def button_group(self, str_commands:list[tuple[str, Callable]]=None):
        """
        Create a horizontal group of buttons.
        """
        subframe = Frame(self.frame, padx=0, pady=0)
        self.items.append(subframe)

        for id, combo in enumerate(str_commands):
            (text, command) = combo
            button = ttk.Button(subframe, text=text, command=command)
            button.grid(row=0, column=id, sticky='EW')
            subframe.columnconfigure(id, weight=1)
        
        subframe.pack(fill='x')
        return subframe

    def tree_preview(self):
        """Create a canvas specifically for a tree previews"""
        canvas = Canvas(self.frame, width=TREE_PREVIEW_SIZE[0], height=TREE_PREVIEW_SIZE[1])
        self.items.append(canvas)

        canvas.configure(bg=UIColors.canvas_col, highlightthickness=0)
        canvas.pack()
        return canvas