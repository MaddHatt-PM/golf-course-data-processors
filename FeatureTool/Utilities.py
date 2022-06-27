from enum import Enum
from tkinter import Canvas, Image
from geographiclib.geodesic import Geodesic

from loaded_asset import LoadedAsset

class ColorSet:
    def __init__(self, path:str, fill:str) -> None:
        self.path = path
        self.fill = fill

class UIColors:
    # Colors: https://materialui.co/colors/
    canvas_col:str = "#212121"
    ui_bgm_col:str = "#424242" 

    red = ColorSet(path="#EF5350", fill="#B71C1C")
    pink = ColorSet(path="#EC407A", fill="#880E4F")
    purple = ColorSet(path="#AB47BC", fill="#4A148C")
    indigo = ColorSet(path="#5C6BC0", fill="#1A237E")
    blue = ColorSet(path="#42A5F5", fill="#0D47A1")
    cyan = ColorSet(path="#26C6DA", fill="#006064")
    teal = ColorSet(path="#26A69A", fill="#004D40")
    green = ColorSet(path="#7CB342", fill="#66BB6A")
    orange = ColorSet(path="#FFA726", fill="#FF6F00")
    brown = ColorSet(path="#A1887F", fill="#4E342E")

class CoordMode(Enum):
    normalized = 0,
    pixel = 1,
    earth = 2

class ToolMode(Enum):
    default = 0

class SpaceTransformer:
    def __init__(self, canvasRef: Canvas, target:LoadedAsset, image_raw:Image):
        self.canvasRef = canvasRef
        self.target = target
        self.image_raw = image_raw
        self.geo_util:Geodesic = Geodesic.WGS84

    def point_to_size_coords(self, pt, size=8, addOffset=False) -> tuple:
        '''pt is assumed to be the centered position point'''
        if addOffset is True:
            offset = self.canvasRef.canvasx(0), self.canvasRef.canvasy(0)
        else:
            offset = 0,0

        x0 = pt[0] - size/2 + offset[0]
        y0 = pt[1] - size/2 + offset[1]
        x1 = pt[0] + size/2 + offset[0]
        y1 = pt[1] + size/2 + offset[1]

        return (x0, y0, x1, y1)

    def earth_pt_to_pixel_space(self, pt, to_int=False) -> tuple:
        '''
        Convert an earth point (lat, lon) to 0-1 normalization
        then to pixel coordinates.
        '''
        coords = self.target.coordinates()
        max_x = coords[1][0]
        min_x = coords[0][0]
        min_y = coords[0][1]
        max_y = coords[1][1]

        norm_x = (pt[0] - min_x) / (max_x - min_x)
        norm_y = (pt[1] - min_y) / (max_y - min_y)

        if to_int is True:
            norm_x = int(norm_x)
            norm_y = int(norm_y)

        return self.norm_pt_to_pixel_space(norm_x, norm_y)

    def pixel_pt_to_earth_space(self, pt) -> tuple:
        '''
        Convert a pixel point to 0-1 normalization
        then to earth coordinates (lat, long).
        '''
        pt = self.pixel_pt_to_norm_space(pt)
        return self.norm_pt_to_earth_space(pt)

    def pixel_pt_to_norm_space(self, pt) -> tuple:
        min_x = self.canvasRef.canvasx(0)
        max_x = self.image_raw.width
        min_y = self.canvasRef.canvasy(0)
        max_y = self.image_raw.height

        norm_x = (pt[0] + min_x) / (max_x)
        norm_y = (pt[1] + min_y) / (max_y)

        return norm_x, norm_y


    def norm_pt_to_pixel_space(self, pt, to_int=False) -> tuple:
        x = pt[0] * self.image_raw.width
        y = pt[1] * self.image_raw.height
        
        if to_int is True:
            x = int(x)
            y = int(y)

        return (x, y)

    def norm_pt_to_earth_space(self, pt) -> tuple:
        coords = self.target.coordinates()
        max_x = coords[1][0]
        min_x = coords[0][0]
        min_y = coords[0][1]
        max_y = coords[1][1]

        x = pt[0] * (max_x - min_x) + min_x
        y = pt[1] * (max_y - min_y) + min_y

        return (x, y)

    def latlong_lerp(self, pt0, pt1, value) -> tuple[float, float]:
        geo = Geodesic.WGS84

        return 0.0, 0.0

    def compute_area(self, pt0, pt1, mode:CoordMode):
        if mode is CoordMode.normalized:
            pt0 = self.norm_pt_to_earth_space(pt0)
            pt1 = self.norm_pt_to_earth_space(pt1)
        elif mode is CoordMode.pixel:
            pt0 = self.pixel_pt_to_earth_space(pt0)
            pt1 = self.pixel_pt_to_earth_space(pt1)

