import os
import tkinter as tk
from pathlib import Path
from tkinter import Frame, Canvas, messagebox, simpledialog, StringVar, IntVar
from tkinter.ttk import Button, Entry
from typing import Callable

class LayerManager:
    def __init__(self, layers:dict, commit_func:Callable, is_main_window=False):
        if is_main_window is True:
            self.window = tk.Tk()
        else:
            self.window = tk.Toplevel()
            self.window.grab_set()
            self.window.focus_force()
    
        self.window.title("Layer Manager")

        def draw_key_value_pair(frame, keyVar, valueVar):
            subframe = Frame(frame)

            keyEntry = Entry(subframe, textvariable=keyVar)
            keyEntry.grid(row=0, column=0, sticky='e', padx=5)

            valueEntry = Entry(subframe, textvariable=valueVar)
            valueEntry.grid(row=0, column=1, sticky='e', padx=5)
            subframe.pack(fill='x')

        self.tkVars:list[tuple[StringVar, IntVar]] = []
        for key in layers:
            keyVar = StringVar(value=key)
            valueVar = IntVar(value=layers[key])

            draw_key_value_pair(self.window, keyVar, valueVar)
            self.tkVars.append((keyVar, valueVar))

        def add_new_layer():
            keyVar = StringVar(value="New Layer")
            valueVar = IntVar(value=0)
            draw_key_value_pair(self.window, keyVar, valueVar)

        add_new_layer_button = Button(self.window, text="Add new layer")
        add_new_layer_button.pack(padx=5, pady=10, fill='x')

        def on_confirm():
            # recreate dict from tkVars 
            layers = {}
            for pair in self.tkVars:
                key, val = pair
                layers[key.get()] = val.get()

            # validate check
            if len(layers) != len(self.tkVars):
                print("Remove duplicate key")
                
            commit_func(layers)
            self.window.destroy()

        subframe = Frame(self.window)

        cancel = Button(subframe, text="cancel", command=self.window.destroy)
        cancel.grid(row=0, column=0, sticky='ew')

        confirm = Button(subframe, text="confirm", command=on_confirm)
        confirm.grid(row=0, column=1, sticky='ew')

        subframe.pack(fill='x', padx=5, pady=20)

        self.window.mainloop()

    
if __name__ == "__main__":
    layers = {
            "Trees" : 100,
            "Sandtrap": 80,
            "Green" : 60,
            "Fairway": 40,
            "Rough" : 20,
            }
    
    def commit_func(new_layers):
        layers = new_layers
        print(layers)

    LayerManager(layers, commit_func, is_main_window=True)