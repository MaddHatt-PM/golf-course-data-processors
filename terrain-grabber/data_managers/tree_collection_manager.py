from pathlib import Path
from functools import partial

import tkinter as tk
from tkinter import Canvas, DoubleVar, Frame, StringVar
from tkinter import ttk

from asset_project import LocationPaths
from subviews import InspectorDrawer
from utilities import SpaceTransformer, UIColors
from utilities.math import clamp01
from data_assets import TreeAsset

class TreeCollectionManager:
    def __init__(self, target:LocationPaths) -> None:
        self.target = target
        self.trees:list[TreeAsset] = []
        self.load_data_from_file()

        self.selected_tree_text:StringVar = StringVar()
        self.selected_tree_text.set("None selected")
        self.selected_tree:TreeAsset = None
        if len(self.trees) == 0:
            self.trees.append(TreeAsset())

        if len(self.trees) > 0:
            self.selected_tree = self.trees[0]
            self.selected_tree.select(self)

        self.presets_path = Path("resources/tree_presets.csv")
        self.presets:list[TreeAsset] = []

        self.canvas_ids = []

        if self.presets_path.is_file() is True:
            with self.presets_path.open('r') as file:
                lines = file.readlines()
                header = lines.pop(0)
                for line in lines:
                    self.presets.append(TreeAsset(header, line))

    def load_data_from_file(self):
        if self.target.treesCSV_path.is_file():
            with self.target.treesCSV_path.open('r') as file:
                treedata = file.readlines()
                header = treedata.pop(0).replace('\n', '')

                for tree_str in treedata:
                    self.trees.append(TreeAsset(header=header, data=tree_str))

    def save_data_to_files(self):
        with self.target.treesCSV_path.open('w') as file:
            output = TreeAsset().header() + '\n'

            for tree in self.trees:
                output += tree.to_csv() + '\n'

            output = output.removesuffix('\n')
            file.write(output)

    # -------------------------------------------------------------- #
    # --- Presets -------------------------------------------------- #
    def add_preset(self, tree:TreeAsset=None):
        '''Adds currently selected tree if None provided'''
        if tree is None:
            tree = self.selected_tree

        self.presets.append(self.selected_tree.to_csv(include_name=True))
        self.save_presets()

    def remove_preset(self, index:int):
        self.presets.pop(index)
        self.save_presets()

    def save_presets(self):
        with self.presets_path.open('w'):
            with self.presets_path.open('w') as file:
                file.write(TreeAsset().header(include_name=True))
                file.write('\n')

                for tree in self.presets:
                    file.write(tree.to_csv)

    def _save_settings(self):
        pass

    def add_tree(self):
        tree = TreeAsset()
        self.trees.append(tree)
        self.save_data_to_files()

    def remove_tree(self, tree:TreeAsset):
        self.trees.remove(tree)
        self.save_data_to_files()
        self.draw_to_inspector()

    def draw_to_canvas(self, canvas:Canvas, util:SpaceTransformer):
        for id in self.canvas_ids:
            canvas.delete(id)
        self.canvas_ids.clear()

        for tree in self.trees:
            pos = tree.transform_position_x, tree.transform_position_y
            pos = util.norm_pt_to_pixel_space(pos)

            half_length = 2.0 # pixels
            center_coords = tuple(
                pos[0] - half_length,
                pos[1] - half_length,
                pos[0] + half_length,
                pos[1] + half_length
            )
            
            center_id = canvas.create_rectangle(*center_coords, fill="white")
            self.canvas_ids.append(center_id)

            # Draw radius
            radius = max(tree.trunk_radius, tree.foliage_radius)
            radius_cords = tuple(
                pos[0] - radius,
                pos[1] - radius,
                pos[0] + radius,
                pos[1] + radius
            )
            radius_id = canvas.create_oval(*radius_cords, fill="blue")
            self.canvas_ids.append(radius_id)

    def draw_to_inspector(self, inspector:Frame, drawer:InspectorDrawer):
        '''
        Mockup:
        
        canvasSelect:Button | trees:Dropdown | new_tree:Button
        sub_canvas renderer
        '''

        tree_pos_list = []
        for tree in self.trees:
            result = "{}, {}".format(tree.transform_position_x, tree.transform_position_y)
            tree_pos_list.append(result)

        selector_frame = Frame(inspector, padx=0, pady=0)
        tk.Label(selector_frame, text="Selected tree:").grid(row=0, column=0)
        
        dropdown = ttk.OptionMenu(selector_frame, self.selected_tree_text, self.selected_tree_text.get(), *tree_pos_list)
        dropdown.grid(row=0, column=1, sticky='ew')
        
        # ttk.Label(selector_frame, textvariable=self.selected_tree_text, anchor="e").grid(row=0, column=1)
        ttk.Button(selector_frame, text='⦺', width=2).grid(row=0, column=2)
        ttk.Button(selector_frame, text='+', width=2, command=self.add_tree).grid(row=0, column=3)
        selector_frame.grid_columnconfigure(1, weight=5)
        selector_frame.pack(fill="x", anchor="n", expand=False)
        drawer.seperator()

        self.selected_tree.draw_to_inspector(inspector, drawer)

        # drawer.empty_space()
        # drawer.button(text="Save all trees", command=self.save_data_to_files)