import json
from pathlib import Path
import tkinter as tk
from tkinter import BooleanVar, Canvas, Frame, Label, StringVar
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk
from utilities import SpaceTransformer
from ui_inspector_drawer import inspector_drawers
from loaded_asset import LoadedAsset
from utilities import ColorSet, CoordMode, UIColors

from geographiclib.geodesic import Geodesic
from geographiclib.polygonarea import PolygonArea

class Settings:
    fill_alpha = "fill_alpha"
    stroke_width = "stroke_width"
    do_draw_points = True
    do_draw_fill = False
    color = "color"
    _color_path = "color_path"
    _color_fill = "color_fill"

class AreaAsset:
    def __init__(self, name:str, target:LoadedAsset) -> None:
        self.name = name
        self.is_dirty = False
        self.canvasIDs = []
        self.inspectorIDs = []
        self.canvas = None
        self.drawer = None
        self.util = None
        self.do_draw_fill = False
        self.do_draw_points = True
        self.possible_line = None
        self.is_fully_init = False
        self.fill_img:Image.Image = None

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
            self.settings[Settings.fill_alpha] = 0.25
            self.settings[Settings.stroke_width] = 3.0
            self.settings[Settings.color] = UIColors.indigo
            self.__save_settings()

        self.fill_alpha = 0.25
        self.stroke_width = 3.0
        self.color = UIColors.indigo

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
        if self._fill_img_filepath.is_file():
            self.fill_img = Image.open(self._fill_img_filepath)

    def __save_settings(self):
        settings = dict(self.settings)
        color:ColorSet = settings.pop(Settings.color)
        settings[Settings._color_path] = color.path
        settings[Settings._color_fill] = color.fill

        with self._settings_path.open('w') as file:
            # color_set is not json compatible
            settings_str = json.dumps(settings)
            file.write(settings_str)
        
    def save_data_to_files(self):
        # if self.is_dirty == False:
        #     return

        with open(str(self._stroke_filepath), 'w') as file:
            csv_header = "latitude,longitude,elevation,resolution\n"
            file.write(csv_header)

            # Write stroke data
            for id, item in enumerate(self.stroke_data):
                file.write(str(item).removeprefix('(').removesuffix(')'))
                if id - 1 != len(self.stroke_data):
                    file.write('\n')
        
        self.is_dirty = False
    
    def drawing_init(self, canvas:Canvas, util:SpaceTransformer, img_size:tuple):
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

    def append_point(self, position:tuple, coordID:CoordMode):
        if (coordID == CoordMode.pixel):
            position = self.util.pixel_pt_to_norm_space(position)

        self.stroke_data.append(position)
        self.is_dirty = True
        self.draw_inspector()

    def remove_point(self, id:int):
        self.stroke_data.pop(id)
        self.is_dirty = True
        self.draw_inspector()

    def clear_points(self):
        self.stroke_data.clear()
        self.draw_canvas()
        self.draw_inspector()

        
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
            self.draw_fill()

        if coord_id is CoordMode.pixel:
            pass
        elif coord_id is CoordMode.earth:
            pt = self.util.earth_pt_to_pixel_space(pt, to_int=True)
        elif coord_id is CoordMode.normalized:
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

    def compute_info(self):
        geo:Geodesic = Geodesic.WGS84
        polygon = PolygonArea(geo, False)

        for pt in self.stroke_data:
            _pt = self.util.norm_pt_to_earth_space(pt)
            # Order: LAT, Long
            polygon.AddPoint(_pt[0], _pt[1])

        return polygon.Compute(False, False)

    def destroy(self):
        pass

    # -------------------------------------------------------------- #
    # --- Canvas functions ----------------------------------------- #
    def draw_canvas(self):
        self.clear_canvasIDs()

        if self.do_draw_fill is True:
            self.draw_fill()
            
        self.draw_perimeter()
        
    def draw_perimeter(self):
        if self.is_fully_init is False:
            raise Exception("{} is not fully initiated, call drawing_init()")

        data = self.stroke_data
        img_size = self.img_size
        util = self.util

        # Draw fill (do later)
        # Draw lines
        if len(data) >= 2:
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
        if self.do_draw_points:
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

        if self.do_draw_fill is False:
            self.fill_img = None
            self.image_pi = None

        self.draw_canvas()

    def toggle_points(self):
        self.do_draw_points = not self.do_draw_points
        self.draw_canvas()


    def draw_fill(self):
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
            self.fill_img = Image.new("RGBA", img_size, (255, 255, 255, 1))
            drawer = ImageDraw.Draw(self.fill_img)
            drawer.polygon(polygon_points, fill=(255,0,0,125))

            self.fill_img.save(self._fill_img_filepath)
            self.fill_img = self.fill_img
            
            self.image_pi = ImageTk.PhotoImage(Image.open(self._fill_img_filepath))
            imageid = self.canvas.create_image(self.image_pi.width()/2, self.image_pi.height()/2, anchor=tk.CENTER, image=self.image_pi)


    # -------------------------------------------------------------- #
    # --- Inspector functions -------------------------------------- #
    def draw_inspector(self, drawer:inspector_drawers=None):
        if drawer is not None:
            self.drawer = drawer

        if self.drawer is None:
            raise Exception("Trying to draw inspector without being fully initialized")

        self.drawer.clear_inspector()
        self.drawer.header(text="Settings")

        do_draw_points = BooleanVar(value=self.do_draw_points)
        self.drawer.labeled_toggle(label_text="Toggle path points", command=self.toggle_points, boolVar=do_draw_points)

        do_fill = BooleanVar(value=self.do_draw_fill)
        self.drawer.labeled_toggle(label_text="Toggle fill", command=self.toggle_fill, boolVar=do_fill)
        self.drawer.labeled_slider("Fill Opacity")
        self.drawer.seperator()

        area_info = self.compute_info()

        self.drawer.header(text="Statistics")
        text = "Point count: {}\n".format(len(self.stroke_data))
        text += "Perimeter (m): {:.4f}\n".format(area_info[1])
        text += "Area (m²): {:.4f}\n".format(area_info[2])
        text += "Bounds: NW: {}, {}\n".format(0.5, 0.5)
        text += "Bounds: SE: {}, {}".format(0.5, 0.5)
        self.drawer.label(text)
        
        self.drawer.seperator()
        placeholder = StringVar()
        placeholder.set("Entry Text")
        self.drawer.labeled_entry(label_text="Labeled Entry test", entryVariable=placeholder)
        
        # Lower half
        self.drawer.vertical_divider()
        self.drawer.seperator()
        self.drawer.header(text="Actions")
        self.drawer.button(text="Sample Elevation")
        self.drawer.button(text="Save", command=self.save_data_to_files)
        self.drawer.button(text="Clear Points", command=self.clear_points)
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