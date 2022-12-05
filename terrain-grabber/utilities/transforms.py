"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022
"""

from tkinter import Canvas, Image
from geographiclib.geodesic import Geodesic

from asset_project import LocationPaths

from .enums import CoordMode

class SpaceTransformer:
    """
    Utility object to handle coordinate system changes.
    Normalized space (0-1) is used as an in between stage between pixel space and earth (latitude/longitude) space.
    """
    def __init__(self, canvasRef: Canvas, target:LocationPaths, image_resized:Image):
        self.canvasRef = canvasRef
        self.target = target
        self.image_resized = image_resized
        self.geo_util:Geodesic = Geodesic.WGS84

    def point_to_size_coords(self, pt:tuple[float,float], size=8, addOffset=False) -> tuple:
        '''Expand a point in pixel space to a square of points with sides of length *size*'''
        if addOffset is True:
            offset = self.canvasRef.canvasx(0), self.canvasRef.canvasy(0)
        else:
            offset = 0,0

        x0 = pt[0] - size/2 + offset[0]
        y0 = pt[1] - size/2 + offset[1]
        x1 = pt[0] + size/2 + offset[0]
        y1 = pt[1] + size/2 + offset[1]

        return (x0, y0, x1, y1)

    def earth_pt_to_pixel_space(self, pt:tuple[float,float], to_int=False) -> tuple:
        """Transform a point from latitude/longitude space to """
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

    def pixel_pt_to_earth_space(self, pt:tuple[float,float]) -> tuple:
        """Transform a point from pixel space to normalized space"""
        pt = self.pixel_pt_to_norm_space(pt)
        return self.norm_pt_to_earth_space(pt)

    def pixel_pt_to_norm_space(self, pt:tuple[float,float]) -> tuple:
        """Transform a point from pixel space to normalized space (0-1)"""
        min_x = self.canvasRef.canvasx(0)
        max_x = self.image_resized.width
        min_y = self.canvasRef.canvasy(0)
        max_y = self.image_resized.height

        norm_x = (pt[0] + min_x) / (max_x)
        norm_y = (pt[1] + min_y) / (max_y)

        return norm_x, norm_y


    def norm_pt_to_pixel_space(self, pt:tuple[float,float], to_int=False) -> tuple:
        """Transform a point from normalized space (0-1) to pixel space"""
        x = pt[0] * self.image_resized.width
        y = pt[1] * self.image_resized.height
        
        if to_int is True:
            x = int(x)
            y = int(y)

        return (x, y)

    def norm_pt_to_earth_space(self, pt:tuple[float,float]) -> tuple:
        """Transform a point from normalized space (0-1) to latitude/longitude space"""
        coords = self.target.coordinates()
        max_x = coords[1][0]
        min_x = coords[0][0]
        min_y = coords[0][1]
        max_y = coords[1][1]

        x = pt[0] * (max_x - min_x) + min_x
        y = pt[1] * (max_y - min_y) + min_y

        return (x, y)

    def compute_area(self, pt0, pt1, mode:CoordMode):
        if mode is CoordMode.normalized:
            pt0 = self.norm_pt_to_earth_space(pt0)
            pt1 = self.norm_pt_to_earth_space(pt1)
        elif mode is CoordMode.pixel:
            pt0 = self.pixel_pt_to_earth_space(pt0)
            pt1 = self.pixel_pt_to_earth_space(pt1)