from enum import Enum
from pathlib import Path
from tkinter import Canvas
from PIL import Image, ImageTk
from CanvasDrawers import canvas_util
from LoadedAsset import loaded_asset

class coord_type(Enum):
    normalized = 0,
    pixel = 1,
    earth = 2

class area_asset:    
    def __init__(self, name:str, target:loaded_asset) -> None:
        self.name = name
        self.is_dirty = False
        self.canvasIDs = []
        self.canvas = None
        self.util = None

        basepath = "SavedAreas/" + target.savename + "/" 

        self._prop_filepath = Path(basepath + name + "_prop.txt")
        self.fill_alpha = 0.25
        self.stroke_width = 2.0
        self.color = 'red'

        if self._prop_filepath.is_file():
            with open(str(self._prop_filepath), 'r') as file:
                # do later
                pass


        self._stroke_filepath = Path(basepath + name + "_path.csv")
        print(basepath + name + "_path.csv")
        self.coord_id:coord_type = coord_type.normalized
        self.stroke_data = []

        if self._stroke_filepath.is_file():
            with open(str(self._stroke_filepath), 'r') as file:
                lines = file.read().splitlines()
                

                for id, line in enumerate(lines):
                    if id == 0:
                        # Interprete csv header to get coordinate type
                        if "normalized" in lines[0]:
                            self.coord_id = coord_type.normalized
                        elif "longitude" in lines[0]:
                            self.coord_id = coord_type.earth
                        elif "pixel" in lines[0]:
                            self.coord_id = coord_type.pixel

                    else:
                        # Convert nonheader lines to tuple[float,float]
                        # and add to the raw data
                        self.stroke_data.append(eval(line))

        print(self.stroke_data)
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
            if self.coord_id == coord_type.normalized:
                header = "normalized_x,normalized_y"
            elif self.coord_id == coord_type.pixel:
                header = "pixel_x,pixel_y"
            elif self.coord_id == coord_type.earth:
                header = "latitude,longitude"
            
            file.write(header + '\n')

            # Write stroke data
            for id, item in enumerate(self.stroke_data):
                file.write(str(item))
                if id - 1 != len(self.stroke_data):
                    file.write('/n')
        
        self.is_dirty = False

    # -------------------------------------------------------------- #
    # --- Wrappers for stroke_data --------------------------------- #
    def modify_point(self, id:int, position:tuple):
        self.stroke_data[id] = position
        self.is_dirty = True

    def insert_point(self, position:tuple):
        self.stroke_data.insert(position)
        self.is_dirty = True

    def add_point(self, position:tuple):
        self.stroke_data.append(position)
        self.is_dirty = True

    def remove_point(self, id:int):
        self.stroke_data.pop(id)
        self.is_dirty = True

    # -------------------------------------------------------------- #
    # --- Canvas functions ----------------------------------------- #
    def draw_area(self, canvas:Canvas, util:canvas_util, img_size:tuple):
        self.canvas = canvas
        data = self.stroke_data

        # Draw fill (do later)
        # Draw lines
        if len(data) > 2:
            for id in range(0, len(data) - 1):
                pt_a = data[id+0][0] * img_size[0], data[id+0][1] * img_size[1]
                pt_b = data[id+1][0] * img_size[0], data[id+1][1] * img_size[1]
                lineID = self.canvas.create_line(*pt_a, *pt_b, width=self.stroke_width, fill=self.color)
                self.canvasIDs.append(lineID)


        pt_a = data[0][0] * img_size[0], data[0][1] * img_size[1]
        pt_b = data[-1][0] * img_size[0], data[-1][1] * img_size[1]
        lineID = self.canvas.create_line(*pt_a, *pt_b, width=self.stroke_width, fill=self.color, dash=(6,4))
        self.canvasIDs.append(lineID)

        # Draw points
        circle_size = 8
        for point in self.stroke_data:
            pt_a = point[0] * img_size[0], point[1] * img_size[1]
            pointID = self.canvas.create_oval(util.point_to_size_coords((pt_a), circle_size), fill=self.color)
            self.canvasIDs.append(pointID)

    def clear_canvasIDs(self):
        if self.canvas == None:
            return

        for item in self.canvasIDs:
            self.canvas.delete(item)

        self.canvasIDs.clear()