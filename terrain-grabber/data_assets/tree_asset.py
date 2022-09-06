'''
Super ellipse equation: https://www.desmos.com/calculator/byif8mjgy3
'''

from pathlib import Path
from functools import partial
from time import sleep

import tkinter as tk
from tkinter import Canvas, DoubleVar, Frame, StringVar
from tkinter import ttk

from asset_project import LocationPaths
from subviews import InspectorDrawer
from subviews.inspector_drawer import TREE_PREVIEW_SIZE
from utilities import SpaceTransformer, UIColors
from utilities.math import clamp01
from utilities import UIColors

taper_minmax = 0.0, 1.0
curvature_range = 0.5, 15.0

class TreeAsset:

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
        self.canvas:Canvas = None
        self.canvas_items = []
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
        if self.canvas is not None:
            self.redraw_canvas()
        # print("{} -> {}".format(key, self.__dict__[key]))


    def validate_for_double(self, value) -> bool:
        try:
            float(value)
            return True
        except:
            return False

    def select(self, view_manager:"TreeCollectionManager"): # type: ignore
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

    def sample_point(self, value01):
        '''
        Input values are clamped to 01 space.
        Input values are shifted to their corresponding curve (lower or upper)
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
        for i in range(1, sample_count-1):
            profile.append([
                radius * abs(self.sample_point((i - 1) / (sample_count - 1))),
                height * ((i - 1) / (sample_count - 1)) + offset
            ])

        profile.append([0.0, offset + height])
        return profile

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

    def draw_to_inspector(self, inspector:Frame, drawer:InspectorDrawer):
        drawer.header('Tree Attributes')
        drawer.button('Add new Preset')
        drawer.button('Import from Preset')
        for key in self.__tkVars:
            cleaned_name = key.replace('_', ' ').capitalize()

            drawer.labeled_entry(
                label_text=cleaned_name,
                entry_variable=self.__tkVars[key],
                pady=1
                )

        drawer.seperator()
        drawer.vertical_divider()

        self.canvas = drawer.tree_preview()
        self.redraw_canvas()
        # Canvas is oriented so that 0,0 is the top left corner
        # self.canvas.create_oval(5, 5, 100, 100, fill= UIColors.blue.fill)
        # foliage = self.generate_foliage_profile()
        # print(foliage)

    def redraw_canvas(self):
        for item in self.canvas_items:
            self.canvas.delete(item)

        def mirror_x(pt) -> tuple[float,float]:
            return pt[0]*-1, pt[1]

        def offset(pt) -> tuple[float,float]:
            x,y = pt[0], pt[1]
            x += TREE_PREVIEW_SIZE[0] * 0.5
            y *= -1
            y += TREE_PREVIEW_SIZE[1]
            return x,y

        trunk_verts = self.generate_trunk_profile()
        trunk_verts += [mirror_x(v) for v in reversed(trunk_verts)]
        trunk_verts = [offset(v) for v in trunk_verts]

        for id in range(0, len(trunk_verts) - 1):
            line = self.canvas.create_line(
                *trunk_verts[id],
                *trunk_verts[id+1],
                width=3,
                fill='#654321'
            )
            self.canvas_items.append(line)


        foliage_verts = self.generate_foliage_profile(sample_count=32)
        foliage_verts += [mirror_x(v) for v in reversed(foliage_verts)]
        foliage_verts = [offset(v) for v in foliage_verts]

        for id in range(0, len(foliage_verts) - 1):
            line = self.canvas.create_line(
                *foliage_verts[id],
                *foliage_verts[id+1],
                width=3,
                fill=UIColors.green.path
            )
            self.canvas_items.append(line)

    def on_deselect(self):
        for item in self.canvas_items:
            self.canvas.delete(item)
        
        self.canvas = None
