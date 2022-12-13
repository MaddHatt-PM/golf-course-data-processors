"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022

References:
    Super ellipse equation: https://www.desmos.com/calculator/byif8mjgy3
"""

from functools import partial
from tkinter import Canvas, DoubleVar, Frame, IntVar
from subviews import InspectorDrawer
from subviews.inspector_drawer import TREE_PREVIEW_SIZE
from utilities import UIColors
from utilities.math import clamp01, remap, rotate_from_2d_point

from typing import Callable

import os
import tkinter as tk
from pathlib import Path
from tkinter import Frame, Canvas, messagebox, simpledialog
from tkinter.ttk import Button

TAPER_MINMAX = 0.0, 1.0
CURVATURE_RANGE = 0.5, 15.0
GROUND_OFFSET = 50.0

PRESETS_PATH = Path(os.path.dirname(__file__)) / "tree_presets.csv"

def add_preset(name, tree:"TreeAsset"):
    """
    Add a tree's parameters to the presets file.\n
    Create the preset file with header if needed.
    """
    if PRESETS_PATH.exists() is False:
        with PRESETS_PATH.open('w', encoding="utf8") as file:
            file.write("name," + tree.generate_header() + '\n')

    with PRESETS_PATH.open('a', encoding="utf8") as file:
        file.write(name + ',' + tree.to_csv() + '\n')

class TreeSelector:
    """Create a window to display and select presets of tree"""
    def __init__(self, active_tree, is_main_window=False, on_confirm_func=None) -> None:
        if is_main_window is True:
            self.window = tk.Tk()
        else:
            self.window = tk.Toplevel()
            self.window.grab_set()
            self.window.focus_force()

        self.window.title("Tree Selector")

        if PRESETS_PATH.exists() is False:
            messagebox.showerror(
                "Warning",
                "No available presets at " +
                str(PRESETS_PATH) +
                "\nAdd more presets via the inspector"
                )
            return

        self.content = Frame(self.window)
        self.content.grid(row=0, column=0, sticky="nsew")

        self.active_tree:TreeAsset = active_tree
        self.on_confirm_func = on_confirm_func

        self.header = ""
        self.preset_trees = {}
        self.selected_preset = None
        self.selected_preset_tree:TreeAsset = None
        self.load_presets()
        self.setup_buttons()

        self.canvas = None
        self.setup_canvas()

        self.selector_frame = None
        self.setup_preset_selector()

        self.window.mainloop()

    def load_presets(self):
        """
        Deserialize presets from a csv file into a dictionary of tree_assets
        """
        
        with PRESETS_PATH.open() as file:
            lines = file.readlines()

        self.header = lines.pop(0)
        self.header = self.header.removeprefix('name,')

        for line in lines:
            if line[0] == '#':
                # skip comment lines
                continue

            line = line.split(',')
            name = line.pop(0)
            line = ','.join(line)

            if self.selected_preset is None:
                self.selected_preset = name

            self.preset_trees[name] = TreeAsset(header=self.header, data=line)

    def setup_preset_selector(self):
        '''
        Setup the frame for the presets then create preset buttons through self.tree_presets.
        '''
        if self.selector_frame is None:
            selector_frame = Frame(self.content, bg="#505050")
            selector_frame.grid(row=0, column=0)

        def make_preset_cell(keyname:str) -> Frame:
            '''
            Create a cell that displays the name of the preset.\n
            On click, toggle this cell as the selected preset.
            '''
            cell = Frame(selector_frame)
            cell.pack()

            def set_selected_preset(keyname):
                self.selected_preset = keyname
                self.setup_canvas()

            text = keyname + '\n' + "other text goes here"
            command = partial(set_selected_preset, keyname)
            btn = Button(cell, text=text, command=command, width=40)
            btn.pack()

        for keyname in self.preset_trees:
            make_preset_cell(keyname)

        tk.Label(selector_frame, text="test").pack(fill='both', expand=True)
        tk.Label(selector_frame, text="test").pack(fill='both', expand=True)


    def setup_canvas(self):
        '''
        Setup the canvas if initial call.\n
        Draw a preview of self.active_tree_preset.
        If a tree is provided to the constructor, draw the tree with greyscale and low contrast.\n
        '''
        if self.canvas is None:
            canvas_frame = Frame(self.content)
            canvas_frame.grid(row=0, column=1)

            self.canvas = Canvas(canvas_frame, width=250, height=250*1.618)
            self.canvas.configure(bg="#212121", highlightthickness=0)
            self.canvas.pack()
        else:
            self.canvas.delete('all')

        if self.active_tree is not None:
            self.active_tree.draw_preview(
                overrideColor="#4b4b4b",
                overrideCanvas=self.canvas,
                ignore_transforms=True
            )

        if (len(self.preset_trees) != 0 and self.preset_trees[self.selected_preset] is not None):
            self.preset_trees[self.selected_preset].draw_preview(
                overrideCanvas=self.canvas,
                ignore_transforms=True
            )

    def setup_buttons(self):
        """
        If an onConfirm function was provided in the constructor,
        create a cancel and confirm button.\n
        Else, just create a close button.
        """
        output_frame = Frame(self.window)
        output_frame.grid(row=1, column=0, sticky="ew")

        if self.on_confirm_func is not None:
            cancel_btn = Button(
                output_frame,
                text="Cancel",
                command=self.window.destroy,
                width=22)
            cancel_btn.grid(row=0, column=0, sticky='ew')

            def on_confirm():
                self.on_confirm_func(self.preset_trees[self.selected_preset])
                self.window.destroy()

            confirm_btn = Button(
                output_frame,
                text="Confirm",
                command=on_confirm,
                width=22)
            confirm_btn.grid(row=0, column=1, sticky='ew')

        else:
            close_btn = Button(output_frame, text="Close", command=self.window.destroy)
            close_btn.grid(row=0, column=1, sticky='ew')

    def save_preset(self):
        pass


class TreeAsset:
    """
    A parametric representation of a tree's trunk and foliage.\n
    Also contains helper methods to:
    1. Draw the tree in 2D in a forward facing preview
    2. Draw variables to an inspector and sync any changes from tkinter
    3. Convert the parametric representation into a series of points at a chosen resolution
    4. Export an OBJ 3D Model
    """
    def __init__(self, header:str="", data:str="", position_x=0.5, position_y=0.5) -> None:
        self._is_dirty = False

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
        self.__trunk_vars:dict[str, any] = {}
        self.__foliage_vars:dict[str, any] = {}
        self.__transform_vars:dict[str, any] = {}
        self.__rendering_vars:dict[str, any] = {}

        self.__set_default_func:Callable = None
        self.__redraw_func:Callable = None

        
        self.__slider_vars = {
            # var-name: min, max
            "transform_position_x": (-0.1, 1.1),
            "transform_position_y": (-0.1, 1.1),
            "trunk_upper_taper": (0.0, 1.0),
            "foliage_lower_curv": (0.005, 2.0),
            "foliage_midpoint": (-1.0, 1.0),
            "foliage_upper_curv": (0.005, 2.0),
            "transform_rotation_tilt": (0, 90.0),
            "transform_rotation_spin": (0.0, 360.0),
            # "rendering_samples": (8, 64)
        }

        self.__ignore_ui_vars = [
            "transform_position_x",
            "transform_position_y",
        ]

        if header != "" and data != "":
            variables = zip(header.split(','), data.split(','))
            for itemset in variables:
                if itemset[0] in self.__dict__:
                    self.__setattr__(itemset[0], eval(itemset[1]))
                else:
                    # print("TreeAsset: {} not in __init__ variables".format(itemset[0]))
                    pass


    def sync_variable(self, key:str, tkVar, *args, **kwargs):
        """
        Sync the given tkVar with the tree_asset's variable then update the viewport
        """
        try:
            self.__dict__[key] = tkVar.get()
            self.__tree_manager.draw_to_viewport()
        except:
            return

        self._is_dirty = True
        self.draw_preview()
        # print("{} -> {}".format(key, self.__dict__[key]))


    def copy_from(self, other_tree:"TreeAsset", exclude_transform=True):
        for key in self.__dict__:
            if exclude_transform and "transform" in key:
                continue

            self.__dict__[key] = other_tree.__dict__[key]


    def validate_for_double(self, value) -> bool:
        """
        Attempt to convert the given value into a double.
        """
        try:
            float(value)
            return True
        except:
            return False

    def select(self, view_manager:"TreeCollectionManager", redraw_func, set_default_func): # type: ignore
        """
        Called when selected as the active tree in an inspector UI
        """
        self.__trunk_vars.clear()
        self.__foliage_vars.clear()
        self.__transform_vars.clear()
        self.__rendering_vars.clear()
        self.__tree_manager = view_manager

        def setup_key(key, dictionary:dict):
            tk_var = DoubleVar()
            tk_var.set(self.__dict__[key])
            closure = partial(self.sync_variable, key, tk_var)
            tk_var.trace_add("write", closure)
            dictionary[key] = tk_var

        for key in self.__dict__:
            if key[0] != '_':
                if "trunk" in key:
                    setup_key(key, self.__trunk_vars)

                if "foliage" in key:
                    setup_key(key, self.__foliage_vars)

                if "transform" in key:
                    setup_key(key, self.__transform_vars)

        tkVar = IntVar()
        tkVar.set(self.__dict__['rendering_samples'])
        closure = partial(self.sync_variable, 'rendering_samples', tkVar)
        tkVar.trace_add('write', closure)
        self.__rendering_vars['rendering_samples'] = tkVar

        self.__redraw_func = redraw_func
        self.__set_default_func = set_default_func

    def deselect(self):
        """
        Called when no longer selected as the active tree in an inspector UI
        """
        if self._canvas is not None:
            for item in self._canvas_items:
                self._canvas.delete(item)
        
        self.__trunk_vars.clear()
        self.__foliage_vars.clear()
        self.__transform_vars.clear()
        self.__rendering_vars.clear()
        self.__tree_manager = None
        self.__redraw_func = None
        self._canvas = None

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

    def generate_header(self, include_name=False) -> str:
        """
        Generate a csv header of tree_asset variables.\n
        Variables beginning with an excluded will be excluded.\n
        Does not include new line character.
        """
        output = ""
        if include_name:
            output +="{},".format("_name")

        for item in self.__dict__:
            if item[0] != '_':
                output += "{},".format(item)
            
        output = output.removesuffix(',')
        return output

    def move_tree_to_point(self, x,y):
        self.__transform_vars["transform_position_x"].set(x)
        self.__transform_vars["transform_position_y"].set(y)

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

    def generate_foliage_profile(self, samples=None) -> list[tuple[float, float]]:
        radius = self.foliage_radius
        height = self.foliage_height 

        profile:list[tuple[float, float]] = []
        if samples is None:
            samples = self.rendering_samples * 2 + 1

        for i in range(1, int(samples)-1):
            profile.append([
                radius * abs(self.sample_foliage_point((i - 1) / (int(samples) - 1))),
                height * ((i - 1) / (int(samples) - 1))
            ])

        profile.append([0.0, height])

        def apply_midpoint_warp(pt):
            (x,y) = pt
            midpoint = height * 0.5
            if (y < midpoint):
                y = remap(
                    val=y,
                    in_min=0,
                    in_max=midpoint,
                    out_min=0,
                    out_max=midpoint * (self.foliage_midpoint + 1))
            else:
                y = remap(
                    val=y,
                    in_min=midpoint,
                    in_max=height,
                    out_min=midpoint * (self.foliage_midpoint + 1),
                    out_max=height)
                    
            return (x,y)

        profile = [apply_midpoint_warp(pt) for pt in profile]

        def apply_offset(pt):
            offset = self.foliage_offset + self.trunk_offset
            (x,y) = pt
            return (x, y + offset)

        profile = [apply_offset(pt) for pt in profile]

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
        if self._canvas is not None:
            for item in self._canvas_items:
                    self._canvas.delete(item)

        drawer.clear_inspector()

        def open_tree_selector():
            def on_confirm_func(target_tree:TreeAsset):
                if target_tree is not None:
                    for key in self.__dict__.keys():
                        if key[0] != '_' and "transform" not in key:
                            self.__dict__[key] = target_tree.__dict__[key]

                    self.select(self.__tree_manager, self.__redraw_func)
                    self.__redraw_func()


            TreeSelector(active_tree=self, on_confirm_func=on_confirm_func)

        def add_self_to_preset():
            preset_name = simpledialog.askstring(
                "Name the preset",
                "Enter in a valid preset name without any commas"
                )

            if ',' in preset_name:
                messagebox.showerror(
                    "Error",
                    "Preset name contained a comma and will not be added"
                )

            add_preset(name=preset_name, tree=self)

        def set_default():
            if self.__set_default_func is not None:
                self.__set_default_func(self)

        drawer.header('Tree Attributes (in ft)')
        drawer.button_group(str_commands=[
            ('Add preset', add_self_to_preset),
            ('Copy preset', open_tree_selector),
            ('Set default', set_default),
        ])

        def key_to_labeled_entry(key, dictionary):
            if key in self.__ignore_ui_vars:
                return

            cleaned_name:str = key.replace('_', ' ').title()
            if "Transform " in cleaned_name:
                cleaned_name = cleaned_name.removeprefix("Transform ")

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

        for key in self.__trunk_vars:
            key_to_labeled_entry(key, self.__trunk_vars)
        drawer.empty_space()

        for key in self.__foliage_vars:
            key_to_labeled_entry(key, self.__foliage_vars)
        drawer.empty_space()

        for key in self.__transform_vars:
            key_to_labeled_entry(key, self.__transform_vars)
        drawer.empty_space()

        for key in self.__rendering_vars:
            key_to_labeled_entry(key, self.__rendering_vars)
        drawer.empty_space()

        drawer.seperator()
        drawer.header(text="Controls")
        drawer.label(text="Right click: Move tree to position")
        drawer.seperator()
        drawer.vertical_divider()

        # Canvas is oriented so that 0,0 is the top left corner
        self._canvas = drawer.tree_preview()
        self.draw_preview()
        # self.canvas.create_oval(5, 5, 100, 100, fill= UIColors.blue.fill)
        # foliage = self.generate_foliage_profile()
        # print(foliage)

    def draw_preview(self, overrideColor=None, overrideCanvas=None, ignore_transforms=False):
        canvas = overrideCanvas if overrideCanvas != None else self._canvas

        def checkOverrideColor(color:str):
            return overrideColor if overrideColor != None else color

        for item in self._canvas_items:
            canvas.delete(item)

        def mirror_x(pt) -> tuple[float,float]:
            return pt[0]*-1, pt[1]

        def offset(pt) -> tuple[float,float]:
            x,y = pt[0], pt[1]
            x += TREE_PREVIEW_SIZE[0] * 0.5
            y *= -1
            y += TREE_PREVIEW_SIZE[1]
            y -= GROUND_OFFSET
            return x,y

        origin = (
            TREE_PREVIEW_SIZE[0] * 0.5, # X
            TREE_PREVIEW_SIZE[1] - GROUND_OFFSET, # Y
        )

        trunk_verts = self.generate_trunk_profile()
        trunk_verts += [mirror_x(pt) for pt in reversed(trunk_verts)]
        trunk_verts = [offset(pt) for pt in trunk_verts]

        if ignore_transforms is False:
            trunk_verts = [rotate_from_2d_point(*pt, *origin, self.transform_rotation_tilt) for pt in trunk_verts]

        line_width = 1
        antialias = 0.5
        for id in range(0, len(trunk_verts) - 1):
            self._canvas_items.append(canvas.create_line(
                *trunk_verts[id],
                *trunk_verts[id+1],
                width=line_width,
                fill=checkOverrideColor('#654321')
            ))
            # antialias line needs color multiplication with background
            # self.canvas_items.append(self.canvas.create_line(
            #     *trunk_verts[id],
            #     *trunk_verts[id+1],
            #     width=line_width + antialias,
            #     fill=checkOverrideColor('#654321')
            # ))


        foliage_verts = self.generate_foliage_profile()
        foliage_verts += [mirror_x(v) for v in reversed(foliage_verts)]
        foliage_verts = [offset(v) for v in foliage_verts]
        if ignore_transforms is False:
            foliage_verts = [rotate_from_2d_point(*pt, *origin, self.transform_rotation_tilt) for pt in foliage_verts]
        
        for id in range(0, len(foliage_verts) - 1):
            self._canvas_items.append(canvas.create_line(
                *foliage_verts[id],
                *foliage_verts[id+1],
                width=line_width,
                fill=checkOverrideColor(UIColors.green.path)
            ))
            # self.canvas_items.append(self.canvas.create_line(
            #     *foliage_verts[id],
            #     *foliage_verts[id+1],
            #     width=line_width + antialias,
            #     fill=checkOverrideColor(UIColors.green.path)
            # ))

        '''Draw initial foliage starting point'''
        # self._canvas_items.append(canvas.create_oval(
        #     foliage_verts[0][0] - 4,
        #     foliage_verts[0][1] - 4,
        #     foliage_verts[0][0] + 4,
        #     foliage_verts[0][1] + 4,
        #     fill=checkOverrideColor('white')
        # ))

        '''Draw foliage mid line'''
        # self._canvas_items.append(self._canvas.create_line(
        #     (0.0, TREE_PREVIEW_SIZE[1] - self.orig_midpoint - ground_offset),
        #     (TREE_PREVIEW_SIZE[0], TREE_PREVIEW_SIZE[1] - self.orig_midpoint - ground_offset),
        #     width=line_width,
        #     fill=checkOverrideColor('#AAA')
        # ))

        '''Draw flat ground plane'''
        self._canvas_items.append(canvas.create_line(
            (0.0, TREE_PREVIEW_SIZE[1] - GROUND_OFFSET),
            (TREE_PREVIEW_SIZE[0], TREE_PREVIEW_SIZE[1] - GROUND_OFFSET),
            width=line_width,
            fill=checkOverrideColor('#AAA')
        ))

    def export_3d_model(self):
        pass