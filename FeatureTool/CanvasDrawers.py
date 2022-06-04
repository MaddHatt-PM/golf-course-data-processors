from tkinter import Canvas

from LoadedAsset import loaded_asset


class canvas_util:
    def __init__(self, canvasRef: Canvas, target:loaded_asset):
        self.canvasRef = canvasRef
        self.target = target

    def point_to_size_coords(self, pt, size=8) -> tuple:
        '''pt is assumed to be the centered position point'''
        x0 = pt[0] - size/2 + self.canvasRef.canvasx(0)
        y0 = pt[1] - size/2 + self.canvasRef.canvasy(0)
        x1 = pt[0] + size/2 + self.canvasRef.canvasx(0)
        y1 = pt[1] + size/2 + self.canvasRef.canvasy(0)

        return (x0, y0, x1, y1)

    def earth_pt_to_canvas_space(self, pt) -> tuple:
        '''
        Convert an earth point (lat, lon) to 0-1 normalization
        then to canvas coordinates.
        '''
        coords = self.target.coordinates()
        max_y = coords[0][0]
        min_x = coords[0][1]
        min_y = coords[1][0]
        max_x = coords[1][1]

        norm_x = (pt[0] - min_x) / (max_x - min_x)
        norm_y = (pt[1] - min_y) / (max_y - min_y)

        max_y = self.canvasRef.canvasy(1)
        min_x = self.canvasRef.canvasx(0)
        min_y = self.canvasRef.canvasy(0)
        max_x = self.canvasRef.canvasx(1)

        x = norm_x * (max_x - min_x) + min_x
        y = norm_y * (max_y - min_y) + min_y

        return (x, y)

    def canvas_pt_to_earth_space(self, pt) -> tuple:
        '''
        Convert a canvas point to 0-1 normalization
        then to earth coordinates (lat, long).
        '''
        max_y = self.canvasRef.canvasy(1)
        min_x = self.canvasRef.canvasx(0)
        min_y = self.canvasRef.canvasy(0)
        max_x = self.canvasRef.canvasx(1)

        norm_x = (pt[0] - min_x) / (max_x - min_x)
        norm_y = (pt[1] - min_y) / (max_y - min_y)

        coords = self.target.coordinates()
        max_y = coords[0][0]
        min_x = coords[0][1]
        min_y = coords[1][0]
        max_x = coords[1][1]

        x = norm_x * (max_x - min_x) + min_x
        y = norm_y * (max_y - min_y) + min_y

        return (x, y)
