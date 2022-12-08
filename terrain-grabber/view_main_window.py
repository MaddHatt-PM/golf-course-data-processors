'''
@Author 2022: Patt Martin
Description:
    All GUI Drawing and Event Handling

Tasklist:
    - Figure out a nicer way to split up the UI code before this class becomes too large
    - [NewAreaPopup] Change around execute_download_btn() to only reload the program for new projects
    - [NewAreaPopup] Figure out how to detect changes on Entry fields so that the download button can be validated
    - [StatusBar] Figure out how to redraw a label to display info, preferably without a direct reference
'''

import os
import sys
import random
import string
from pathlib import Path
from functools import partial

from PIL import Image, ImageTk
import tkinter as tk
from tkinter import IntVar, Tk, ttk, BooleanVar, DoubleVar, StringVar, Variable, Canvas, Frame, Menu, PhotoImage
from tkinter.messagebox import askyesnocancel

from operations.generate_imagery import generate_imagery, generate_contour_map

from asset_project import LocationPaths
from data_managers import TreeCollectionManager, LayerManager, LayerEditor
from asset_area import AreaAsset, create_area_file_with_data
from operations import export_data, export_model, restart_with_location
from utilities import SpaceTransformer, ToolMode, CoordMode, UIColors
from views import show_api_usage, show_create_area, show_create_location, show_import_path_as_area
from subviews import InspectorDrawer

class ViewSettings():
    """
    Helper object to contain tkinter variables and other application settings.
    Implied to work akin to a singleton, so create once and then pass the reference around.
    (If a metaclass wasn't needed to have a static singleton, it would bypass passing around the reference)
    """
    def __init__(self) -> None:
        self.show_controls = BooleanVar(value=True, name='Show controls')
        self.fill_only_active_area = BooleanVar(value=True, name='Fill only active area')

        self.height_map_toggle = BooleanVar(value=False, name='Height Map Toggle')
        self.height_map_opacity = DoubleVar(value=100, name='Height Map Opacity')
        
        self.contour_map_toggle = BooleanVar(value=False, name='Contour Map Toggle')
        self.contour_map_opacity = DoubleVar(value=100, name='Contour Map Opacity')
        
        self.sampleDist_map_toggle = BooleanVar(value=False, name='Sample Dist Map Toggle')
        self.sampleDist_map_opacity = DoubleVar(value=100, name='Sample Dist Map Opacity')

        self.contour_levels = DoubleVar(value=58, name='Contour Levels')
        self.contour_thickness = DoubleVar(value=1.5, name='Contour Thickness')

        self.toolmode = ToolMode.area

        self.status_text = tk.StringVar()
        self.status_text.set("")

class MainWindow:
    """
    Initialize and create the main window for terrain grabber
    """
    def __init__(self, target:LocationPaths):
        self.target:LocationPaths = target
        if target is None:
            return

        self.root = tk.Tk()
        self.view_settings = ViewSettings()

        self.zoom = 1.0
        self.mouse_pos = (-100, -100)
        self.is_dirty = False

        # Prepare image references
        self.image_raw:Image = Image.open(self.target.satelite_img_path).convert('RGBA')
        self.image_base:Image = self.image_raw
        self.image_pi:PhotoImage = None

        self.height_raw:Image = None
        if target.elevation_img_linear_path.exists():
            self.height_raw = Image.open(target.elevation_img_linear_path).convert('RGBA')

        self.contour_raw:Image = None
        if target.contour_img_path.exists():
            self.contour_raw = Image.open(target.contour_img_path).convert('RGBA')

        self.sample_dist_raw:Image = None
        if target.sample_distribution_img_path.exists():
            self.sample_dist_raw = Image.open(target.sample_distribution_img_path).convert('RGBA')

        # Prepare layer manager
        self.layer_manager = LayerManager(filepath=target.layers_path)

        # Prepare references to areas
        self.areas:list[AreaAsset] = []
        filenames = os.listdir(target.basepath)
        for name in filenames:
            if "_area" in name:
                area_name = name.split("_area")[0]
                self.areas.append(AreaAsset(area_name, self.target, self.view_settings))

        self.area_names:list[str] = [x.name for x in self.areas]
        self.active_area = None
        if len(self.areas) != 0:
            self.active_area = self.areas[0]
            self.active_area.on_select()

        self.tree_manager = TreeCollectionManager(self.target)

        # Setup skeleton of UI
        self.root.title(self.target.savename + " - Terrain Viewer")
        self.root.minsize(width=500, height=400)
        self.root.iconbitmap(False, str(Path("resources/icon.ico")))
        self.root.config(bg=UIColors.canvas_col)
        self.root.config(menu=self.setup_menubar(self.root))

        INSPECTOR_WIDTH = 260
        self.root.grid_columnconfigure(2, minsize=INSPECTOR_WIDTH)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=5)

        # UI Drawing
        self.canvas:Canvas = None
        self.canvas_container = None
        self.setup_viewport()
        self.setup_statusbar()
        self.setup_inspector()

        # Read pref file for window geometry
        self.prefsPath = Path("resources/prefs.windowprefs")
        if self.prefsPath.is_file():
            with open(str(self.prefsPath), 'r') as pref_file:
                prefs = pref_file.read().splitlines()

                self.root.geometry(prefs[0])
                self.root.state(prefs[1])

        # Blanks
        Frame(self.root, padx=0,pady=0).grid(row=1, column=2, sticky="nswe")
        Frame(self.root, padx=0,pady=0).grid(row=2, column=2, sticky="nswe")

        # Seperators for visual clarity
        Frame(self.root, bg="grey2").grid(row=0, column=1, sticky="nswe")
        Frame(self.root, bg="grey2").grid(row=1, column=0, sticky="nswe")

        # Attach callbacks
        def redraw_canvas_on_change(*args):
            for area in self.areas:
                area.draw_to_viewport()
            
        def redraw_inspector_on_change(*args):
            self.active_area.draw_to_inspector

        self.view_settings.fill_only_active_area.trace_add('write', redraw_canvas_on_change)
        self.view_settings.show_controls.trace_add('write', redraw_inspector_on_change)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Launch GUI
        self.root.mainloop()
        

    # -------------------------------------------------------------- #
    # --- Event Handling ------------------------------------------- #
    def print_test(self, *args, **kwargs):
        '''Dummy function for quick testing'''
        print("test")

    # Gets called but no references due to circular import
    def create_new_area(self, name:str="", *args, **kwargs):
        """
        Callback from area_asset's inspector that creates a new area then sets it as the active area
        """
        if(kwargs.get('name', None) is not None):
            name = kwargs.get('name')

        if name == "":
            name = "NewArea_"
            for i in range(5):
                name += random.choice(string.ascii_letters)

        if (kwargs.get('data', None) is not None):
            area = create_area_file_with_data(name, self.target, kwargs.get('data'), self.view_settings)
        else:
            area = AreaAsset(name, self.target, self.view_settings)

        area.save_data_to_files()
        area.drawing_init(self.canvas, self.canvasUtil, self.img_size)

        self.areas.append(area)
        self.area_names.append(name)
        
        self.select_area(area.name)
        self.setup_inspector()
        self.redraw_viewport()

    def handle_left_click(self, event:tk.Event):
        """
        Callback function called for all left click events
        """
        if self.active_area is not None:
            self.active_area.append_point((event.x, event.y), CoordMode.pixel)

        self.check_for_changes()
        self.redraw_viewport()
        
        if self.active_area is not None and self.view_settings.toolmode is ToolMode.area:
            self.active_area.draw_last_point_to_cursor(self.mouse_pos)

    def handle_right_click(self, event:tk.Event):
        """
        Callback function called for all right click events
        """
        if self.view_settings.toolmode == ToolMode.area:
            if self.active_area is not None:
                self.active_area.remove_point()
                self.check_for_changes()
        
        if self.view_settings.toolmode == ToolMode.tree:
            mouse_pos = (event.x, event.y)
            mouse_pos = self.canvasUtil.pixel_pt_to_norm_space(mouse_pos)
            self.tree_manager.move_tree_on_right_click(*mouse_pos)

    def motion(self, event):
        """
        Callback function called for any mouse movement
        """
        self.mouse_pos = (event.x, event.y)
        self.update_status_bar_text(event)

        if self.active_area is not None and self.view_settings.toolmode is ToolMode.area:
            self.active_area.draw_last_point_to_cursor(self.mouse_pos)

    def update_status_bar_text(self, event):
        """
        Refresh the status bar text with up to date info
        """
        spacer = '        '

        text = ("Mouse Position: x={}, y={}").format(self.mouse_pos[0], self.mouse_pos[1])
        text += spacer

        earth_coords = self.canvasUtil.pixel_pt_to_earth_space(self.mouse_pos)
        text += ("Earth Position: lat={}, lon={}").format(earth_coords[0], earth_coords[1])
        
        self.view_settings.status_text.set(text)
        
    def check_for_changes(self):
        """
        Check areas of the program for a dirty object (object needing to be saved to disk).
        If dirty, add an asterick to the window title.
        """
        if self.is_dirty:
            return

        for area in self.areas:
            if area.is_dirty:
                self.is_dirty = True
                break

        for tree in self.tree_manager.trees:
            if tree._is_dirty:
                self.is_dirty = True
                break
        
        if self.is_dirty:
            self.root.title('*' + self.target.savename + ' - Terrain Viewer')
        else:
           self.root.title(self.target.savename + ' - Terrain Viewer')

    def save(self):
        """
        Save area assets and trees
        """
        for area in self.areas:
            area.save_data_to_files()
            area._save_settings()
        
        self.tree_manager.save_data_to_files()
        
        self.is_dirty = False
        self.root.title(self.target.savename + ' - Terrain Viewer')

    def on_close(self):
        """
        Callback function that interrupts the quit process to save files.
        If the quit process continues, window geometry is preserved.
        """
        if self.is_dirty:
            result = askyesnocancel(title="Save changes", message='There are unsaved changes\nDo you want to save?')
            if result is None:
                return
            elif result is True:
                self.save()

        # Write window geometry before exiting
        with open(str(self.prefsPath), 'w') as prefs:
            prefs.write(self.root.geometry())
            prefs.write("\n")
            prefs.write(self.root.state())

        self.root.destroy()
        sys.exit(0)

    # -------------------------------------------------------------- #
    # --- Canvas Binding ------------------------------------------- #
    def start_pan(self, event):
        """
        Callback function that is called before pan() and is binded to middle mouse click
        """
        self.canvas.scan_mark(event.x, event.y)

    def pan(self, event):
        """
        Callback function that is binded to middle mouse wheel dragging
        """
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.mouse_pos = (event.x, event.y)

        self.update_status_bar_text(event)
        self.redraw_viewport()
    
    def redraw_viewport(self):
        """
        
        """
        img_box = self.canvas.bbox(self.canvas_container)
        canvas_box = (self.canvas.canvasx(0), 
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))

        overscroll = 1000
        scroll_bbox = [min(img_box[0] - overscroll, canvas_box[0]), min(img_box[1] - overscroll, canvas_box[1]),  
                       max(img_box[2] + overscroll, canvas_box[2]), max(img_box[3] + overscroll, canvas_box[3])]

        if scroll_bbox[0] == canvas_box[0] and scroll_bbox[2] == canvas_box[2]:
            scroll_bbox[0] = img_box[0]
            scroll_bbox[2] = img_box[2]

        if scroll_bbox[1] == canvas_box[1] and scroll_bbox[3] == canvas_box[3]:
            scroll_bbox[1] = img_box[1]
            scroll_bbox[3] = img_box[3]
        
        if self.active_area and self.view_settings.toolmode == ToolMode.area:
            self.active_area.draw_last_point_to_cursor(self.mouse_pos)
    

    # -------------------------------------------------------------- #
    # --- Sub-UI Drawing ------------------------------------------- #
    def setup_menubar(self, root:Tk):
        """
        Creates the UI for the top menubar and should only be called ONCE.
        Unsure how this will behave a mac.
        """
        menubar = Menu(root)

        '''FILE menu'''
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="New Location", command=show_create_location)

        open_menu = Menu(filemenu, tearoff=0)
        directories = os.listdir('../SavedAreas/')

        # partial() is used here to 'bake' dir into a new function
        # otherwise command would always use the last value of dir
        def prompt_for_restart(root, location):
            if self.is_dirty:
                result = askyesnocancel(title="Save changes", message='There are unsaved changes\nDo you want to save?')
                if result is None:
                    return
                elif result is True:
                    self.save()

            restart_with_location(root, location)

        for dir in directories:
            closure = partial(prompt_for_restart, self.root, dir)
            open_menu.add_command(label=dir, command=closure)

        def prep_data_export():
            for area in self.areas:
                area.export_binary_masks()
            export_data(self.target)

        def prep_3D_model_export():
            export_model(target=self.target, input_texture=self.target.satelite_img_path)
        
        filemenu.add_cascade(label="Open", menu=open_menu)
        filemenu.add_command(label="Save", command=self.save)
        filemenu.add_command(label="Revert", command=self.print_test, state=tk.DISABLED)
        filemenu.add_separator()
        filemenu.add_command(label="Export as files", command=prep_data_export)
        filemenu.add_command(label="Export as 3D Model", command=prep_3D_model_export)
        filemenu.add_command(label="Check API Usage", command=show_api_usage)
        filemenu.add_separator()
        filemenu.add_command(label="Quit                   ", command=self.on_close)
        
        closure = partial(show_import_path_as_area, self)
        filemenu.add_command(label="Create import window", command=closure)
        menubar.add_cascade(label="File", menu=filemenu)

        '''VIEW menu'''
        viewmenu = Menu(menubar, tearoff=0)

        for var in self.view_settings.__dict__.values():
            if isinstance(var, Variable):
                viewmenu.add_checkbutton(label=var, variable=var)

        menubar.add_cascade(label='View', menu=viewmenu)

        '''DATA menu'''
        datamenu = Menu(menubar, tearoff=0)


        '''HELP menu'''
        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About Me", command=self.print_test)

        menubar.add_cascade(label="Help", menu=helpmenu)
        return menubar

    def mode_to_area(self):
        """
        Change mode to Area Assets
        """
        self.view_settings.toolmode = ToolMode.area
        self.tree_manager.set_active_tool(False)
        self.__finish_mode_change()
        
    def mode_to_tree(self):
        """
        Change mode to Trees
        """
        self.view_settings.toolmode = ToolMode.tree
        self.tree_manager.set_active_tool(True)
        self.__finish_mode_change()

    def mode_to_overlays(self):
        """
        Change mode to overlays
        """
        self.view_settings.toolmode = ToolMode.overlays
        self.tree_manager.set_active_tool(False)
        self.__finish_mode_change()

    def __finish_mode_change(self):
        """
        Private function to finish up mode changes
        """
        self.tree_manager.draw_to_viewport()
        self.active_area.draw_to_viewport()
        self.setup_inspector()

    def setup_inspector(self):
        self.check_for_changes()
        
        inspector = Frame(self.root, padx=4, pady=0)
        inspector.grid(row=0, column=2, sticky="nswe")
        # inspector.configure(width=45)

        drawer = InspectorDrawer(inspector)
        self.drawer = drawer

        '''Functionality Switcher'''
        mode_frame = Frame(inspector, padx=0, pady=0)
        ttk.Button(mode_frame, text="Overlays", command=self.mode_to_overlays).grid(row=0, column=0, sticky='ew')
        ttk.Button(mode_frame, text="Areas", command=self.mode_to_area).grid(row=0, column=1, sticky='ew')
        ttk.Button(mode_frame, text="Trees", command=self.mode_to_tree).grid(row=0, column=2, sticky='ew')
        mode_frame.grid_columnconfigure(0, weight=1)
        mode_frame.grid_columnconfigure(1, weight=1)
        mode_frame.pack(fill='x', anchor='n', expand=False)
        
        ttk.Separator(inspector, orient="horizontal").pack(fill='x', pady=4)

        '''Overlays UI'''
        if (self.view_settings.toolmode == ToolMode.overlays):
            '''Height Controls'''
            if self.height_raw is None:
                drawer.label('Height map not generated')

            toggle = drawer.labeled_toggle(boolVar=self.view_settings.height_map_toggle, label_text='Height Map', command=self.setup_inspector)
            slider = drawer.labeled_slider(tkVar=self.view_settings.height_map_opacity, label_text='Opacity', from_=0.0, to=99.0)

            if self.height_raw is None:
                toggle['state'] = tk.DISABLED
                slider['state'] = tk.DISABLED

            if self.view_settings.height_map_toggle.get() is False:
                slider['state'] = tk.DISABLED

            drawer.seperator()

            '''Contour Controls'''
            if self.contour_raw is None:
                drawer.label('Contour map not generated')

            toggle = drawer.labeled_toggle(boolVar=self.view_settings.contour_map_toggle, label_text='Contour Map', command=self.setup_inspector)
            slider = drawer.labeled_slider(tkVar=self.view_settings.contour_map_opacity, label_text='Opacity', from_=0.0, to=99.0)
            
            if self.contour_raw is None:
                toggle['state'] = tk.DISABLED
                slider['state'] = tk.DISABLED
                
            if self.view_settings.contour_map_toggle.get() is False:
                slider['state'] = tk.DISABLED
                
            drawer.seperator()

            '''Sample Distribution Controls'''
            if self.contour_raw is None:
                drawer.label('Sample Distribution map not generated')

            toggle = drawer.labeled_toggle(boolVar=self.view_settings.sampleDist_map_toggle, label_text='Sample Distribution Map', command=self.setup_inspector)
            slider = drawer.labeled_slider(tkVar=self.view_settings.sampleDist_map_opacity, label_text='Opacity', from_=0.0, to=99.0)
            
            if self.sample_dist_raw is None:
                toggle['state'] = tk.DISABLED
                slider['state'] = tk.DISABLED
                
            if self.view_settings.sampleDist_map_toggle.get() is False:
                slider['state'] = tk.DISABLED

            self.drawer.vertical_divider()

            drawer.labeled_slider(label_text="Contour Levels", tkVar=self.view_settings.contour_levels, from_=10, to=100)
            drawer.labeled_slider(label_text="Contour Thickness", tkVar=self.view_settings.contour_thickness, from_=0.5, to=5.0)
            
            def regenerate_maps():
                generate_contour_map(
                    self.target,
                    contour_levels=int(self.view_settings.contour_levels.get()),
                    contour_thickness=self.view_settings.contour_thickness.get()
                    )

                # Prepare image references
                self.image_raw:Image = Image.open(self.target.satelite_img_path).convert('RGBA')
                self.image_base:Image = self.image_raw
                self.image_pi:PhotoImage = None

                self.height_raw:Image = None
                if self.target.elevation_img_linear_path.exists():
                    self.height_raw = Image.open(self.target.elevation_img_linear_path).convert('RGBA')

                self.contour_raw:Image = None
                if self.target.contour_img_path.exists():
                    self.contour_raw = Image.open(self.target.contour_img_path).convert('RGBA')

                self.sample_dist_raw:Image = None
                if self.target.sample_distribution_img_path.exists():
                    self.sample_dist_raw = Image.open(self.target.sample_distribution_img_path).convert('RGBA')

                self.rerender_base_image()

            drawer.button(text="Regenerate Maps", command=regenerate_maps)
                

        '''Area UI'''
        if (self.view_settings.toolmode == ToolMode.area):
            area_selector_frame = Frame(inspector, padx=0, pady=0)
            
            if len(self.areas) == 0:
                closure = partial(show_create_area, self, self.areas, False, self.root)
                add_area = ttk.Button(area_selector_frame, text='Create new area', command=closure)
                add_area.pack()
                area_selector_frame.pack(fill="x", anchor="n", expand=False)
            
            else:
                tk.Label(area_selector_frame, text="Selected area:").grid(row=0, column=0)

                area_selector_title = tk.StringVar(self.root)
                available_areas = len(self.area_names) != 0
                
                area_selector_title.set(self.area_names[0] if available_areas is True else "No areas")
                dropdown_selected = self.active_area.name if available_areas is True else "No areas"
                area_selector = ttk.OptionMenu(
                    area_selector_frame,
                    area_selector_title,
                    dropdown_selected,
                    *self.area_names,
                    command=self.select_area
                    ).grid(row=0, column=1, sticky='ew')
                area_selector_frame.grid_columnconfigure(1, weight=5)

                if available_areas:
                    closure = partial(show_create_area, self, self.areas, False, self.root)
                    add_area = ttk.Button(area_selector_frame, text='+', width=2, command=closure)
                    add_area.grid(row=0, column=3)
                    layer_key = "layer_key"

                    def select_layer(choice):
                        self.active_area.settings[layer_key] = choice
                        self.active_area._save_settings()
                        self.check_for_changes()

                    layer_selector_title = tk.StringVar(self.root)
                    tk.Label(area_selector_frame, text="Layer:").grid(row=1, column=0)
                    layer_selector = ttk.OptionMenu(
                        area_selector_frame,
                        layer_selector_title,
                        self.active_area.settings[layer_key],
                        *self.layer_manager.get_layer_names(),
                        command=select_layer
                    ).grid(row=1, column=1, sticky='ew')
                    

                    def edit_layers(layers):
                        self.layer_manager.layers = layers
                        self.layer_manager.save()

                        for area in self.areas:
                            keys = list(self.layer_manager.layers.keys())
                            if area.settings[layer_key] not in keys:
                                area.settings[layer_key] = "Default"
                                area.is_dirty = True

                        self.check_for_changes()
                        self.setup_inspector()

                    closure = partial(LayerEditor, self.layer_manager.layers, edit_layers)
                    edit_layers_button = ttk.Button(area_selector_frame, text='...', width=2, command=closure)
                    edit_layers_button.grid(row=1, column=3)

                    area_selector_frame.pack(fill="x", anchor="n", expand=False)
                    ttk.Separator(inspector, orient="horizontal").pack(fill='x')

                    if self.active_area is not None:
                        self.active_area.draw_to_inspector(self.drawer)

        '''Tree UI'''
        if (self.view_settings.toolmode == ToolMode.tree):
            self.tree_manager.draw_to_inspector(inspector, self.drawer, force_selector_draw=True)

    def rerender_base_image(self):
        self.image_base = self.image_raw
        
        if self.view_settings.height_map_toggle.get() is True and self.height_raw is not None:
            self.image_base = Image.blend(self.image_base, self.height_raw, self.view_settings.height_map_opacity.get() / 100.0)
            
        if self.view_settings.contour_map_toggle.get() is True and self.contour_raw is not None:
            clear = Image.new('RGBA', self.image_base.size)
            contour_modified = Image.blend(clear, self.contour_raw, self.view_settings.contour_map_opacity.get() / 100.0)
            self.image_base = Image.alpha_composite(self.image_base, contour_modified)

        if self.view_settings.sampleDist_map_toggle.get() is True and self.sample_dist_raw is not None:
            clear = Image.new('RGBA', self.image_base.size)
            sample_dist_modified = Image.blend(clear, self.sample_dist_raw, self.view_settings.sampleDist_map_opacity.get() / 100.0)
            self.image_base = Image.alpha_composite(self.image_base, sample_dist_modified)

        
        self.resize_viewport(0)

    def resize_viewport(self, zoom_dir:int):
        zoom_increment = 0.25
        zoom_limits = (0.25, 2.50)

        if zoom_dir == 0:
            pass
        elif zoom_dir > 0:
            self.zoom += zoom_increment
            self.zoom = min(self.zoom, zoom_limits[1])
        elif zoom_dir < 0:
            self.zoom -= zoom_increment
            self.zoom = max(self.zoom, zoom_limits[0])
        self.zoom_percentage_var.set('{}%'.format(round(self.zoom * 100)))

        width, height = self.zoom * self.image_base.width, self.zoom * self.image_base.height
        width, height = int(width), int(height)
        self.img_size = width, height

        self.image_resized = self.image_base.resize((width, height), resample=Image.BICUBIC)
        self.canvasUtil.image_resized = self.image_resized

        self.image_pi = ImageTk.PhotoImage(image=self.image_resized)
        self.image_canvasID = self.canvas.create_image(self.image_pi.width()/2, self.image_pi.height()/2, anchor=tk.CENTER, image=self.image_pi)

        self.tree_manager.draw_to_viewport()

        for area in self.areas:
            area.img_size = self.img_size
            area.draw_to_viewport()

    def setup_viewport(self):
        viewport = Frame(self.root, bg=UIColors.canvas_col)
        viewport.grid(row=0, column=0, sticky="nswe")

        
        width, height = self.zoom * self.image_base.width, self.zoom * self.image_base.height
        self.img_size = int(width), int(height)

        # Keep image references to avoid Garbage Collector
        self.image_resized = self.image_base.resize(self.img_size, resample=Image.BICUBIC)
        self.image_pi = ImageTk.PhotoImage(image=self.image_resized)

        self.canvas = Canvas(viewport)
        self.canvasUtil = SpaceTransformer(self.canvas, self.target, self.image_resized)
        self.canvas.configure(bg=UIColors.canvas_col, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.image_canvasID = self.canvas.create_image(self.image_pi.width()/2, self.image_pi.height()/2, anchor=tk.CENTER, image=self.image_pi)
        self.canvas.lower(self.image_canvasID)

        self.canvas.bind("<Button-1>", self.handle_left_click) # Left Click
        self.canvas.bind("<Button-2>", self.start_pan) # Middle Click
        self.canvas.bind("<Button-3>", self.handle_right_click) # Right Click
        self.canvas.bind("<B2-Motion>", self.pan)
        self.canvas.bind("<Motion>", self.motion)

        def tkVar_to_rerender_base(*args, **kwargs):
                self.rerender_base_image()

        self.view_settings.contour_map_opacity.trace_add('write', tkVar_to_rerender_base)
        self.view_settings.contour_map_toggle.trace_add('write', tkVar_to_rerender_base)
        self.view_settings.height_map_opacity.trace_add('write', tkVar_to_rerender_base)
        self.view_settings.height_map_toggle.trace_add('write', tkVar_to_rerender_base)
        self.view_settings.sampleDist_map_opacity.trace_add('write', tkVar_to_rerender_base)
        self.view_settings.sampleDist_map_toggle.trace_add('write', tkVar_to_rerender_base)

        if self.active_area is not None:
            self.canvas.bind("<Leave>", self.active_area.destroy_last_point_line)

        self.canvas_container = self.canvas.create_rectangle(0, 0, *self.img_size, width=0)

        self.tree_manager.setup_draw_to_viewport(canvas=self.canvas, util=self.canvasUtil)
        self.tree_manager.draw_to_viewport()

        for area in self.areas:
            area.drawing_init(self.canvas, self.canvasUtil, self.img_size)
            area.draw_to_viewport()

    def select_area(self, choice):
        self.drawer.clear_inspector()
        if self.active_area is not None:
            self.active_area.on_deselect()

        for area in self.areas:
            if area.name == choice:
                self.active_area = area
                break

        self.active_area.on_select()
        self.canvas.bind("<Leave>", self.active_area.destroy_last_point_line)
        self.active_area.drawing_init(self.canvas, self.canvasUtil, self.img_size)
        self.active_area.draw_to_inspector(self.drawer)
        self.active_area.draw_to_viewport()

    def setup_statusbar(self):
        frame = Frame(self.root, bg=UIColors.ui_bgm_col)
        frame.grid(row=2, column= 0, sticky="nswe")

        # Coordinates
        status = tk.Label(frame, textvariable=self.view_settings.status_text, bg=UIColors.ui_bgm_col, fg="white")
        status.pack(anchor="w", side=tk.LEFT)

        spacer = tk.Label(frame, text='', bg=UIColors.ui_bgm_col)
        spacer.pack(anchor='w', expand=True, side=tk.LEFT)

        # Zoom
        zoom_out_closure = partial(self.resize_viewport, -1.0)
        zoom_out = tk.Button(frame, text="-", bg=UIColors.ui_bgm_col, fg="white", width=2, command=zoom_out_closure)
        zoom_in_closure = partial(self.resize_viewport, 1.0)
        zoom_in = tk.Button(frame, text="+", bg=UIColors.ui_bgm_col, fg="white", width=2, command=zoom_in_closure)
        self.zoom_percentage_var = StringVar(value='{}%'.format(round(self.zoom * 100)))
        zoom_percentage = tk.Label(frame, textvariable=self.zoom_percentage_var, bg=UIColors.ui_bgm_col, fg="white", width=8)

        zoom_out.pack(side=tk.LEFT, padx=4)
        zoom_percentage.pack(side=tk.LEFT)
        zoom_in.pack(side=tk.LEFT, padx=0)
