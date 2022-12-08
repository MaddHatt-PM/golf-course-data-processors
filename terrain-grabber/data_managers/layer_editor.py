import os
import tkinter as tk
from functools import partial
from pathlib import Path
from tkinter import Frame, Label, messagebox, simpledialog, StringVar, IntVar
from tkinter.ttk import Button, Entry
from typing import Callable

class LayerEditor:
    def __init__(self, layers:dict, commit_func:Callable, is_main_window=False):
        if is_main_window is True:
            self.window = tk.Tk()
        else:
            self.window = tk.Toplevel()
            self.window.grab_set()
            self.window.focus_force()
    
        self.window.title("Layer Manager")

        self.tkVars:list[tuple[StringVar, IntVar]] = []
        for key in layers:
            keyVar = StringVar(value=key)
            valueVar = IntVar(value=layers[key])
            self.tkVars.append((keyVar, valueVar))
        
        self.commit_func = commit_func
        # self.validate_state()
        self.errorVar = StringVar(value="")

        self.ui_items = []
        self.draw_ui()

        self.window.mainloop()

    def validate_state(self):
        defaultKeyVar = StringVar(value="Default")
        defaultValVar = IntVar(value=-10)
        var_pair = (defaultKeyVar, defaultValVar)
        if var_pair not in self.tkVars:
            self.tkVars.append(var_pair)

    def draw_ui(self):
        # Wipe out any pre-existing ui items
        for item in self.ui_items:
            item.destroy()   

        def draw_key_value_pair(frame, keyVar:StringVar, valueVar:IntVar):
            def modify_priority(valueVar:IntVar, amount):
                amount = valueVar.get() + (amount * 10)
                amount = max(0, min(1000, amount))
                valueVar.set(amount)
                self.draw_ui()
            
            subframe = Frame(frame)
            state = tk.NORMAL
            if keyVar.get() == "Default" and valueVar.get() == -10:
                state = tk.DISABLED

            keyEntry = Entry(subframe, textvariable=keyVar, state=state)
            keyEntry.grid(row=0, column=0, sticky='e', padx=5)
            self.ui_items.append(keyEntry)

            move_up_command = partial(modify_priority, valueVar, 1)
            move_up_button = Button(subframe, text="^", command=move_up_command, width=3, state=state)
            move_up_button.grid(row=0, column=1)
            self.ui_items.append(move_up_button)

            move_down_command = partial(modify_priority, valueVar, -1)
            move_down_button = Button(subframe, text="v", command=move_down_command, width=3, state=state)
            move_down_button.grid(row=0, column=2)
            self.ui_items.append(move_down_button)

            valueEntry = Entry(subframe, textvariable=valueVar, width=5, state=state)
            valueEntry.grid(row=0, column=3, sticky='e')
            self.ui_items.append(valueEntry)

            def delete_layer_command():
                self.tkVars.remove((keyVar, valueVar))
                self.draw_ui()

            delete_layer_button = Button(subframe, text="X", command=delete_layer_command, width=3, state=state)
            delete_layer_button.grid(row=0, column=4, padx=5)
            self.ui_items.append(delete_layer_button)

            subframe.pack(fill='x', padx=5)
            self.ui_items.append(subframe)

        # sort
        self.tkVars = sorted(
            self.tkVars,
            key= lambda item: item[1].get(),
            reverse=True
        )
        
        Label(
            self.window,
            text="Changing the name of a layer will reset areas\nusing that layer back to \"Default\"."
            ).pack()

        for keyVar, valueVar in self.tkVars:
            draw_key_value_pair(self.window, keyVar, valueVar)

        def add_new_layer_command():
            keyVar = StringVar(value="New Layer")
            valueVar = IntVar(value=0)
            self.tkVars.append((keyVar, valueVar))
            self.draw_ui()

        add_new_layer_button = Button(self.window, text="Add new layer", command=add_new_layer_command)
        add_new_layer_button.pack(padx=10, pady=10, fill='x')
        self.ui_items.append(add_new_layer_button)

        def on_confirm():
            # recreate dict from tkVars 
            layers = {}
            for pair in self.tkVars:
                key, val = pair
                layers[key.get()] = val.get()

            # validate check
            if len(layers) != len(self.tkVars):
                self.errorVar.set("Error: Duplicate layer name detected")
                self.draw_ui()
                return
                
            self.commit_func(layers)
            self.window.destroy()

        if self.errorVar.get() != "":
            error_label = Label(self.window, textvariable=self.errorVar)
            error_label.pack()
            self.ui_items.append(error_label)

        subframe = Frame(self.window)

        cancel = Button(subframe, text="Cancel", command=self.window.destroy)
        cancel.grid(row=0, column=0, sticky='ew')
        self.ui_items.append(cancel)

        confirm = Button(subframe, text="Confirm", command=on_confirm)
        confirm.grid(row=0, column=1, sticky='ew')
        self.ui_items.append(confirm)

        subframe.pack(fill='x', padx=5, pady=20)
        self.ui_items.append(subframe)
    
if __name__ == "__main__":
    layers = {
            "Trees" : 100,
            "Sandtrap": 80,
            "Green" : 60,
            "Fairway": 40,
            "Rough" : 10,
            }
    
    def commit_func(new_layers):
        layers = new_layers
        print(layers)

    LayerEditor(layers, commit_func, is_main_window=True)