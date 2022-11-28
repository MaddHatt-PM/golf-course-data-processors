from math import cos, pi, sin
from pathlib import Path
from functools import partial

import tkinter as tk
from tkinter import Canvas, DoubleVar, Frame, StringVar
from tkinter import ttk

from utilities.math import rotate_from_2d_point

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
        self.canvas:Canvas = None
        self.util:SpaceTransformer = None

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

    def setup_draw_to_viewport(self, canvas:Canvas, util:SpaceTransformer=None):
        self.canvas = canvas
        self.util = util

    def draw_to_viewport(self):
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

            for i in range(len(foliage_pts) - 1):
                lineID = self.canvas.create_line(
                    *foliage_pts[i],
                    *foliage_pts[i+1],
                    width=2.5,
                    fill='white'
                    )
                self.canvas_ids.append(lineID)

            lineID = self.canvas.create_line(
                *foliage_pts[-1],
                *foliage_pts[0],
                width=2.5,
                fill='white'
                )
            self.canvas_ids.append(lineID)


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