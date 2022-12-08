"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022
"""

from math import cos, pi, sin
from pathlib import Path
from functools import partial

import tkinter as tk
from tkinter import Canvas, Frame, StringVar, messagebox
from tkinter import ttk

from utilities.math import rotate_from_2d_point
from copy import copy

from asset_project import LocationPaths
from subviews import InspectorDrawer
from utilities import SpaceTransformer
from data_assets import TreeAsset

class TreeCollectionManager:
    def __init__(self, target:LocationPaths) -> None:
        self.target = target
        self.trees:list[TreeAsset] = []
        self.load_data_from_file()

        self.active_tree_title:StringVar = StringVar()
        self.active_tree_title.set("None selected")
        self.active_tree:TreeAsset = None
        self.default_tree:TreeAsset = TreeAsset()
        self.tree_dropdown = None
        self.is_active_tool = False
        # if len(self.trees) == 0:
        #     self.trees.append(TreeAsset())

        def redraw_func():
            self.draw_to_inspector()
            self.draw_to_viewport()

        def set_default_tree(tree:TreeAsset):
            self.default_tree = copy(tree)

        if len(self.trees) > 0:
            self.active_tree = self.trees[0]
            self.active_tree.select(self, redraw_func, set_default_tree)

        self.presets_path = Path("resources/tree_presets.csv")
        self.presets:list[TreeAsset] = []

        self.canvas_ids = []
        self.canvas:Canvas = None
        self.util:SpaceTransformer = None
        self.drawer = None
        self.inspector = None

        if self.presets_path.is_file() is True:
            with self.presets_path.open('r') as file:
                lines = file.readlines()
                header = lines.pop(0)
                for line in lines:
                    self.presets.append(TreeAsset(header, line))

    def set_active_tool(self, state:bool):
        self.is_active_tool = state

    def load_data_from_file(self):
        if self.target.trees_csv_path.is_file():
            with self.target.trees_csv_path.open('r') as file:
                treedata = file.readlines()
                header = treedata.pop(0).replace('\n', '')

                for tree_str in treedata:
                    self.trees.append(TreeAsset(header=header, data=tree_str))

    def save_data_to_files(self):
        with self.target.trees_csv_path.open('w') as file:
            output = TreeAsset().generate_header() + '\n'

            for tree in self.trees:
                output += tree.to_csv() + '\n'

            output = output.removesuffix('\n')
            file.write(output)

    # -------------------------------------------------------------- #
    # --- TODO Rename -------------------------------------------------- #

    def add_tree(self):
        tree = TreeAsset()
        tree.copy_from(self.default_tree)
        self.trees.append(tree)
        self.active_tree.deselect()
        self.active_tree = tree

        def redraw_func():
            self.draw_to_inspector()
            self.draw_to_viewport()

        def set_default_tree(tree:TreeAsset):
            self.default_tree = copy(tree)

        self.active_tree.select(self, redraw_func, set_default_tree)
            
        self.save_data_to_files()
        self.draw_to_inspector()
        self.draw_to_viewport()

    def remove_tree(self, tree:TreeAsset):
        if messagebox.askokcancel("Delete Tree?", "Are you sure you want to delete this tree"):
            self.trees.remove(tree)
            self.active_tree = self.trees[-1] if len(self.trees) != 0 else None
            self.save_data_to_files()
            self.draw_to_inspector()
            self.draw_to_viewport()

    def move_tree_on_right_click(self, x, y):
        if self.active_tree is not None:
            self.active_tree.move_tree_to_point(x, y)

    def setup_draw_to_viewport(self, canvas:Canvas, util:SpaceTransformer=None):
        self.canvas = canvas
        self.util = util

    def draw_to_viewport(self):
        """
        Draw to the main viewport canvas
        """
        for id in self.canvas_ids:
            self.canvas.delete(id)
        self.canvas_ids.clear()

        for tree in self.trees:
            pos = tree.transform_position_x, tree.transform_position_y
            pos = self.util.norm_pt_to_pixel_space(pos)

            sample_count = 64
            def sin_lerp(start:float, end:float, val01:float):
                return start + sin(val01 * pi * 0.5) * (end - start)

            radius = max(tree.trunk_radius, tree.foliage_radius)
            straight_pts = []
            for i in range(sample_count):
                pt = (
                    sin(i/sample_count * 2 * pi) * radius,
                    cos(i/sample_count * 2 * pi) * radius,
                )
                # pt = self.util.norm_pt_to_pixel_space(pt)
                pt = (
                    pt[0] + pos[0],
                    pt[1] + pos[1],
                )
                straight_pts.append(pt)

            # tipped_pts = [ (pt[0], pt[1] + 50) for pt in straight_pts]
            tipped_pts = tree.generate_foliage_profile(samples=sample_count / 2 + 1)
            tipped_pts = list(reversed(tipped_pts))
            def mirror_x(pt) -> tuple[float,float]:
                return pt[0]*-1, pt[1]
            tipped_pts += [mirror_x(pt) for pt in reversed(tipped_pts)]
            tipped_pts = [
                (
                    pt[0]-tipped_pts[0][0] + pos[0],
                    pt[1]-tipped_pts[0][1] + pos[1] + tree.foliage_offset + tree.foliage_height,
                )
                for pt in tipped_pts]

            foliage_pts = []
            for i in range(sample_count):
                pt = (
                    sin_lerp(straight_pts[i][0], tipped_pts[i][0], tree.transform_rotation_tilt / 90.0),
                    sin_lerp(straight_pts[i][1], tipped_pts[i][1], tree.transform_rotation_tilt / 90.0),
                )
                foliage_pts.append(pt)
                
            foliage_pts = [rotate_from_2d_point(*pt, *pos, tree.transform_rotation_spin) for pt in foliage_pts]

            # Draw Dots
            # for pt in foliage_pts:
            #     circle_pt = self.canvas.create_oval(self.util.point_to_size_coords(pt, 8), fill="white")
            #     self.canvas_ids.append(circle_pt)
            def draw_foliage(pts, color='white'):
                for i in range(len(pts) - 1):
                    line_id = self.canvas.create_line(
                        *pts[i],
                        *pts[i+1],
                        width=2.5,
                        fill=color
                        )
                    self.canvas_ids.append(line_id)

                line_id = self.canvas.create_line(
                    *pts[-1],
                    *pts[0],
                    width=2.5,
                    fill=color
                    )
                self.canvas_ids.append(line_id)

            if self.active_tree == tree and self.is_active_tool:
                pixel_offset = 3
                drop_shadow_pts = [(pt[0], pt[1] + pixel_offset) for pt in foliage_pts]
                draw_foliage(drop_shadow_pts, color='#212121')
                draw_foliage(foliage_pts, color='#EFEBE9')
            
            else:
                draw_foliage(foliage_pts, color='#BDBDBD')


            # Draw radius (solid circle)
            # radius = max(tree.trunk_radius, tree.foliage_radius)
            # radius_cords = (
            #     pos[0] - radius,
            #     pos[1] - radius,
            #     pos[0] + radius,
            #     pos[1] + radius
            # )
            # radius_id = self.canvas.create_oval(*radius_cords, fill="blue")
            # self.canvas_ids.append(radius_id)

            # Draw center point
            center_id = self.canvas.create_oval(self.util.point_to_size_coords(pos, 8), fill="white")
            self.canvas_ids.append(center_id)

            # Draw initial radius point
            center_id = self.canvas.create_oval(self.util.point_to_size_coords(foliage_pts[0], 8), fill="white")
            self.canvas_ids.append(center_id)

    def draw_to_inspector(self, inspector:Frame=None, drawer:InspectorDrawer=None, force_selector_draw=False):
        '''
        Mockup:
        
        canvasSelect:Button | trees:Dropdown | new_tree:Button
        sub_canvas renderer
        '''
        if self.inspector is None and inspector is None:
            print("inspector must be supplied at least once")
        
        if inspector is None:
            inspector = self.inspector
        self.inspector = inspector

        if self.drawer is None and drawer is None:
            print("inspector must be supplied at least once")
        
        if drawer is None:
            drawer = self.drawer
        self.drawer = drawer


        tree_dropdown_options = []
        for id, tree in enumerate(self.trees):
            result = "[{}] {:.4f}, {:.4f}".format(id, tree.transform_position_x, tree.transform_position_y)
            tree_dropdown_options.append(result)

        def select_tree_from_dropdown(choice:str, do_rerender=True):
            def redraw_func():
                self.draw_to_inspector()
                self.draw_to_viewport()
                
            def set_default_tree(tree:TreeAsset):
                self.default_tree = copy(tree)
            
            tree_id = int(choice[1:choice.index(']')])
            self.active_tree.deselect()
            self.active_tree = self.trees[tree_id]
            self.active_tree.select(self, redraw_func, set_default_tree)
            
            if do_rerender:
                self.draw_to_inspector()
                self.draw_to_viewport()

        if (self.active_tree_title.get() == "None selected" and len(self.trees) != 0):
            select_tree_from_dropdown(tree_dropdown_options[0], do_rerender=False)
            self.active_tree_title.set(tree_dropdown_options[0])

        if len(self.trees) == 0:
            self.active_tree_title.set("None selected")

        if self.tree_dropdown is None or force_selector_draw:
            selector_frame = Frame(inspector, padx=0, pady=0)
            tk.Label(selector_frame, text="Tree:").grid(row=0, column=0)

            self.tree_dropdown = ttk.OptionMenu(
                selector_frame,
                self.active_tree_title,
                self.active_tree_title.get(),
                *tree_dropdown_options,
                command=select_tree_from_dropdown
                )
            
            self.tree_dropdown.grid(row=0, column=1, sticky='ew')

            remove_func = partial(self.remove_tree, self.active_tree)
            # ttk.Button(selector_frame, text='⦺', width=2).grid(row=0, column=2)
            ttk.Button(selector_frame, text='+', width=2, command=self.add_tree).grid(row=0, column=3)
            ttk.Button(selector_frame, text='-', width=2, command=remove_func).grid(row=0, column=4)

            selector_frame.grid_columnconfigure(1, weight=5)
            selector_frame.pack(fill="x", anchor="n", expand=False)
        # ttk.Label(selector_frame, textvariable=self.selected_tree_text, anchor="e").grid(row=0, column=1)


        if self.active_tree is not None:
            drawer.seperator()
            self.active_tree.draw_to_inspector(inspector, drawer)

        # drawer.empty_space()
        # drawer.button(text="Save all trees", command=self.save_data_to_files)