'''
Super ellipse equation: https://www.desmos.com/calculator/byif8mjgy3
'''

from pathlib import Path
from functools import partial
from time import sleep

import tkinter as tk
from tkinter import Canvas, DoubleVar, Frame, IntVar, StringVar
from tkinter import ttk
from asset_project import LocationPaths
from subviews import InspectorDrawer
from subviews.inspector_drawer import TREE_PREVIEW_SIZE
from utilities import SpaceTransformer, UIColors
from utilities.math import clamp01, remap, rotate_from_2d_point

taper_minmax = 0.0, 1.0
curvature_range = 0.5, 15.0
ground_offset = 50.0

class TreeAsset:
    def __init__(self, header:str="", data:str="", position_x=0.5, position_y=0.5) -> None:
        self.is_dirty = False

        self.trunk_radius = 1.0
        self.trunk_height = 2.0
        self.trunk_offset = 0.0
        self.trunk_upper_taper = 0.0

        self.foliage_radius = 2.5
        self.foliage_height = 5.0
        self.foliage_offset = 0.0
        self.foliage_upper_curv = 2.0
        self.foliage_midpoint = 0.5
        self.foliage_lower_curv = 2.0

        self.transform_position_x = position_x
        self.transform_position_y = position_y
        self.transform_rotation_tilt = 0.0 # range: 0-90 degrees
        self.transform_rotation_spin = 0.0 # range: 0-360 degrees

        self.rendering_samples = 32

        self._name = ""
        self._canvas:Canvas = None
        self._canvas_items = []
        self.__tree_manager = None
        self.__trunkVars:dict[str, any] = {}
        self.__foliageVars:dict[str, any] = {}
        self.__positioningVars:dict[str, any] = {}
        self.__renderingVars:dict[str, any] = {}

        
        self.__slider_vars = {
            # var-name: min, max
            "transform_position_x": (-0.1, 1.1),
            "transform_position_y": (-0.1, 1.1),
            "trunk_upper_taper": (0.0, 1.0),
            "foliage_lower_curv": (0.005, 5.0),
            "foliage_midpoint": (0.0, 5.0),
            "foliage_upper_curv": (0.005, 2.0),
            "transform_rotation_tilt": (-90.0, 90.0),
            "transform_rotation_spin": (0.0, 360.0),
            # "rendering_samples": (8, 64)
        }

        if header != "" and data != "":
            variables = zip(header.split(','), data.split(','))
            for itemset in variables:
                if itemset[0] in self.__dict__:
                    self.__setattr__(itemset[0], eval(itemset[1]))
                else:
                    # print("TreeAsset: {} not in __init__ variables".format(itemset[0]))
                    pass

    def sync_variable(self, key:str, tkVar, *args, **kwargs):
        try:
            self.__dict__[key] = tkVar.get()
            self.__tree_manager.draw_to_viewport()
        except:
            return
        
        self.is_dirty = True
        self.redraw_inspector_preview()
        # print("{} -> {}".format(key, self.__dict__[key]))


    def validate_for_double(self, value) -> bool:
        try:
            float(value)
            return True
        except:
            return False

    def select(self, view_manager:"TreeCollectionManager"): # type: ignore
        self.__trunkVars.clear()
        self.__foliageVars.clear()
        self.__positioningVars.clear()
        self.__renderingVars.clear()
        self.__tree_manager = view_manager

        sel_text = "tree at {}, {}".format(self.transform_position_x, self.transform_position_y)
        view_manager.selected_tree_text.set(sel_text)

        def setup_key(key, dictionary:dict):
            tkVar = DoubleVar()
            tkVar.set(self.__dict__[key])
            closure = partial(self.sync_variable, key, tkVar)
            tkVar.trace_add("write", closure)
            dictionary[key] = tkVar
            

        for key in self.__dict__:
            if key[0] != '_':
                if "trunk" in key:
                    setup_key(key, self.__trunkVars)

                if "foliage" in key:
                    setup_key(key, self.__foliageVars)

                if "transform" in key:
                    setup_key(key, self.__positioningVars)

        tkVar = IntVar()
        tkVar.set(self.__dict__['rendering_samples'])
        closure = partial(self.sync_variable, 'rendering_samples', tkVar)
        tkVar.trace_add('write', closure)
        self.__renderingVars['rendering_samples'] = tkVar

    def deselect(self):
        self.__view_manager = None
        #Clean up canvas items
        pass

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

    def sample_foliage_point(self, value01):
        '''
        Input values are clamped to 01 space.
        Input values are shifted to their corresponding curve (lower or upper)
        '''
        x = clamp01(value01)
        invert = (x <= 0.5)
        x = abs((x-0.5) * 2.0)

        curvature = self.foliage_lower_curv if invert else self.foliage_upper_curv
        y = pow((1.0 - pow(x , curvature)), 1.0 / curvature)
        if invert:
            y *= -1
        return y

    def generate_foliage_profile(self) -> list[tuple[float, float]]:
        radius = self.foliage_radius
        height = self.foliage_height 
        offset = self.foliage_offset + self.trunk_offset

        profile:list[tuple[float, float]] = []
        samples = self.rendering_samples * 2 + 1
        for i in range(1, int(samples)-1):
            profile.append([
                radius * abs(self.sample_foliage_point((i - 1) / (int(samples) - 1))),
                height * ((i - 1) / (int(samples) - 1)) + offset
            ])

        profile.append([0.0, offset + height])

        def apply_midpoint_warp(pt):
            (x,y) = pt
            midpoint = offset + height * 0.5
            if (y < midpoint):
                y = remap(
                    val=y,
                    in_min=offset,
                    in_max=midpoint,
                    out_min=offset,
                    out_max=midpoint * self.foliage_midpoint)
            else:
                y = remap(
                    val=y,
                    in_min=midpoint,
                    in_max=offset + height,
                    out_min=midpoint * self.foliage_midpoint,
                    out_max=offset + height)
                    
            return (x,y)

        profile = [apply_midpoint_warp(pt) for pt in profile]
        return profile

    def generate_trunk_profile(self) -> list[tuple[float, float]]:
        radius = self.trunk_radius
        height = self.trunk_height
        offset = self.trunk_offset
        lo_tap = 0.0
        # lo_tap = self.trunk_lower_taper
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
        drawer.button_group(str_commands=[
            ('Add as Preset', None),
            ('Copy from Preset', None)
        ])

        def key_to_labeled_entry(key, dictionary):
            cleaned_name = key.replace('_', ' ').capitalize()

            if key in self.__slider_vars.keys():
                
                drawer.labeled_slider(
                    label_text=cleaned_name,
                    tkVar=dictionary[key],
                    from_=self.__slider_vars[key][0],
                    to=self.__slider_vars[key][1]
                )
            
            else:
                drawer.labeled_entry(
                    label_text=cleaned_name,
                    entry_variable=dictionary[key],
                    pady=1
                    )

        for key in self.__trunkVars:
            key_to_labeled_entry(key, self.__trunkVars)
        drawer.empty_space()

        for key in self.__foliageVars:
            key_to_labeled_entry(key, self.__foliageVars)
        drawer.empty_space()

        for key in self.__positioningVars:
            key_to_labeled_entry(key, self.__positioningVars)
        drawer.empty_space()

        for key in self.__renderingVars:
            key_to_labeled_entry(key, self.__renderingVars)
        drawer.empty_space()

        drawer.seperator()
        drawer.vertical_divider()

        self._canvas = drawer.tree_preview()
        self.redraw_inspector_preview()
        # Canvas is oriented so that 0,0 is the top left corner
        # self.canvas.create_oval(5, 5, 100, 100, fill= UIColors.blue.fill)
        # foliage = self.generate_foliage_profile()
        # print(foliage)

    def redraw_inspector_preview(self):
        for item in self._canvas_items:
            self._canvas.delete(item)

        def mirror_x(pt) -> tuple[float,float]:
            return pt[0]*-1, pt[1]

        def offset(pt) -> tuple[float,float]:
            x,y = pt[0], pt[1]
            x += TREE_PREVIEW_SIZE[0] * 0.5
            y *= -1
            y += TREE_PREVIEW_SIZE[1]
            y -= ground_offset
            return x,y

        origin = (
            TREE_PREVIEW_SIZE[0] * 0.5, # X
            TREE_PREVIEW_SIZE[1] - ground_offset, # Y
        )

        trunk_verts = self.generate_trunk_profile()
        trunk_verts += [mirror_x(pt) for pt in reversed(trunk_verts)]
        trunk_verts = [offset(pt) for pt in trunk_verts]
        trunk_verts = [rotate_from_2d_point(*pt, *origin, self.transform_rotation_tilt) for pt in trunk_verts]

        line_width = 1
        antialias = 0.5
        for id in range(0, len(trunk_verts) - 1):
            self._canvas_items.append(self._canvas.create_line(
                *trunk_verts[id],
                *trunk_verts[id+1],
                width=line_width,
                fill='#654321'
            ))
            # antialias line needs color multiplication with background
            # self.canvas_items.append(self.canvas.create_line(
            #     *trunk_verts[id],
            #     *trunk_verts[id+1],
            #     width=line_width + antialias,
            #     fill='#654321'
            # ))


        foliage_verts = self.generate_foliage_profile()
        foliage_verts += [mirror_x(v) for v in reversed(foliage_verts)]
        foliage_verts = [offset(v) for v in foliage_verts]
        foliage_verts = [rotate_from_2d_point(*pt, *origin, self.transform_rotation_tilt) for pt in foliage_verts]
        
        for id in range(0, len(foliage_verts) - 1):
            self._canvas_items.append(self._canvas.create_line(
                *foliage_verts[id],
                *foliage_verts[id+1],
                width=line_width,
                fill=UIColors.green.path
            ))
            # self.canvas_items.append(self.canvas.create_line(
            #     *foliage_verts[id],
            #     *foliage_verts[id+1],
            #     width=line_width + antialias,
            #     fill=UIColors.green.path
            # ))

        '''Draw foliage mid line'''
        # self._canvas_items.append(self._canvas.create_line(
        #     (0.0, TREE_PREVIEW_SIZE[1] - self.orig_midpoint - ground_offset),
        #     (TREE_PREVIEW_SIZE[0], TREE_PREVIEW_SIZE[1] - self.orig_midpoint - ground_offset),
        #     width=line_width,
        #     fill='#AAA'
        # ))

        '''Draw flat ground plane'''
        self._canvas_items.append(self._canvas.create_line(
            (0.0, TREE_PREVIEW_SIZE[1] - ground_offset),
            (TREE_PREVIEW_SIZE[0], TREE_PREVIEW_SIZE[1] - ground_offset),
            width=line_width,
            fill='#AAA'
        ))

    def on_deselect(self):
        for item in self._canvas_items:
            self._canvas.delete(item)
        
        self._canvas = None
