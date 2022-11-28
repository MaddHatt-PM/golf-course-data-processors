from functools import partial
import os
import tkinter as tk
from pathlib import Path
from tkinter import Frame, StringVar, Canvas
from tkinter.ttk import Entry, Label, Button

from data_assets import TreeAsset
from utilities import UIColors


'''
For later: Importing from sibling folder:
https://stackoverflow.com/questions/6323860/sibling-package-imports
'''

class TreeSelector:
    def __init__(self, activeTree, isMainWindow=False, onConfirmFunc=None) -> None:
        if isMainWindow == True:
            self.window = tk.Tk()
        else:
            self.window = tk.Toplevel()
            self.window.grab_set()
            self.window.focus_force()

        self.window.title("Tree Selector")
        # self.window.geometry("600x400")

        self.content = Frame(self.window)
        self.content.grid(row=0, column=0, sticky="nsew")

        self.active_tree:TreeAsset = activeTree
        self.onConfirmFunc = onConfirmFunc
        self.preset_trees = {}
        self.header = ""
        self.selected_preset = None
        self.selected_preset_tree:TreeAsset = None
        self.load_presets()
        self.setup_buttons()

        self.selector_frame = None
        self.setup_preset_selector()

        self.canvas = None
        self.setup_canvas()
        
        self.window.mainloop()

    def load_presets(self):
        presets_path = Path(os.path.dirname(__file__)) / "tree_presets.csv"
        with presets_path.open() as file:
            lines = file.readlines()

        self.header = lines.pop(0)
        self.header = self.header.removeprefix('name,')

        for line in lines:
            line = line.split(',')
            name = line.pop(0)
            line = ','.join(line)

            if (self.selected_preset is None):
                self.selected_preset = name

            self.preset_trees[name] = TreeAsset(header=self.header, data=line)

        # TODO: Remove this testcode
        self.active_tree = self.preset_trees[self.selected_preset]
        self.preset_trees.pop(self.selected_preset)
        self.selected_preset = list(self.preset_trees.keys())[0]

    def setup_preset_selector(self):
        if (self.selector_frame == None):
            selector_frame = Frame(self.content, bg="#505050")
            selector_frame.grid(row=0, column=0)

        def make_preset_cell(keyname:str, preset:TreeAsset) -> Frame:
            cell = Frame(selector_frame)
            cell.pack()

            def set_selected_preset(keyname):
                self.selected_preset = keyname
                self.setup_canvas()

            text = keyname + '\n' + "other text goes here"
            command = partial(set_selected_preset, keyname)
            btn = Button(cell, text=text, command=command)
            btn.pack()


        for keyname in self.preset_trees.keys():
            make_preset_cell(keyname, self.preset_trees[keyname])

    def setup_canvas(self):
        if (self.canvas == None):
            canvas_frame = Frame(self.content)
            canvas_frame.grid(row=0, column=1)

            self.canvas = Canvas(canvas_frame, width=250, height=250*1.618)
            self.canvas.configure(bg=UIColors.canvas_col, highlightthickness=0)
            self.canvas.pack()
        else:
            self.canvas.delete('all')

        if (self.active_tree != None):
            self.active_tree.draw_preview(
                overrideColor="#4b4b4b",
                overrideCanvas=self.canvas
            )

        if (len(self.preset_trees) != 0 and self.preset_trees[self.selected_preset] != None):
            self.preset_trees[self.selected_preset].draw_preview(
                overrideCanvas=self.canvas
            )

    def setup_buttons(self):
        output_frame = Frame(self.window)
        output_frame.grid(row=1, column=0, sticky="ew")

        if (self.onConfirmFunc != None):
            cancel_btn = Button(
                output_frame,
                text="Cancel",
                command=self.window.destroy,
                width=22)
            cancel_btn.grid(row=0, column=0, sticky='ew')

            def onConfirm():
                self.onConfirmFunc(self.preset_trees[self.selected_preset])
                self.window.destroy()

            confirm_btn = Button(
                output_frame, 
                text="Confirm", 
                command=onConfirm, 
                width=22)
            confirm_btn.grid(row=0, column=1, sticky='ew')
        
        else:
            close_btn = Button(output_frame, text="Close", command=self.window.destroy)
            close_btn.grid(row=0, column=1, sticky='ew')


    def render_canvas(self):
        '''Attempt to render previous tree for a frame of reference'''

if __name__ == "__main__":
    TreeSelector(None, isMainWindow=True)
    def testFunc(tree_asset):
        print("I did stuff")

    TreeSelector(None, isMainWindow=True, onConfirmFunc=testFunc)