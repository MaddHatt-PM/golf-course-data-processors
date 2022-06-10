from enum import Enum
from pathlib import Path
from tkinter import Canvas, Frame
from turtle import pos
from PIL import Image, ImageDraw
from cv2 import line
from matplotlib.pyplot import fill
from CanvasDrawers import canvas_util
from InspectorDrawers import inspector_drawers
from LoadedAsset import loaded_asset
from Utilities import coord_mode, ui_colors

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

        self._prop_filepath = Path(basepath + name + "_prop.txt")
        self.fill_alpha = 0.25
        self.stroke_width = 3.0
        self.color = ui_colors.indigo

        if self._prop_filepath.is_file():
            with open(str(self._prop_filepath), 'r') as file:
                # do later
                pass


        self._stroke_filepath = Path(basepath + name + "_path.csv")
        self.coord_id:coord_mode = coord_mode.normalized
        self.stroke_data = []

        if self._stroke_filepath.is_file():
            with open(str(self._stroke_filepath), 'r') as file:
                lines = file.read().splitlines()
                

                for id, line in enumerate(lines):
                    if id == 0:
                        # Interprete csv header to get coordinate type
                        if "normalized" in lines[0]:
                            self.coord_id = coord_mode.normalized
                        elif "longitude" in lines[0]:
                            self.coord_id = coord_mode.earth
                        elif "pixel" in lines[0]:
                            self.coord_id = coord_mode.pixel

                    else:
                        # Convert nonheader lines to tuple
                        # and add to the raw data
                        self.stroke_data.append(eval(line))

        self._filled_filepath = Path(basepath + name + "_fill.tif")
        self.fill_img:Image = None
        # https://www.geeksforgeeks.org/python-pil-imagedraw-draw-polygon-method/

        if self._filled_filepath.is_file():
            self.fill_img = Image.open(self._filled_filepath)
        
    def write_data_to_files(self):
        if self.is_dirty == False:
            return

        with open(str(self._stroke_filepath), 'w') as file:
            # Write header
            header = "error_x,error_y"
            if self.coord_id == coord_mode.normalized:
                header = "normalized_x,normalized_y"
            elif self.coord_id == coord_mode.pixel:
                header = "pixel_x,pixel_y"
            elif self.coord_id == coord_mode.earth:
                header = "latitude,longitude"
            
            file.write(header + '\n')

            # Write stroke data
            for id, item in enumerate(self.stroke_data):
                file.write(str(item))
                if id - 1 != len(self.stroke_data):
                    file.write('/n')
        
        self.is_dirty = False
    
    def drawing_init(self, canvas:Canvas, util:canvas_util, img_size:tuple):
        self.is_fully_init = True

        self.canvas = canvas
        self.util = util
        self.img_size = img_size


    # -------------------------------------------------------------- #
    # --- Wrappers for stroke_data --------------------------------- #
    def modify_point(self, id:int, position:tuple):
        self.stroke_data[id] = position
        self.is_dirty = True

    def insert_point(self, position:tuple):
        self.stroke_data.insert(position)
        self.is_dirty = True

    def append_point(self, position:tuple, coordID:coord_mode):
        if (coordID == coord_mode.pixel):
            position = self.util.pixel_pt_to_norm_space(position)

        self.stroke_data.append(position)
        self.is_dirty = True
        self.draw_inspector()

    def remove_point(self, id:int):
        self.stroke_data.pop(id)
        self.is_dirty = True

        
    # -------------------------------------------------------------- #
    # --- Utility functions ---------------------------------------- #
    def is_point_in_area(self, pt:tuple, coord_id:coord_mode) -> bool:
        '''
        This method of checking if a point is within an
        irregular polygon is directly tied to the satellite
        image's dimensions. This should be replaced with an
        independent method later on.

        Another bandaid solution would be to supersize the image.
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


    # -------------------------------------------------------------- #
    # --- Canvas functions ----------------------------------------- #
    def draw(self):
        self.clear_canvasIDs()

        if self.do_draw_fill is True:
            self.draw_fill(export_to_img=True)
        
        self.draw_perimeter()

    def draw_perimeter(self):
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

        if self.possible_line != None:
            self.canvas.delete(self.possible_line)
            self.possible_line = None

        # Draw dotted line to cursor
        if len(data) > 0:
            pt_a = data[-1][0] * img_size[0], data[-1][1] * img_size[1]
            pt_b = cursor_pos[0] + self.canvas.canvasx(0), cursor_pos[1] + self.canvas.canvasy(0)
            lineID = self.canvas.create_line(*pt_a, *pt_b, width=self.stroke_width, fill='blue', dash=(6,4))
            self.possible_line = lineID


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

            fill_img.save("TEST.png")
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

        ids = self.inspectorIDs
        for item in ids:
            item.destroy()

        header = self.drawer.header(text=self.name)
        ids.append(header)
        ids.append(self.drawer.seperator())

        fill_btn = self.drawer.button(text="Toggle Fill", command=self.toggle_fill)
        ids.append(fill_btn)
        ids.append(self.drawer.seperator())

        count_header = self.drawer.header(text="(x,y) Coordinates: {}".format(len(self.stroke_data)))
        ids.append(count_header)

        for pt in self.stroke_data:
           item = self.drawer.label(text= "({0:.7f}, {0:.7f})".format(pt[0], pt[1]))
           ids.append(item)
