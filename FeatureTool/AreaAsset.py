from enum import Enum
import json
from pathlib import Path
import tkinter as tk
from tkinter import Canvas, Frame, Label, StringVar
from tkinter import ttk
from turtle import pos
from PIL import Image, ImageDraw
from cv2 import line
from matplotlib.pyplot import fill
from TransformUtil import transform_util
from InspectorDrawers import inspector_drawers
from LoadedAsset import loaded_asset
from Utilities import color_set, coord_mode, ui_colors


class settings_keys:
    fill_alpha = "fill_alpha"
    stroke_width = "stroke_width"
    color = "color"
    _color_path = "color_path"
    _color_fill = "color_fill"

class area_asset:    
    def __init__(self, name:str, target:loaded_asset) -> None:
        self.name = name
        self.is_dirty = False
        self.canvasIDs = []
        self.inspectorIDs = []
        self.canvas = None
        self.drawer = None
        self.util = None
        self.do_draw_fill = False
        self.possible_line = None
        self.is_fully_init = False
        self.fill_img:Image.Image = None

        basepath = "SavedAreas/" + target.savename + "/" 


        self._settings_path = Path(basepath + name + "_settings.txt")
        if self._settings_path.is_file():
            with self._settings_path.open('r') as file:
                self.settings:dict = json.loads(file.read())
                
                path = self.settings.pop(settings_keys._color_path)
                fill = self.settings.pop(settings_keys._color_fill)
                self.settings[settings_keys.color] = color_set(path, fill)
        else:
            self.settings = {}
            self.settings[settings_keys.fill_alpha] = 0.25
            self.settings[settings_keys.stroke_width] = 3.0
            self.settings[settings_keys.color] = ui_colors.indigo
            self.__save_settings()

        self.fill_alpha = 0.25
        self.stroke_width = 3.0
        self.color = ui_colors.indigo

        self._stroke_filepath = Path(basepath + name + "_area.csv")
        self.coord_id:coord_mode = coord_mode.normalized
        self.stroke_data = []

        if self._stroke_filepath.is_file():
            with open(str(self._stroke_filepath), 'r') as file:
                lines = file.read().splitlines()
                
                for id, line in enumerate(lines):
                    if id == 0:
                        continue

                    # Convert nonheader lines to tuple
                    # and add to the raw data
                    self.stroke_data.append(eval(line))

        self.fill_img:Image = None
        self._fill_img_filepath = Path(basepath + name + "_fill.tif")
        if self._fill_img_filepath.is_file():
            self.fill_img = Image.open(self._fill_img_filepath)

    def __save_settings(self):
        settings = dict(self.settings)
        color:color_set = settings.pop(settings_keys.color)
        settings[settings_keys._color_path] = color.path
        settings[settings_keys._color_fill] = color.fill

        with self._settings_path.open('w') as file:
            # color_set is not json compatible
            settings_str = json.dumps(settings)
            file.write(settings_str)
        
    def save_data_to_files(self):
        # if self.is_dirty == False:
        #     return

        with self._stroke_filepath.open('r') as file:
            header = file.readline()

        with open(str(self._stroke_filepath), 'w') as file:
            file.write(header + '\n')

            # Write stroke data
            for id, item in enumerate(self.stroke_data):
                file.write(str(item))
                if id - 1 != len(self.stroke_data):
                    file.write('/n')
        
        self.is_dirty = False
    
    def drawing_init(self, canvas:Canvas, util:transform_util, img_size:tuple):
        self.is_fully_init = True

        self.canvas = canvas
        self.util = util
        self.img_size = img_size


    # -------------------------------------------------------------- #
    # --- Wrappers for stroke_data --------------------------------- #
    def modify_point(self, id:int, position:tuple):
        self.stroke_data[id] = position
        self.is_dirty = True
        self.draw_inspector()

    def insert_point(self, position:tuple):
        self.stroke_data.insert(position)
        self.is_dirty = True
        self.draw_inspector()

    def append_point(self, position:tuple, coordID:coord_mode):
        if (coordID == coord_mode.pixel):
            position = self.util.pixel_pt_to_norm_space(position)

        self.stroke_data.append(position)
        self.is_dirty = True
        self.draw_inspector()

    def remove_point(self, id:int):
        self.stroke_data.pop(id)
        self.is_dirty = True
        self.draw_inspector()

        
    # -------------------------------------------------------------- #
    # --- Utility functions ---------------------------------------- #
    def is_point_in_area(self, pt:tuple, coord_id:coord_mode) -> bool:
        '''
        This method checks if a point is within an
        irregular polygon is directly tied to the satellite
        image's dimensions. This should be replaced with an
        independent method later

        Bandaid solutions to refine edges would be to:
            [a] supersize the image  
            [b] average the value of surrounding pixels since getpixel() uses an int and not a float
        '''
        if self.fill_img is None:
            self.draw_fill(export_to_img=True)

        if coord_id is coord_mode.pixel:
            pass
        elif coord_id is coord_mode.earth:
            pt = self.util.earth_pt_to_pixel_space(pt, to_int=True)
        elif coord_id is coord_mode.normalized:
            pt = self.util.norm_pt_to_pixel_space(pt, to_int=True)

        # Check only the red channel
        return self.fill_img.getpixel(pt)[0] > 128

    def get_points(self) -> list[tuple[float,float]]:
        points:list[tuple[float,float]]
        points.append((0.25, 0.25)) 
        points.append((0.55, 0.25)) 
        points.append((0.25, 0.55))

        print("area_asset.get_points() => not implemented")
        return points

    def destroy(self):
        pass

    # -------------------------------------------------------------- #
    # --- Canvas functions ----------------------------------------- #
    def draw(self):
        self.clear_canvasIDs()

        if self.do_draw_fill is True:
            self.draw_fill(export_to_img=True)
        
        self.draw_perimeter()

    def draw_perimeter(self):
        if self.is_fully_init is False:
            raise Exception("{} is not fully initiated, call drawing_init()")

        data = self.stroke_data
        img_size = self.img_size
        util = self.util

        # Draw fill (do later)
        # Draw lines
        if len(data) > 2:
            for id in range(0, len(data) - 1):
                pt_a = data[id+0][0] * img_size[0], data[id+0][1] * img_size[1]
                pt_b = data[id+1][0] * img_size[0], data[id+1][1] * img_size[1]
                lineID = self.canvas.create_line(*pt_a, *pt_b, width=self.stroke_width, fill=self.color.path)
                self.canvasIDs.append(lineID)


        pt_a = data[0][0] * img_size[0], data[0][1] * img_size[1]
        pt_b = data[-1][0] * img_size[0], data[-1][1] * img_size[1]

        lineID = self.canvas.create_line(*pt_a, *pt_b, width=self.stroke_width, fill=self.color.path, dash=(6,4))
        self.canvasIDs.append(lineID)

        # Draw points
        circle_size = 8
        for point in self.stroke_data:
            pt_a = point[0] * img_size[0], point[1] * img_size[1]
            pointID = self.canvas.create_oval(util.point_to_size_coords((pt_a), circle_size), fill=self.color.path)
            self.canvasIDs.append(pointID)

    def draw_last_point_to_cursor(self, cursor_pos:tuple):
        data = self.stroke_data
        img_size = self.img_size

        self.destroy_possible_line()

        # Draw dotted line to cursor
        if len(data) > 0:
            pt_a = data[-1][0] * img_size[0], data[-1][1] * img_size[1]
            pt_b = cursor_pos[0] + self.canvas.canvasx(0), cursor_pos[1] + self.canvas.canvasy(0)
            lineID = self.canvas.create_line(*pt_a, *pt_b, width=2, fill='white', dash=(6,4))
            self.possible_line = lineID

    def destroy_possible_line(self, *args, **kwargs):
        if self.possible_line != None:
            self.canvas.delete(self.possible_line)
            self.possible_line = None



    def on_select(self):
        pass

    def on_deselect(self):
        self.destroy_possible_line()

    def clear_canvasIDs(self):
        if self.canvas == None:
            return

        for item in self.canvasIDs:
            self.canvas.delete(item)

        self.canvasIDs.clear()

    def toggle_fill(self):
        self.do_draw_fill = not self.do_draw_fill
        self.draw()

    def draw_fill(self, export_to_img=False):
        polygon_points = []
        for pt in self.stroke_data:
            pixel_pt = self.util.norm_pt_to_pixel_space(pt)
            polygon_points.append(pixel_pt[0])
            polygon_points.append(pixel_pt[1])


        if export_to_img is True:
            bgm_xy_coords = [
                *self.util.norm_pt_to_pixel_space((0.0, 0.0)),
                *self.util.norm_pt_to_pixel_space((0.0, 1.0)),
                *self.util.norm_pt_to_pixel_space((1.0, 1.0)),
                *self.util.norm_pt_to_pixel_space((1.0, 0.0))
            ]

            for id in range(len(bgm_xy_coords)):
                if bgm_xy_coords[id] > 5:
                    bgm_xy_coords[id] += 1


            img_size = self.util.norm_pt_to_pixel_space((1.0, 1.0))
            img_size = (
                (int)(img_size[0]),
                (int)(img_size[1])
            )

            fill_img = Image.new("RGBA", img_size, (255, 255, 255, 1))
            drawer = ImageDraw.Draw(fill_img)
            drawer.polygon(bgm_xy_coords, fill="black")
            drawer.polygon(polygon_points, fill="white")

            fill_img.save(self._fill_img_filepath)
            self.fill_img = fill_img
            

        polygonID = self.canvas.create_polygon(polygon_points, fill=self.color.fill)
        self.canvasIDs.append(polygonID)


    # -------------------------------------------------------------- #
    # --- Inspector functions -------------------------------------- #
    def draw_inspector(self, drawer:inspector_drawers=None):
        if drawer is not None:
            self.drawer = drawer

        if self.drawer is None:
            raise Exception("Trying to draw inspector without being fully initialized")

        self.drawer.clear_inspector()
        self.drawer.header(text="Settings")

        placeholder = StringVar()
        placeholder.set("Entry Text")
        self.drawer.labeled_entry(label_text="Example", entryVariable=placeholder)
        
        
        self.drawer.button(text="Toggle Fill", command=self.toggle_fill)
        self.drawer.seperator()

        self.drawer.header(text="Statistics")
        self.drawer.label("Perimeter Point count: {}".format(len(self.stroke_data)))
        self.drawer.label("Area point count: {}".format("N/A"))
        self.drawer.label("Area size: {}".format(0))
        self.drawer.label("Bounds: NW: {}, {}".format(0.5, 0.5))
        self.drawer.label("Bounds: NE: {}, {}".format(0.5, 0.5))
        self.drawer.seperator()

        self.drawer.header(text="Actions")
        self.drawer.button(text="Sample Elevation")
        self.drawer.button(text="Delete area", command=self.draw_delete_popup)

    def draw_delete_popup(self):
        popup = tk.Toplevel()
        popup.grab_set()
        popup.focus_force()
        popup.title("Warning")
        popup.resizable(False, False)

        warning = Label(popup, text="This action cannot be undone!\nAre you sure you want to delete:\n\n{}".format(self.name), padx=60, pady=20)
        warning.grid(row=0, column=0, columnspan=2)

        cancel = ttk.Button(popup, text="Cancel", command=popup.destroy)
        cancel.grid(row=1, column=0, sticky='ew', padx=10)

        delete = ttk.Button(popup, text="Delete", command=self.destroy())
        delete.grid(row=1, column=1, sticky='ew', padx=10)

        deadspace = Label(popup, text="")
        deadspace.grid(row=2)