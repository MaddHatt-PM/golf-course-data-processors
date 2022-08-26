from functools import partial
import json
from pathlib import Path
import tkinter as tk
from tkinter import BooleanVar, Canvas, DoubleVar, Frame, IntVar, Label, StringVar
from tkinter import ttk
from tkinter.messagebox import askyesno
from typing import Tuple
from PIL import Image, ImageDraw, ImageTk, ImageColor
from utilities import SpaceTransformer
from ui_inspector_drawer import inspector_drawers
from asset_project import ProjectAsset
from utilities import ColorSet, CoordMode, UIColors

from geographiclib.geodesic import Geodesic
from geographiclib.polygonarea import PolygonArea

class Settings:
    '''
    TODO: Think of a nicer way to handle settings
            - Data class paired with a store to handle fileio?
    '''
    fill_alpha = "fill_alpha"
    stroke_width = "stroke_width"
    do_draw_points = "do_draw_points"
    do_draw_fill = "do_draw_fill"
    overfill_amt = "overfill_amt"
    color = "color"

    _color_path = "color_path"
    _color_fill = "color_fill"

HEADER = "latitude,longitude,elevation,resolution\n"

class AreaAsset:
    def __init__(self, name:str, target:ProjectAsset, app_settings) -> None:
        self.name = name
        self.is_dirty = False
        self.is_fill_dirty = True
        self.canvasIDs = []
        self.canvas = None
        self.drawer = None
        self.util = None
        self.is_active_area = False
        self.was_deleted = False
        self.app_settings = app_settings

        self.possible_line = None
        self.is_fully_init = False
        self.fill_img:Image.Image = None
        self.canvasID_fill = None
        self.target = target

        basepath = "SavedAreas/" + target.savename + "/"

        self._settings_path = Path(basepath + name + "_settings.txt")
        if self._settings_path.is_file():
            with self._settings_path.open('r') as file:
                self.settings:dict = json.loads(file.read())
                
                path = self.settings.pop(Settings._color_path)
                fill = self.settings.pop(Settings._color_fill)
                self.settings[Settings.color] = ColorSet(path, fill)
        else:
            self.settings = {}
            self.settings[Settings.fill_alpha] = 0.5
            self.settings[Settings.stroke_width] = 3.0
            self.settings[Settings.color] = UIColors.indigo
            self.settings[Settings.overfill_amt] = 0
            self.settings[Settings.do_draw_fill] = True
            self.settings[Settings.do_draw_points] = True
            self._save_settings()

        # self.fill_alpha = 0.25
        self.stroke_width = 3.0

        self._stroke_filepath = Path(basepath + name + "_area.csv")
        self.coord_id:CoordMode = CoordMode.normalized
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
        self._fill_img_filepath = Path(basepath + name + "_fill.png")
        self._mask_img_filepath = Path(basepath + name + '_mask.png')
        if self._fill_img_filepath.is_file():
            self.fill_img = Image.open(self._fill_img_filepath)

    def _save_settings(self):
        settings = dict(self.settings)
        
        # color_set is not json compatible
        color:ColorSet = settings.pop(Settings.color)
        settings[Settings._color_path] = color.path
        settings[Settings._color_fill] = color.fill

        with self._settings_path.open('w') as file:
            settings_str = json.dumps(settings)
            file.write(settings_str)
        
    def save_data_to_files(self):
        with open(str(self._stroke_filepath), 'w') as file:
            csv_header = "latitude,longitude,elevation,resolution\n"
            file.write(csv_header)

            # Write stroke data
            for id, item in enumerate(self.stroke_data):
                file.write(str(item).removeprefix('(').removesuffix(')'))
                if id - 1 != len(self.stroke_data):
                    file.write('\n')
        
        self._save_settings()
        self.is_dirty = False
    
    def drawing_init(self, canvas:Canvas, util:SpaceTransformer, img_size:tuple):
        self.is_fully_init = True

        self.canvas = canvas
        self.util = util
        self.img_size = img_size

    def mark_as_deleted(self):
        delete_msg = "Deleting this area will send associated files to trash.\n"
        delete_msg += "To undo, restore the files back to the project and restart."

        if askyesno(title="Delete area?", message=delete_msg):
            self.was_deleted = True
            self.finish_delete()
            self.mark_area_to_be_redrawn()

    def finish_delete(self):
        self._stroke_filepath.unlink(missing_ok=True)
        self._settings_path.unlink(missing_ok=True)
        self._fill_img_filepath.unlink(missing_ok=True)
        self._mask_img_filepath.unlink(missing_ok=True)

    def get_lat_long(self) -> tuple[list[float], list[float]]:
        lat, long = [], []
        for pt in self.stroke_data:
            pt = self.util.norm_pt_to_earth_space(pt)
            lat.append(pt[0])
            long.append(pt[1])

        return (lat, long)

    # -------------------------------------------------------------- #
    # --- Wrappers for stroke_data --------------------------------- #
    def modify_point(self, id:int, position:tuple):
        self.stroke_data[id] = position
        self.mark_area_to_be_redrawn()

    def insert_point(self, position:tuple):
        self.stroke_data.insert(position)
        self.mark_area_to_be_redrawn()

    def append_point(self, position:tuple, coordID:CoordMode):
        if (coordID == CoordMode.pixel):
            position = self.util.pixel_pt_to_norm_space(position)

        self.stroke_data.append(position)
        self.mark_area_to_be_redrawn()

    def remove_point(self, id:int=-1):
        self.stroke_data.pop(id)
        self.mark_area_to_be_redrawn()

    def clear_points(self):
        self.stroke_data.clear()
        self.mark_area_to_be_redrawn()

    def mark_area_to_be_redrawn(self):
        self.is_dirty = True
        self.is_fill_dirty = True
        self.draw_to_canvas()
        self.draw_to_inspector()


    # -------------------------------------------------------------- #
    # --- Utility functions ---------------------------------------- #
    def is_point_in_area(self, pt:tuple, coord_id:CoordMode) -> bool:
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
            self.is_fill_dirty = True
            self.__draw_fill()

        if coord_id is CoordMode.pixel:
            pass
        elif coord_id is CoordMode.earth:
            pt = self.util.earth_pt_to_pixel_space(pt, to_int=True)
        elif coord_id is CoordMode.normalized:
            pt = self.util.norm_pt_to_pixel_space(pt, to_int=True)

        # Check only the red channel
        return self.fill_img.getpixel(pt)[0] > 1

    def get_points(self) -> list[tuple[float,float]]:
        points:list[tuple[float,float]]
        points.append((0.25, 0.25)) 
        points.append((0.55, 0.25)) 
        points.append((0.25, 0.55))

        print("area_asset.get_points() => not implemented")
        return points

    def compute_info(self):
        geo:Geodesic = Geodesic.WGS84
        polygon = PolygonArea(geo, False)

        for pt in self.stroke_data:
            _pt = self.util.norm_pt_to_earth_space(pt)
            # Order: LAT, Long
            polygon.AddPoint(_pt[0], _pt[1])

        '''
        Counterclockwise and clockwise return different results.
        Return lowest to counter user input
        '''
        return min(polygon.Compute(False, False), polygon.Compute(True, False))

    def get_polygonArea(self) -> PolygonArea:
        geo:Geodesic = Geodesic.WGS84
        polygon = PolygonArea(geo, False)

        for pt in self.stroke_data:
            _pt = self.util.norm_pt_to_earth_space(pt)
            # Order: LAT, Long
            polygon.AddPoint(_pt[0], _pt[1])

        return polygon

    
    def get_bounds(self) -> Tuple[float,float,float,float]:
        '''
        NW -> MaxMin
        SE -> MinMax
        '''
        n,w = float("-inf"), float("inf")
        s,e = float("inf"), float("-inf")

        for pt in self.stroke_data:
            n,w = max(n, pt[0]), min(w, pt[1])
            s,e = min(s, pt[0]), max(e, pt[1])

        return n,w,s,e

    def destroy(self):
        pass


    # -------------------------------------------------------------- #
    # --- Canvas functions ----------------------------------------- #
    def draw_to_canvas(self):
        self.clear_canvasIDs()

        if self.was_deleted:
            if self.canvasID_fill is not None:
                self.canvas.delete(self.canvasID_fill)
                self.canvasID_fill = None
            return

        
        if self.app_settings.fill_only_active_area.get() is True:
            if self.is_active_area:
                self.__draw_fill()
            else:
                self.fill_img = None
                self.image_pi = None

        elif self.settings.get('do_draw_fill', False) is True:
            self.__draw_fill()
            
        self.__draw_perimeter()
    
    def make_masks(self):
        self.__draw_fill(asMask=True)

    def __draw_perimeter(self):
        if self.is_fully_init is False:
            raise Exception("{} is not fully initiated, call drawing_init()")

        data = self.stroke_data
        img_size = self.img_size
        util = self.util

        if len(data) >= 2:
            '''Draw drop shadow if the area is selected'''
            if (self.is_active_area):
                offset_x, offset_y = 2, 3
                path_color = ImageColor.getcolor(self.settings['color'].path, 'RGB')
                mult_color = ImageColor.getcolor('#37474F', 'RGB')
                drop_color = (
                    int ((path_color[0] / 255.0) * (mult_color[0] / 255.0) * 255),
                    int ((path_color[1] / 255.0) * (mult_color[1] / 255.0) * 255),
                    int ((path_color[2] / 255.0) * (mult_color[2] / 255.0) * 255)
                )
                drop_color = '#' + '%02x%02x%02x' % drop_color

                for id in range(0, len(data) - 1):
                    pt_a = data[id+0][0] * img_size[0] + offset_x / 2, data[id+0][1] * img_size[1] + offset_y
                    pt_b = data[id+1][0] * img_size[0] + offset_x / 2, data[id+1][1] * img_size[1] + offset_y
                    lineID = self.canvas.create_line(*pt_a, *pt_b, width=self.stroke_width, fill=drop_color)
                    self.canvasIDs.append(lineID)

                pt_a = data[0][0] * img_size[0], data[0][1] * img_size[1]
                pt_b = data[-1][0] * img_size[0], data[-1][1] * img_size[1]

                lineID = self.canvas.create_line(*pt_a, *pt_b, width=self.stroke_width, fill='#424242', dash=(6,4))
                self.canvasIDs.append(lineID)

            '''Draw unselected lines'''
            for id in range(0, len(data) - 1):
                pt_a = data[id+0][0] * img_size[0], data[id+0][1] * img_size[1]
                pt_b = data[id+1][0] * img_size[0], data[id+1][1] * img_size[1]
                lineID = self.canvas.create_line(*pt_a, *pt_b, width=self.stroke_width, fill=self.settings['color'].path)
                self.canvasIDs.append(lineID)

            pt_a = data[0][0] * img_size[0], data[0][1] * img_size[1]
            pt_b = data[-1][0] * img_size[0], data[-1][1] * img_size[1]

            lineID = self.canvas.create_line(*pt_a, *pt_b, width=self.stroke_width, fill=self.settings['color'].path, dash=(6,4))
            self.canvasIDs.append(lineID)

            for id in range(0, len(data) - 1):
                pt_a = data[id+0][0] * img_size[0], data[id+0][1] * img_size[1]
                pt_b = data[id+1][0] * img_size[0], data[id+1][1] * img_size[1]
                lineID = self.canvas.create_line(*pt_a, *pt_b, width=self.stroke_width, fill=self.settings['color'].path)
                self.canvasIDs.append(lineID)

            pt_a = data[0][0] * img_size[0], data[0][1] * img_size[1]
            pt_b = data[-1][0] * img_size[0], data[-1][1] * img_size[1]

            lineID = self.canvas.create_line(*pt_a, *pt_b, width=self.stroke_width, fill=self.settings['color'].path, dash=(6,4))
            self.canvasIDs.append(lineID)

        '''Draw points'''
        if self.settings['do_draw_points'] and self.is_active_area:
            circle_size = 8
            for point in self.stroke_data:
                pt_a = point[0] * img_size[0], point[1] * img_size[1]
                pointID = self.canvas.create_oval(util.point_to_size_coords((pt_a), circle_size), fill=self.settings['color'].path)
                self.canvasIDs.append(pointID)

    def __draw_fill(self, asMask=False):
        polygon_points = []
        for pt in self.stroke_data:
            pixel_pt = self.util.norm_pt_to_pixel_space(pt)
            polygon_points.append(pixel_pt[0])
            polygon_points.append(pixel_pt[1])

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

        if len(polygon_points) > 2:
            if self.is_fill_dirty is True or asMask is True:

                fill = ImageColor.getcolor(self.settings['color'].fill, 'RGB')
                alpha = int(self.settings['fill_alpha'] * 255)
                color = (*fill, alpha)
                background = (255,255,255, 0)
                savePath = self._fill_img_filepath
                
                if asMask is True:
                    color = (255,255,255,255) # white
                    background = (0,0,0,255) # black
                    savePath = self._mask_img_filepath

                fill_img = Image.new("RGBA", img_size, background)
                drawer = ImageDraw.Draw(fill_img)

                drawer.polygon(polygon_points, fill=color)
                
                if self.settings.get(Settings.overfill_amt, 0) > 0:
                    '''Overfill - Outline'''
                    width = self.settings.get(Settings.overfill_amt, 0)
                    outline = polygon_points.copy()
                    outline.append(polygon_points[0])
                    outline.append(polygon_points[1])
                    drawer.line(outline, fill=color, width=width, joint="curve")

                    ''' Overfill - Endcaps '''
                    def circle(drawer: ImageDraw.ImageDraw, center, radius, fill):
                        drawer.ellipse(
                            (
                                center[0] - radius + 1, center[1] - radius + 1,
                                center[0] + radius - 1, center[1] + radius - 1
                            ),
                            fill=fill, outline=None
                        )

                    circle(drawer, (polygon_points[0], polygon_points[1]), width/2, color)
                
                fill_img.save(savePath)
                if asMask: return

                self.fill_img = fill_img
                self.is_fill_dirty = False
            
            self.image_pi = ImageTk.PhotoImage(Image.open(self._fill_img_filepath).resize(self.img_size))
            self.canvasID_fill = self.canvas.create_image(self.image_pi.width()/2, self.image_pi.height()/2, anchor=tk.CENTER, image=self.image_pi)

        elif self.canvasID_fill is not None:
            self.canvas.delete(self.canvasID_fill)
            self.canvasID_fill = None


    def draw_last_point_to_cursor(self, cursor_pos:tuple):
        data = self.stroke_data
        img_size = self.img_size

        self.destroy_possible_line()
        
        if self.was_deleted:
            return

        # Draw dotted line to cursor
        if len(data) > 0:
            pt_a = data[-1][0] * img_size[0], data[-1][1] * img_size[1]
            pt_b = cursor_pos[0] + self.canvas.canvasx(0), cursor_pos[1] + self.canvas.canvasy(0)
            self.possible_line = self.canvas.create_line(*pt_a, *pt_b, width=2, fill='white', dash=(6,4))

    def destroy_possible_line(self, *args, **kwargs):
        if self.possible_line != None:
            self.canvas.delete(self.possible_line)
            self.possible_line = None

    def select(self):
        self.is_active_area = True

    def deselect(self):
        self.is_active_area = False
        self.draw_to_canvas()
        self.destroy_possible_line()

    def clear_canvasIDs(self):
        if self.canvas == None:
            return

        for item in self.canvasIDs:
            self.canvas.delete(item)

        self.canvasIDs.clear()

    def set_color(self, color:ColorSet, *args, **kwargs):
        self.settings['color'] = color
        self.is_fill_dirty = True
        self.draw_to_canvas()
        self._save_settings()

    def toggle_fill(self):
        self.settings['do_draw_fill'] = not self.settings['do_draw_fill']

        if self.settings['do_draw_fill'] is False:
            self.fill_img = None
            self.image_pi = None

        self.draw_to_canvas()
        self.draw_to_inspector()

    def toggle_points(self):
        self.settings['do_draw_points'] = not self.settings['do_draw_points']
        self.draw_to_canvas()


    # -------------------------------------------------------------- #
    # --- Inspector functions -------------------------------------- #

    def draw_to_inspector(self, drawer:inspector_drawers=None):
        if drawer is not None:
            self.drawer = drawer

        if self.drawer is None:
            raise Exception("Trying to draw inspector without being fully initialized")

        self.drawer.clear_inspector()

        if self.was_deleted:
            self.drawer.header("Area Deleted - Select new area")
            return

        self.drawer.header(text="Settings")

        self.drawer.labeled_dropdown(
            self.settings['color'],
            value_data=UIColors.colors,
            value_names=UIColors.names,
            default_index=0,
            label_text="Color",
            change_commands=self.set_color)

        do_draw_points = BooleanVar(value=self.settings['do_draw_points'])
        self.drawer.labeled_toggle(
            label_text="Toggle path points",
            command=self.toggle_points,
            boolVar=do_draw_points)

        do_fill = BooleanVar(value=self.settings['do_draw_fill'])
        self.drawer.labeled_toggle(label_text="Toggle fill", command=self.toggle_fill, boolVar=do_fill)

        def sync_variable(self:AreaAsset, var_name:str, tkVar, *args, **kwargs):
            self.settings[var_name] = tkVar.get()
            self.is_fill_dirty = True
            self.draw_to_canvas()

        fill_state = [] if do_fill.get() == True else ['disabled']

        fill_alpha_var = DoubleVar()
        fill_alpha_var.set(self.settings.get(Settings.fill_alpha, 0.2)) 
        fill_alpha_closure = partial(sync_variable, self, Settings.fill_alpha, fill_alpha_var)
        fill_alpha_var.trace_add('write', fill_alpha_closure)
        fill_alpha_ui = self.drawer.labeled_slider("Fill Opacity", tkVar=fill_alpha_var)
        fill_alpha_ui.state(fill_state)

        OVERFILL_MAX = 500
        overfill_var = IntVar()
        overfill_var.set(self.settings.get(Settings.overfill_amt, 0))
        overfill_closure = partial(sync_variable, self, Settings.overfill_amt, overfill_var)
        overfill_var.trace_add('write', overfill_closure)
        overfill_ui = self.drawer.labeled_slider("Overfill", tkVar=overfill_var, from_=0, to=OVERFILL_MAX)
        overfill_ui.state(fill_state)

        self.drawer.seperator()

        area_info = self.compute_info()
        bounds = self.get_bounds()

        self.drawer.header(text="Statistics")
        text = "Point count: {}\n".format(len(self.stroke_data))
        text += "Perimeter (m): {:.4f}\n".format(area_info[1])
        text += "Area (m²): {:.4f}\n".format(area_info[2])
        text += "Bounds: NW: {:.5f}, {:.5f}\n".format(bounds[0], bounds[1])
        text += "Bounds: SE: {:.5f}, {:.5f}".format(bounds[2], bounds[3])
        self.drawer.label(text)
        
        '''Actions - Lower Half'''
        self.drawer.vertical_divider()
        self.drawer.seperator()
        self.drawer.header(text="Actions")
        self.drawer.button(text="Clear Points", command=self.clear_points)
        self.drawer.button(text="Delete area", command=self.mark_as_deleted)

        self.drawer.seperator()
        
        # def print_height_data(self:AreaAsset, *args, **kwargs):
        #     p0 = self.target.coordinates()[0]
        #     p1 = self.target.coordinates()[1]
        #     download_elevation(self.target, self.get_lat_long(), services.google_elevation)

        # cl = partial(print_height_data, self)
        # self.drawer.button(text="Sample height data", command=cl)

        '''Controls (Move to view_main_window later)'''
        if self.app_settings.show_controls:
            self.drawer.seperator()
            self.drawer.header(text='Controls')
            self.drawer.label('Left Click: Add point to area')
            self.drawer.label('Right Click: Remove last point from area')
            self.drawer.label('Middle Hold: Pan Location')


def create_area_file_with_data(name:str, target:ProjectAsset, data:str, app_settings) -> AreaAsset:
    filepath = Path("SavedAreas/" + target.savename + "/" + name + "_area.csv")
    with filepath.open('w') as file:
        file.write(data)

    return AreaAsset(name, target, app_settings)