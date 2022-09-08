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
        for item in self.items:
            item.destroy()

    def header(self, text=None, textVariable=None):
        text = tk.Label(self.frame, text=text, textVariable=None,
                         font=("Arial, 12"), anchor='w')
        text.pack(fill='x')

        self.items.append(text)
        return text

    def label(self, text:str=None):
        lines = text.splitlines()

        for line in lines:
            text = tk.Label(self.frame, text=line, anchor='e')
            text.pack(fill='x', padx=5, pady=0)
            self.items.append(text)

        return text

    def labeled_entry(self, label_text="", entry_variable:StringVar=None, validate_command=None, pady=0) -> ttk.Entry:
        subframe = Frame(self.frame, padx=0, pady=0)
        self.items.append(subframe)

        label = tk.Label(subframe, text=label_text)
        label.grid(row=0, column=0)
        self.items.append(label)

        entry = ttk.Entry(subframe, textvariable=entry_variable, validate='key', validatecommand=validate_command)
        entry.grid(row=0, column=2, sticky='e',pady=pady)
        self.items.append(entry)

        subframe.grid_columnconfigure(1, weight=3)
        subframe.pack(fill='x')
        return entry

    def button(self, text="", textVariable=None, command=None, *args, **kwargs) -> ttk.Button:
        button = ttk.Button(self.frame, text=text, textvariable=textVariable, command=command, *args, **kwargs)
        button.pack(fill='x', pady=4, padx=8)
        
        self.items.append(button)
        return button

    def labeled_toggle(self, boolVar:BooleanVar, label_text:str="", command=None ) -> Button:
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

    def labeled_slider(self, label_text:str="", from_:float=0.0, to:float=1.0, tkVar:DoubleVar=None) -> ttk.Scale:
        '''Create a slider with a range of 0.0 to 1.0 by default'''

        subframe = Frame(self.frame, padx=0, pady=0)
        subframe.pack(fill='x')
        self.items.append(subframe)

        label = tk.Label(subframe, text=label_text, padx=6)
        subframe.grid_columnconfigure(0, weight=1)
        label.grid(row=0, column=0, sticky='w')
        self.items.append(label)

        slider = ttk.Scale(subframe, orient='horizontal', length=145, from_=from_, to=to, variable=tkVar)
        slider.grid(row=0, column=1, columnspan=2, sticky="NSEW")
        self.items.append(slider)

        return slider

    def empty_space(self) -> tk.Label:
        space = tk.Label(self.frame, text="")
        space.pack(fill='x')

        self.items.append(space)
        return space

    def vertical_divider(self) -> tk.Label:
        space = tk.Label(self.frame, text="")
        space.pack(fill='x', expand=True)

        self.items.append(space)
        return space

    def seperator(self) -> ttk.Separator:
        seperator = ttk.Separator(self.frame, orient="horizontal")
        seperator.pack(fill='x', pady=5)

        self.items.append(seperator)
        return seperator

    def labeled_dropdown(self, current_var, value_data:list, value_names:list, default_index:int, label_text:str, change_commands=None) -> ttk.Combobox:
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
        canvas = Canvas(self.frame, width=TREE_PREVIEW_SIZE[0], height=TREE_PREVIEW_SIZE[1])
        self.items.append(canvas)

        canvas.configure(bg=UIColors.canvas_col, highlightthickness=0)
        canvas.pack()
        return canvas