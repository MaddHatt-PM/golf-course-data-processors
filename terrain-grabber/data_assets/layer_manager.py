import os
import tkinter as tk
from pathlib import Path
from tkinter import Frame, Canvas, messagebox, simpledialog
from tkinter.ttk import Button
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

        def draw_key_value_pair(frame, key, value):
            subframe = Frame(frame)
            subframe.pack()

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