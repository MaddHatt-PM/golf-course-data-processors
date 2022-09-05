'''
Super ellipse equation: https://www.desmos.com/calculator/byif8mjgy3
'''

from functools import partial
from pathlib import Path

import tkinter as tk
from tkinter import Canvas, DoubleVar, Frame, StringVar
from tkinter import ttk

from asset_project import LocationPaths
from subviews import InspectorDrawer
from utilities import SpaceTransformer
from utilities.math import clamp01

class TreeAsset:
    global taper_range; taper_minmax = 0.0, 1.0
    global curvature_range; curvature_range = 0.5, 15.0

    def __init__(self, header:str="", data:str="", position_x=0.5, position_y=0.5) -> None:
        self.trunk_radius = 1.0
        self.trunk_height = 2.0
        self.trunk_offset = 0.0
        self.trunk_lower_taper = 0.0
        self.trunk_upper_taper = 0.0

        self.foliage_radius = 2.5
        self.foliage_height = 5.0
        self.foliage_offset = 0.0
        self.foliage_lower_curv = 2.0
        self.foliage_midpoint = 0.5
        self.foliage_upper_curv = 2.0

        self.position_x = position_x
        self.position_y = position_y

        self._name = ""
        self.__tkVars:dict[str, any] = {}

        if header != "" and data != "":
            variables = zip(header.split(','), data.split(','))
            for itemset in variables:
                if itemset[0] in self.__dict__:
                    self.__setattr__(itemset[0], eval(itemset[1]))
                else:
                    print("TreeAsset: {} not in __init__ variables".format(itemset[0]))

    def sync_variable(self, key:str, tkVar:DoubleVar, *args, **kwargs):
        self.__dict__[key] = tkVar.get()
        print("{} -> {}".format(key, self.__dict__[key]))

    def validate_for_double(self, value) -> bool:
        try:
            float(value)
            return True
        except:
            return False

    def select(self, view_manager:"TreeCollectionAsset"):
        self.__tkVars.clear()

        sel_text = "tree at {}, {}".format(self.position_x, self.position_y)
        view_manager.selected_tree_text.set(sel_text)

        for key in self.__dict__:
            if "trunk" in key or "foliage" in key:
                tkVar = DoubleVar()
                tkVar.set(self.__dict__[key])
                closure = partial(self.sync_variable, key, tkVar)
                tkVar.trace_add("write", closure)
                self.__tkVars[key] = tkVar

    def load_preset(self, tree:"TreeAsset"):
        preset = tree.__dict__
        for key in preset.keys():
            if "trunk" in key or "foliage" in key:
                self.__setattr__(key, preset[key])

    def to_csv(self, include_name=False) -> str:
        '''
        Variables beginning with an underscore are omitted
        '''
        output = ""
        if include_name:
            output +="{},".format(self._name)

        for item in self.__dict__:
            if item[0] != '_':
                output += "{},".format(self.__dict__[item])
            
        output = output.removesuffix(',')
        return output

    def header(self, include_name=False) -> str:
        output = ""
        if include_name:
            output +="{},".format("_name")

        for item in self.__dict__:
            if item[0] != '_':
                output += "{},".format(item)
            
        output = output.removesuffix(',')
        return output

    def demo(self):
        print(self.__dict__["trunk_radius"])
        # variables = locals()
        # variables.__setitem__("trunk_radius", 999.999)
        self.__setattr__("trunk_radius", 999.999)

    def sample_point(self, value01):
        '''
        Input values are clamped to 01 space.
        Input values are shifted to their corresponding
        curve (lower or upper)
        '''
        x = clamp01(value01)
        invert = (x <= 0.5)
        x = abs((x-0.5) * 2.0)

        curvature = self.foliage_lower_curv
        if invert:
            self.foliage_upper_curv

        y = pow((1.0 - pow(x , curvature)), 1.0 / curvature)
        if invert:
            y = -y
        return y

    def generate_foliage_profile(self, sample_count=16) -> list[tuple[float, float]]:
        radius = self.foliage_radius
        height = self.foliage_height
        offset = self.foliage_offset

        profile:list[tuple[float, float]] = []
        profile.append([0.0, offset])

        for i in range(1, sample_count-1):
            profile.append([
                radius * abs(self.sample_point((i - 1) / (sample_count - 1))),
                height * ((i - 1) / (sample_count - 1)) + offset
            ])

        profile.append([0.0, offset + height])

    def generate_trunk_profile(self) -> list[tuple[float, float]]:
        radius = self.trunk_radius
        height = self.trunk_height
        offset = self.trunk_offset
        lo_tap = self.trunk_lower_taper
        up_tap = self.trunk_upper_taper

        profile:list[tuple[float, float]] = [
            [0.0, offset],
            [radius * (1.0 - lo_tap), offset],
            [radius * (1.0 - up_tap), offset + height],
            [0.0, offset + height]
        ]

        return profile

    def get_largest_dimension(self):
        radius = max(self.foliage_radius, self.trunk_radius) * 2
        height = max(self.trunk_height + self.trunk_offset, self.foliage_offset + self.foliage_height)
        return max(radius, height)

    def example(self, *args, **kwargs):
        print("Test")

    def draw_to_inspector(self, inspector:Frame, drawer:InspectorDrawer):
        for key in self.__tkVars:
            cleaned_name = key.replace('_', ' ').capitalize()

            drawer.labeled_entry(
                label_text=cleaned_name,
                entry_variable=self.__tkVars[key],
                # validate_command=self.validate_for_double,
                pady=1
                )

class TreeCollectionAsset:
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
        # self.draw_to_inspector()

    def remove_tree(self, tree:TreeAsset):
        self.trees.remove(tree)
        self.save_data_to_files()
        self.draw_to_inspector()

    def draw_to_canvas(self, canvas:Canvas, util:SpaceTransformer):
        for id in self.canvas_ids:
            canvas.delete(id)
        self.canvas_ids.clear()

        for tree in self.trees:
            pos = tree.position_x, tree.position_y
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
            result = "{}, {}".format(tree.position_x, tree.position_y)
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

        self.selected_tree.draw_to_inspector(inspector, drawer)
        drawer.seperator()
        drawer.empty_space()
        drawer.button(text="Save all trees", command=self.save_data_to_files)



if __name__ == "__main__":
    # tree = TreeAsset()
    # tree.demo()
    # print(tree.header())
    # print(tree.export_to_csv())

    project = LocationPaths(savename="AshevilleClub")
    treeCol = TreeCollectionAsset(target=project)
    treeCol.save_presets()

    header = "trunk_radius,trunk_height,trunk_offset,trunk_lower_taper,trunk_upper_taper,foliage_radius,foliage_height,foliage_offset,foliage_lower_curv,foliage_midpoint,foliage_upper_curv"
    data = "999.999,2.0,0.0,0.0,0.0,2.5,5.0,0.0,2.0,0.5,123.123"
    tree = TreeAsset(header, data)
    print(tree.to_csv())