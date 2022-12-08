"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022
"""

import json
from pathlib import Path
from functools import partial

import tkinter as tk
from tkinter.messagebox import askyesno
from tkinter import BooleanVar, Canvas, DoubleVar, IntVar

from PIL import Image, ImageDraw, ImageTk, ImageColor

from geographiclib.geodesic import Geodesic
from geographiclib.polygonarea import PolygonArea
from utilities.enums import ToolMode

from subviews import InspectorDrawer
from asset_project import LocationPaths
from utilities import SpaceTransformer, CoordMode
from utilities.colors import ColorSet, UIColors


class SettingKeys:
    """
    TODO: Think of a nicer way to handle settings
            - Data class paired with a store to handle fileio?
    """
    fill_alpha = "fill_alpha"
    stroke_width = "stroke_width"
    do_draw_points = "do_draw_points"
    do_draw_fill = "do_draw_fill"
    overfill_amt = "overfill_amt"
    color = "color"
    layer_key = "layer_key"

    _color_path = "color_path"
    _color_fill = "color_fill"

HEADER = "latitude,longitude,elevation,resolution\n"

class AreaAsset:
    """
    A collection of 2D points to define polygonal areas and helper methods to handle:\n
    - Creation/Deletion of polygonal areas\n
    - Saving/Loading of areas from a file\n
    - Saving/Loading of metadata
    - Handling of generated images\n
    - Drawing of an area to a provided tkinter object\n
    """
    def __init__(self, name:str, target:LocationPaths, app_settings) -> None:
        self.name = name
        self.is_dirty = False
        self.is_fill_dirty = True
        self.canvas_ids = []
        self.canvas = None
        self.drawer = None
        self.util = None
        self.is_active_area = False
        self.was_deleted = False
        self.view_settings = app_settings

        self.last_point_line = None
        self.is_fully_init = False
        self.fill_img:Image.Image = None
        self.img_size = None
        self.canvas_id_fill = None
        self.target = target
        self.metadata = {}
        self.image_pi = None

        basepath = "../SavedAreas/" + target.savename + "/"

        self._settings_path = Path(basepath + name + "_settings.txt")
        if self._settings_path.is_file():
            with self._settings_path.open('r', encoding='utf8') as file:
                self.settings:dict = json.loads(file.read())

                path = self.settings.pop(SettingKeys._color_path)
                fill = self.settings.pop(SettingKeys._color_fill)
                self.settings[SettingKeys.color] = ColorSet(path, fill)
        else:
            self.settings = {}
            self.settings[SettingKeys.fill_alpha] = 0.5
            self.settings[SettingKeys.stroke_width] = 3.0
            self.settings[SettingKeys.color] = UIColors.indigo
            self.settings[SettingKeys.overfill_amt] = 0
            self.settings[SettingKeys.do_draw_fill] = True
            self.settings[SettingKeys.do_draw_points] = True
            self.settings[SettingKeys.layer_key] = "Default"
            self._save_settings()

        # self.fill_alpha = 0.25
        self.stroke_width = 3.0

        self._stroke_filepath = Path(basepath + name + "_area.csv")
        self.coord_id:CoordMode = CoordMode.normalized
        self.stroke_data = []

        if self._stroke_filepath.is_file():
            with open(str(self._stroke_filepath), 'r', encoding='utf8') as file:
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
        """
        Write setting data to file.
        """
        settings = dict(self.settings)

        # color_set is not json compatible
        color:ColorSet = settings.pop(SettingKeys.color)
        settings[SettingKeys._color_path] = color.path
        settings[SettingKeys._color_fill] = color.fill

        with self._settings_path.open('w', encoding='utf8') as file:
            settings_str = json.dumps(settings)
            file.write(settings_str)


    def save_data_to_files(self):
        """
        Save point collection to csv file with the name as the filename.
        """
        with open(str(self._stroke_filepath), 'w', encoding='utf8') as file:
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
        """
        Prepare canvas rendering by establishing some references.
        """
        self.canvas = canvas
        self.util = util
        self.img_size = img_size
        self.is_fully_init = True


    def prompt_for_deletion(self):
        """
        Present a popup to delete the region.\n
        If confirmed, delete all files that can be deleted at the moment.
        The remaining files will be deleted at the next program launch.
        """
        delete_msg = "Deleting this area will send associated files to trash.\n"
        delete_msg += "To undo, restore the files back to the project and restart."

        if askyesno(title="Delete area?", message=delete_msg):
            self._stroke_filepath.unlink(missing_ok=True)
            self._settings_path.unlink(missing_ok=True)
            self._fill_img_filepath.unlink(missing_ok=True)
            self._mask_img_filepath.unlink(missing_ok=True)
            
            self.was_deleted = True
            self.rerender_area()


    def get_lat_long(self) -> tuple[list[float], list[float]]:
        """
        Return a new tuple of lists in the coordinate space of latitude and longitude
        """
        lat, long = [], []
        for pt in self.stroke_data:
            pt = self.util.norm_pt_to_earth_space(pt)
            lat.append(pt[0])
            long.append(pt[1])

        return (lat, long)

    # -------------------------------------------------------------- #
    # --- Wrappers for stroke_data --------------------------------- #
    def modify_point(self, id:int, position:tuple):
        """
        Change a point at index id to the supplied position
        """
        self.stroke_data[id] = position
        self.rerender_area()


    def append_point(self, position:tuple, coord_id:CoordMode):
        """
        Add a new point with the given position and coordinate space.
        By default, use pixel coordinate space.
        """
        if coord_id == CoordMode.pixel:
            position = self.util.pixel_pt_to_norm_space(position)

        self.stroke_data.append(position)
        self.rerender_area()


    def remove_point(self, id:int=-1):
        """
        Remove a point from the collection.
        By default, remove the last point.
        """
        self.stroke_data.pop(id)
        self.rerender_area()


    def clear_points(self):
        """
        Remove all points from the selected area and rerender the UI.
        """
        self.stroke_data.clear()
        self.rerender_area()


    def rerender_area(self):
        """
        Rerender the area in the canvas and inspector.
        """
        self.is_dirty = True
        self.is_fill_dirty = True
        self.draw_to_viewport()
        self.draw_to_inspector()


    # -------------------------------------------------------------- #
    # --- Utility functions ---------------------------------------- #
    def is_point_in_area(self, pt:tuple, coord_id:CoordMode) -> bool:
        """
        This method checks if a point is within an
        irregular polygon is directly tied to the satellite
        image's dimensions. This should be replaced with an
        independent method later

        Bandaid solutions to refine edges would be to:
            [a] supersize the image  
            [b] average the value of surrounding pixels since getpixel() uses an int and not a float
        """
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


    def generate_geographiclib_polygon(self):
        """
        Generate a geographiclib polygon from the coordinates.
        Two polygons are generated (depending on which is considered inside the polygon).
        The smaller of the two are returned. 
        """
        geo:Geodesic = Geodesic.WGS84
        polygon = PolygonArea(geo, False)

        for pt in self.stroke_data:
            _pt = self.util.norm_pt_to_earth_space(pt)
            # Order: LAT, Long
            polygon.AddPoint(_pt[0], _pt[1])

        # Counterclockwise and clockwise return different results.
        # Return lowest to counter user input
        return min(polygon.Compute(False, False), polygon.Compute(True, False))


    def get_polygonal_area(self) -> PolygonArea:
        """
        Convert points into a PolygonArea from geographiclib to handle curvature math.
        """
        geo:Geodesic = Geodesic.WGS84
        polygon = PolygonArea(geo, False)

        for pt in self.stroke_data:
            _pt = self.util.norm_pt_to_earth_space(pt)
            # Order: LAT, Long
            polygon.AddPoint(_pt[0], _pt[1])

        return polygon


    def get_bounds(self) -> tuple[float,float,float,float]:
        """
        Get the maximal boundry of the area.
        """

        # N, W -> Max, Min
        # S, E -> Min, Max
        n,w = float("-inf"), float("inf")
        s,e = float("inf"), float("-inf")

        for pt in self.stroke_data:
            n,w = max(n, pt[0]), min(w, pt[1])
            s,e = min(s, pt[0]), max(e, pt[1])

        return n,w,s,e


    # -------------------------------------------------------------- #
    # --- Canvas functions ----------------------------------------- #
    def draw_to_viewport(self):
        """
        1. Clear any referenced canvas elements
        2. Check if this area_asset was deleted before continuing.
        3. If the area_asset is selected, draw it's fill area.
        4. Draw the perimeter of the area.
        """
        self.clear_canvas_ids()

        if self.was_deleted:
            if self.canvas_id_fill is not None:
                self.canvas.delete(self.canvas_id_fill)
                self.canvas_id_fill = None
            return

        
        if self.view_settings.fill_only_active_area.get():
            if self.is_active_area:
                self.__draw_fill()
            else:
                self.fill_img = None
                self.image_pi = None

        elif self.settings.get('do_draw_fill', False) is True:
            self.__draw_fill()
            
        self.__draw_perimeter()
    

    def export_binary_masks(self):
        """
        Render out the fill as black and white image.
        White being the space inside of the area.
        """
        self.__draw_fill(as_mask=True)


    def __draw_perimeter(self):
        """
        Draw the perimeter of the area's polygon as line segments.
        Apply dots to the vertices if applicable.        
        """
        if self.is_fully_init is False:
            raise Exception("{} is not fully initiated, call drawing_init()")

        data = self.stroke_data
        img_size = self.img_size
        util = self.util

        if len(data) >= 2:
            # Draw drop shadow if the area is selected
            if self.is_active_area and self.view_settings.toolmode == ToolMode.area:
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
                    line_id = self.canvas.create_line(*pt_a, *pt_b, width=self.stroke_width, fill=drop_color)
                    self.canvas_ids.append(line_id)

                pt_a = data[0][0] * img_size[0], data[0][1] * img_size[1]
                pt_b = data[-1][0] * img_size[0], data[-1][1] * img_size[1]

                line_id = self.canvas.create_line(*pt_a, *pt_b, width=self.stroke_width, fill='#424242', dash=(6,4))
                self.canvas_ids.append(line_id)

            # Draw unselected lines
            for id in range(0, len(data) - 1):
                pt_a = data[id+0][0] * img_size[0], data[id+0][1] * img_size[1]
                pt_b = data[id+1][0] * img_size[0], data[id+1][1] * img_size[1]
                line_id = self.canvas.create_line(*pt_a, *pt_b, width=self.stroke_width, fill=self.settings['color'].path)
                self.canvas_ids.append(line_id)

            pt_a = data[0][0] * img_size[0], data[0][1] * img_size[1]
            pt_b = data[-1][0] * img_size[0], data[-1][1] * img_size[1]

            self.canvas_ids.append(
                self.canvas.create_line(
                    *pt_a,
                    *pt_b,
                    width=self.stroke_width,
                    fill=self.settings['color'].path,
                    dash=(6,4)
                )
            )

            for id in range(0, len(data) - 1):
                pt_a = data[id+0][0] * img_size[0], data[id+0][1] * img_size[1]
                pt_b = data[id+1][0] * img_size[0], data[id+1][1] * img_size[1]
                line_id = self.canvas.create_line(*pt_a, *pt_b, width=self.stroke_width, fill=self.settings['color'].path)
                self.canvas_ids.append(line_id)

            pt_a = data[0][0] * img_size[0], data[0][1] * img_size[1]
            pt_b = data[-1][0] * img_size[0], data[-1][1] * img_size[1]

            line_id = self.canvas.create_line(*pt_a, *pt_b, width=self.stroke_width, fill=self.settings['color'].path, dash=(6,4))
            self.canvas_ids.append(line_id)

        # Draw points
        if self.settings['do_draw_points'] and self.is_active_area and self.view_settings.toolmode == ToolMode.area:
            circle_size = 8
            for point in self.stroke_data:
                pt_a = point[0] * img_size[0], point[1] * img_size[1]
                self.canvas_ids.append(
                    self.canvas.create_oval(
                        util.point_to_size_coords((pt_a), circle_size),
                        fill=self.settings['color'].path
                        )
                    )


    def __draw_fill(self, as_mask=False):
        """
        Private function to render out the area's polygon to an image then apply it to the canvas.
        If as_mask is True, a black and white binary image of just the fill is exported and the function exits early.
        """
        if as_mask is False and self.view_settings.toolmode != ToolMode.area:
            if self.canvas_id_fill is not None:
                self.canvas.delete(self.canvas_id_fill)
            return

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

        for id, _ in enumerate(bgm_xy_coords):
            if bgm_xy_coords[id] > 5:
                bgm_xy_coords[id] += 1


        img_size = self.util.norm_pt_to_pixel_space((1.0, 1.0))
        img_size = (
            (int)(img_size[0]),
            (int)(img_size[1])
        )

        if len(polygon_points) > 2:
            if self.is_fill_dirty is True or as_mask is True:
                fill = ImageColor.getcolor(self.settings['color'].fill, 'RGB')
                alpha = int(self.settings['fill_alpha'] * 255)
                color = (*fill, alpha)
                background = (255,255,255, 0)
                save_path = self._fill_img_filepath

                if as_mask is True:
                    color = (255,255,255,255) # white
                    background = (0,0,0,255) # black
                    save_path = self._mask_img_filepath

                fill_img = Image.new("RGBA", img_size, background)
                drawer = ImageDraw.Draw(fill_img)

                drawer.polygon(polygon_points, fill=color)

                if self.settings.get(SettingKeys.overfill_amt, 0) > 0:
                    # Overfill - Outline
                    width = self.settings.get(SettingKeys.overfill_amt, 0)
                    outline = polygon_points.copy()
                    outline.append(polygon_points[0])
                    outline.append(polygon_points[1])
                    drawer.line(outline, fill=color, width=width, joint="curve")

                    # Overfill - Endcaps
                    def circle(drawer: ImageDraw.ImageDraw, center, radius, fill):
                        drawer.ellipse(
                            (
                                center[0] - radius + 1, center[1] - radius + 1,
                                center[0] + radius - 1, center[1] + radius - 1
                            ),
                            fill=fill, outline=None
                        )

                    circle(drawer, (polygon_points[0], polygon_points[1]), width/2, color)

                fill_img.save(save_path)
                if as_mask:
                    return

                self.fill_img = fill_img
                self.is_fill_dirty = False

            self.image_pi = ImageTk.PhotoImage(Image.open(self._fill_img_filepath).resize(self.img_size))
            self.canvas_id_fill = self.canvas.create_image(
                self.image_pi.width()/2,
                self.image_pi.height()/2,
                anchor=tk.CENTER,
                image=self.image_pi
                )

        elif self.canvas_id_fill is not None:
            self.canvas.delete(self.canvas_id_fill)
            self.canvas_id_fill = None


    def draw_last_point_to_cursor(self, cursor_pos:tuple):
        """
        Render out a canvas line from the last placed area point and the user's cursor.
        """
        data = self.stroke_data
        img_size = self.img_size

        self.destroy_last_point_line()

        if self.was_deleted:
            return

        # Draw dotted line to cursor
        if len(data) > 0:
            pt_a = data[-1][0] * img_size[0], data[-1][1] * img_size[1]
            pt_b = cursor_pos[0] + self.canvas.canvasx(0), cursor_pos[1] + self.canvas.canvasy(0)
            self.last_point_line = self.canvas.create_line(
                *pt_a,
                *pt_b,
                width=2,
                fill='white',
                dash=(6,4)
                )


    def destroy_last_point_line(self, *args, **kwargs):
        """
        Destroy the canvas element that renders a line between
        the area's last point and the user's cursor.
        """
        if self.last_point_line is not None:
            self.canvas.delete(self.last_point_line)
            self.last_point_line = None


    def on_select(self):
        """
        Function to be called when the area is selected.
        """
        self.is_active_area = True


    def on_deselect(self):
        """
        Function to be called when the area is no longer selected.
        Reconfigured the elements rendered to the viewport.
        """
        self.is_active_area = False
        self.draw_to_viewport()
        self.destroy_last_point_line()


    def clear_canvas_ids(self):
        """
        Delete the elements being rendered to the canvas and clear their references.
        """
        if self.canvas is None:
            return

        for item in self.canvas_ids:
            self.canvas.delete(item)

        self.canvas_ids.clear()


    def set_color(self, color:ColorSet, *args, **kwargs):
        """
        Set the color that is used for the path and fill of an area.\n
        Afterwards, redraw the viewport.
        """
        self.settings['color'] = color
        self.is_fill_dirty = True
        self.draw_to_viewport()
        self._save_settings()


    def toggle_fill(self):
        """
        Toggle the rendering of an area's fill.\n
        Afterwards, redraw the viewport.
        """
        self.settings['do_draw_fill'] = not self.settings['do_draw_fill']

        if self.settings['do_draw_fill'] is False:
            self.fill_img = None
            self.image_pi = None

        self.draw_to_viewport()
        self.draw_to_inspector()


    def toggle_points(self):
        """
        Toggle the rendering of points that define the areas.\n
        Afterwards, redraw the viewport.
        """
        self.settings['do_draw_points'] = not self.settings['do_draw_points']
        self.draw_to_viewport()


    # -------------------------------------------------------------- #
    # --- Inspector functions -------------------------------------- #
    def draw_to_inspector(self, drawer:InspectorDrawer=None):
        if self.drawer is None and drawer is not None:
            self.drawer = drawer

        if drawer is None:
            drawer = self.drawer

        if drawer is None:
            raise Exception("Trying to draw inspector without being fully initialized")

        drawer.clear_inspector()

        if self.was_deleted:
            drawer.header("Area Deleted - Select new area")
            return

        drawer.header(text="Settings")

        drawer.labeled_dropdown(
            self.settings['color'],
            value_data=UIColors.colors,
            value_names=UIColors.names,
            default_index=0,
            label_text="Color",
            change_commands=self.set_color)

        do_draw_points = BooleanVar(value=self.settings['do_draw_points'])
        drawer.labeled_toggle(
            label_text="Toggle path points",
            command=self.toggle_points,
            boolVar=do_draw_points)

        do_fill = BooleanVar(value=self.settings['do_draw_fill'])
        drawer.labeled_toggle(label_text="Toggle fill", command=self.toggle_fill, boolVar=do_fill)

        def sync_variable(self:AreaAsset, var_name:str, tk_var, *args, **kwargs):
            self.settings[var_name] = tk_var.get()
            self.is_fill_dirty = True
            self.draw_to_viewport()

        fill_state = [] if do_fill.get() is True else ['disabled']

        fill_alpha_var = DoubleVar()
        fill_alpha_var.set(self.settings.get(SettingKeys.fill_alpha, 0.2))
        fill_alpha_closure = partial(sync_variable, self, SettingKeys.fill_alpha, fill_alpha_var)
        fill_alpha_var.trace_add('write', fill_alpha_closure)
        drawer.labeled_slider(
            "Fill Opacity",
            tkVar=fill_alpha_var
            ).state(fill_state)

        overfill_max = 500
        overfill_var = IntVar()
        overfill_var.set(self.settings.get(SettingKeys.overfill_amt, 0))
        overfill_closure = partial(sync_variable, self, SettingKeys.overfill_amt, overfill_var)
        overfill_var.trace_add('write', overfill_closure)
        drawer.labeled_slider(
            "Overfill",
            tkVar=overfill_var,
            from_=0,
            to=overfill_max
            ).state(fill_state)

        drawer.seperator()

        area_info = self.generate_geographiclib_polygon()
        bounds = self.get_bounds()

        drawer.header(text="Statistics")
        text = "Point count: {}\n".format(len(self.stroke_data))
        text += "Perimeter (m): {:.4f}\n".format(area_info[1])
        text += "Area (m²): {:.4f}\n".format(area_info[2])
        text += "Bounds: NW: {:.5f}, {:.5f}\n".format(bounds[0], bounds[1])
        text += "Bounds: SE: {:.5f}, {:.5f}".format(bounds[2], bounds[3])
        drawer.label(text)

        # Actions - Lower Half
        drawer.vertical_divider()
        drawer.seperator()
        drawer.header(text="Actions")
        drawer.button(text="Clear Points", command=self.clear_points)
        drawer.button(text="Delete area", command=self.prompt_for_deletion)

        drawer.seperator()

        # def print_height_data(self:AreaAsset, *args, **kwargs):
        #     p0 = self.target.coordinates()[0]
        #     p1 = self.target.coordinates()[1]
        #     download_elevation(self.target, self.get_lat_long(), services.google_elevation)

        # cl = partial(print_height_data, self)
        # drawer.button(text="Sample height data", command=cl)

        # Controls (Move to view_main_window later)
        if self.view_settings.show_controls:
            drawer.seperator()
            drawer.header(text='Controls')
            drawer.label('Left Click: Add point to area')
            drawer.label('Right Click: Remove last point from area')
            drawer.label('Middle Hold: Pan Location')


def create_area_file_with_data(name:str, target:LocationPaths, data:str, app_settings) -> AreaAsset:
    filepath = Path("../SavedAreas/" + target.savename + "/" + name + "_area.csv")
    with filepath.open('w', encoding='utf8') as file:
        file.write(data)

    return AreaAsset(name, target, app_settings)
