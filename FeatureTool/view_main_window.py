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

from dataclasses import dataclass
from functools import partial
import os
import random
import string
import time
import tkinter as tk
from tkinter import BooleanVar, DoubleVar, StringVar, Variable, ttk
from tkinter import Button, Canvas, Entry, Frame, Label, Menu, PhotoImage, Tk
from pathlib import Path
from PIL import Image, ImageTk

from asset_area import AreaAsset, create_area_file_with_data
from asset_project import ProjectAsset
from asset_trees import TreeCollectionAsset
from util_export import export_data
from utilities import SpaceTransformer, ToolMode
from ui_inspector_drawer import inspector_drawers
from data_downloader import services, download_imagery
from utilities import CoordMode, UIColors, restart_with_new_target
from view_api_usage_window import create_api_usage_window
from view_create_area import create_area_view
from view_create_location import CreateLocationView
from view_import_prompt import create_import_window
from tkinter.messagebox import askyesnocancel

class ViewSettings():
    def __init__(self) -> None:
        self.show_controls = BooleanVar(value=True, name='Show controls')
        self.fill_only_active_area = BooleanVar(value=True, name='Fill only active area')

        self.height_map_toggle = BooleanVar(value=False, name='Height Map Toggle')
        self.height_map_opacity = DoubleVar(value=False, name='Contour Map Opacity')
        
        self.contour_map_toggle = BooleanVar(value=False, name='Contour Map Toggle')
        self.contour_map_opacity = DoubleVar(value=False, name='Height Map Opacity')

class MainWindow:
    def __init__(self, target:ProjectAsset):
        self.target:ProjectAsset = target

        if target is None:
            return

        self.root = tk.Tk()
        self.prefsPath = Path("AppAssets/prefs.windowprefs")
        self.zoom = 1.0
        self.mouse_pos = (-100, -100)
        self.status_text = tk.StringVar()
        self.status_text.set("")
        self.toolmode = ToolMode.area

        self.canvas:Canvas = None
        self.container = None
        self.image_raw:Image = Image.open(self.target.sateliteImg_path)
        self.image_pi:PhotoImage = None

        self.height_raw:Image = None
        if target.elevationImg_linear_path.exists():
            self.height_raw = Image.open(target.elevationImg_linear_path)
        self.height_pi:Image = None

        self.contour_raw:Image = None
        if target.contourImg_path.exists():
            self.contour_raw = Image.open(target.contourImg_path)
        self.contour_pi:Image = None

        self.active_area = None
        self.is_dirty = False

        self.app_settings = ViewSettings()

        filenames = os.listdir(target.basePath)
        self.areas:list[AreaAsset] = []
        for name in filenames:
            if "_area" in name:
                area_name = name.split("_area")[0]
                self.areas.append(AreaAsset(area_name, self.target, self.app_settings))
        self.area_names:list[str] = [x.name for x in self.areas]
        if len(self.areas) != 0:
            self.active_area = self.areas[0]
            self.active_area.select()

        self.tree_manager = TreeCollectionAsset(self.target)

        
        def redraw_canvas_on_change(*args):
            for area in self.areas:
                area.draw_to_canvas()
            
        def redraw_inspector_on_change(*args):
            self.active_area.draw_to_inspector

        self.app_settings.fill_only_active_area.trace_add('write', redraw_canvas_on_change)
        self.app_settings.show_controls.trace_add('write', redraw_inspector_on_change)

    # -------------------------------------------------------------- #
    # --- New Area UI ---------------------------------------------- #
    def new_location_popup(self, isMainWindow:bool=False):
        '''
        UI for downloading new areas.
        Popup is designated as the rootUI when no loaded_asset is present
        '''
        if isMainWindow == True:
            popup = self.root
        else:
            popup=tk.Toplevel()
            popup.grab_set()
            popup.focus_force()

        popup.resizable(False, False)
        self.filename = tk.StringVar()
        self.p0 = tk.StringVar()
        self.p1 = tk.StringVar()

        Label(popup, text="Enter two coordinates").grid(row=0)
        Label(popup, text="Via Google Maps, right click on a map to copy coordinates").grid(row=1, padx=20)

        prompts_f = Frame(popup)
        prompts_f.grid(row=2)

        Label(prompts_f, text="Area Name").grid(sticky='w', row=0, column=0)
        Entry(prompts_f, textvariable=self.filename).grid(row=0, column=1)

        Label(prompts_f, text="Coordinate NW").grid(sticky='w', row=1, column=0)
        Entry(prompts_f, textvariable=self.p0).grid(row=1, column=1)

        Label(prompts_f, text="Coordinate SE").grid(sticky='w', row=2, column=0)
        Entry(prompts_f, textvariable=self.p1, ).grid(row=2, column=1)

        buttons_f = Frame(popup)
        buttons_f.grid(row=3)
        cancel_btn = Button(buttons_f, text="Cancel", command=popup.destroy, width=20)
        cancel_btn.grid(row=0, column=0, sticky="nswe", pady=10)

        enter_btn = Button(buttons_f,
                           text="Enter",
                        #    state=self.validate_enter_btn(filename=filename, pt_a=pt_a, pt_b=pt_b),
                           command=self.execute_download_btn,
                           width=20)

        enter_btn.grid(row=0, column=1, sticky="nswe", pady=10)

    
    def execute_download_btn(self):
        '''Setup download environment, pull data via API, then reload program'''
        # Move to disabling the button state when I figure tkinter out callbacks
        if self.validate_download_btn(self.filename, self.p0, self.p1) == tk.DISABLED:
            print("disabled")
            return

        newArea = ProjectAsset(savename=self.filename.get().strip(), p0=eval(self.p0.get()), p1=eval(self.p1.get()))
        print(str(newArea.coordinates()))
        download_imagery(target=newArea, service=services.google_satelite)
        
        restart_with_new_target(newArea.savename)
        
    def restart_with_new_target(self, area_name:str):
        self.root.destroy()
        os.system("py run.py " + area_name)

    def create_new_area(self, name:str="", *args, **kwargs):
        if(kwargs.get('name', None) is not None):
            name = kwargs.get('name')

        if name == "":
            name = "NewArea_"
            for i in range(5):
                name += random.choice(string.ascii_letters)

        if (kwargs.get('data', None) is not None):
            area = create_area_file_with_data(name, self.target, kwargs.get('data'), self.app_settings)
        else:
            area = AreaAsset(name, self.target)

        area.save_data_to_files()
        area.drawing_init(self.canvas, self.canvasUtil, self.img_size)

        self.areas.append(area)
        self.area_names.append(name)
        
        self.select_area(area.name)
        self.setup_inspector()
        self.redraw_viewport()
        

    # -------------------------------------------------------------- #
    # --- Event Handling ------------------------------------------- #
    def print_test(self, *args, **kwargs):
        '''Dummy function for quick testing'''
        print("test")

    def handle_left_click(self, event:tk.Event):
        if self.active_area is not None:
            pt = event.x, event.y        
            self.active_area.append_point((event.x, event.y), CoordMode.pixel)

        self.check_for_changes()
        self.redraw_viewport()
        
        if self.active_area is not None:
            self.active_area.draw_last_point_to_cursor(self.mouse_pos)

    def handle_right_click(self, event:tk.Event):
        if self.active_area is not None:
            self.active_area.remove_point()
            self.check_for_changes()

    def motion(self, event):
        self.mouse_pos = (event.x, event.y)
        self.update_status_bar_text(event)

        if self.active_area is not None:
            self.active_area.draw_last_point_to_cursor(self.mouse_pos)

        # Move around the oval underneath the cursor
        self.canvas.coords(self.id_mouse_oval, self.canvasUtil.point_to_size_coords(self.mouse_pos, addOffset=True) )

    def update_status_bar_text(self, event):
        spacer = '        '

        text = ("Mouse Position: x={}, y={}").format(self.mouse_pos[0], self.mouse_pos[1])
        text += spacer

        earth_coords = self.canvasUtil.pixel_pt_to_earth_space(self.mouse_pos)
        text += ("Earth Position: lat={}, lon={}").format(earth_coords[0], earth_coords[1])

        # text += spacer
        # text += ("canvas offset: x={}, y={}").format(self.canvas.canvasx(0), self.canvas.canvasy(0))
        
        self.status_text.set(text)
        
    def check_for_changes(self):
        if self.is_dirty:
            return

        for area in self.areas:
            if area.is_dirty:
                self.is_dirty = True
                break
        
        if self.is_dirty:
            self.root.title('*' + self.target.savename + ' - Terrain Viewer')
        else:
           self.root.title(self.target.savename + ' - Terrain Viewer')

    def save_all(self):
        for area in self.areas:
            area.save_data_to_files()
            area._save_settings()
        
        self.is_dirty = False

    def on_close(self):
        if self.is_dirty:
            result = askyesnocancel(title="Save changes", message='There are unsaved changes\nDo you want to save?')
            if result is None:
                return
            elif result is True:
                self.save_all()

        '''Write window geometry before exiting'''
        with open(str(self.prefsPath), 'w') as prefs:
            prefs.write(self.root.geometry())
            prefs.write("\n")
            prefs.write(self.root.state())

        self.root.destroy()

    # -------------------------------------------------------------- #
    # --- Canvas Binding ------------------------------------------- #
    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.mouse_pos = (event.x, event.y)

        self.update_status_bar_text(event)
        self.redraw_viewport()
    
    def redraw_viewport(self):
        img_box = self.canvas.bbox(self.container)
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
        
        if self.active_area:
            self.active_area.draw_last_point_to_cursor(self.mouse_pos)
    

    # -------------------------------------------------------------- #
    # --- Sub-UI Drawing ------------------------------------------- #
    def setup_menubar(self, root:Tk):
        menubar = Menu(root)

        '''FILE menu'''
        filemenu = Menu(menubar, tearoff=0)
        closure = partial(CreateLocationView().show)
        filemenu.add_command(label="New Location", command=CreateLocationView().show)

        open_menu = Menu(filemenu, tearoff=0)
        directories = os.listdir('SavedAreas/')

        # partial() is used here to 'bake' dir into a new function
        # otherwise command would always use the last value of dir
        def open_new_location(root, dir):
            if self.is_dirty:
                result = askyesnocancel(title="Save changes", message='There are unsaved changes\nDo you want to save?')
                if result is None:
                    return
                elif result is True:
                    self.save_all()

            restart_with_new_target(root, dir)

        for dir in directories:
            closure = partial(open_new_location, self.root, dir)
            open_menu.add_command(label=dir, command=closure)

        def prep_export():
            for area in self.areas:
                area.make_masks()
            export_data(self.target)
        
        filemenu.add_cascade(label="Open", menu=open_menu)

        filemenu.add_command(label="Save", command=self.save_all)
        filemenu.add_command(label="Revert", command=self.print_test, state=tk.DISABLED)
        filemenu.add_separator()
        filemenu.add_command(label="Export", command=prep_export)
        filemenu.add_command(label="Check API Usage", command=create_api_usage_window)
        filemenu.add_separator()
        filemenu.add_command(label="Quit                   ", command=self.on_close)
        
        closure = partial(create_import_window, self)
        filemenu.add_command(label="Create import window", command=closure)
        menubar.add_cascade(label="File", menu=filemenu)

        '''VIEW menu'''
        viewmenu = Menu(menubar, tearoff=0)

        for var in self.app_settings.__dict__.values():
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
        self.toolmode = ToolMode.area
        self.setup_inspector()
        
    def mode_to_tree(self):
        self.toolmode = ToolMode.tree
        self.setup_inspector()

    def mode_to_overlays(self):
        self.toolmode = ToolMode.overlays
        self.setup_inspector()

    def setup_inspector(self):
        self.check_for_changes()
        
        inspector = Frame(self.root, padx=4, pady=0)
        inspector.grid(row=0, column=2, sticky="nswe")
        # inspector.configure(width=45)

        drawer = self.drawer = inspector_drawers(inspector)

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
        if (self.toolmode == ToolMode.overlays):
            if self.height_raw is None:
                drawer.label('Height map not generated')

            toggle = drawer.labeled_toggle(boolVar=self.app_settings.height_map_toggle, label_text='Height Map', command=self.setup_inspector)
            slider = drawer.labeled_slider(tkVar=self.app_settings.height_map_opacity, label_text='Opacity')

            if self.height_raw is None:
                toggle['state'] = tk.DISABLED
                slider['state'] = tk.DISABLED

            if self.app_settings.height_map_toggle.get() is False:
                slider['state'] = tk.DISABLED

            drawer.seperator()

            if self.contour_raw is None:
                drawer.label('Contour map not generated')

            toggle = drawer.labeled_toggle(boolVar=self.app_settings.contour_map_toggle, label_text='Contour Map', command=self.setup_inspector)
            slider = drawer.labeled_slider(tkVar=self.app_settings.contour_map_opacity, label_text='Opacity')
            
            if self.contour_raw is None:
                toggle['state'] = tk.DISABLED
                slider['state'] = tk.DISABLED
                
            if self.app_settings.contour_map_toggle.get() is False:
                slider['state'] = tk.DISABLED
                
            drawer.seperator()

        '''Area UI'''
        if (self.toolmode == ToolMode.area):
            area_selector_frame = Frame(inspector, padx=0, pady=0)
            tk.Label(area_selector_frame, text="Selected area:").grid(row=0, column=0)

            area_selector = tk.StringVar(self.root)
            available_areas = len(self.area_names) != 0
            
            area_selector.set(self.area_names[0] if available_areas is True else "No areas")
            dropdown_selected = self.active_area.name if available_areas is True else "No areas"
            dropdown = ttk.OptionMenu(area_selector_frame, area_selector, dropdown_selected, *self.area_names, command=self.select_area)
            dropdown.grid(row=0, column=1, sticky='ew')
            area_selector_frame.grid_columnconfigure(1, weight=5)
            self.area_selector = dropdown

            if available_areas:
                closure = partial(create_area_view, self, self.areas, False, self.root)
                add_area = ttk.Button(area_selector_frame, text='+', width=2, command=closure)
                add_area.grid(row=0, column=3)
                
                area_selector_frame.pack(fill="x", anchor="n", expand=False)
                ttk.Separator(inspector, orient="horizontal").pack(fill='x')

                if self.active_area is not None:
                    self.active_area.draw_to_inspector(self.drawer)

        '''Tree UI'''
        if (self.toolmode == ToolMode.tree):
            self.tree_manager.draw_to_inspector(inspector, self.drawer)
            ttk.Separator(inspector, orient="horizontal").pack(fill='x')

    def resize_viewport(self, zoom_dir:int):
        zoom_increment = 0.25
        zoom_limits = (0.25, 2.50)

        if zoom_dir == 0:
            self.zoom = 1.0
        elif zoom_dir > 0:
            self.zoom += zoom_increment
            self.zoom = min(self.zoom, zoom_limits[1])
        elif zoom_dir < 0:
            self.zoom -= zoom_increment
            self.zoom = max(self.zoom, zoom_limits[0])
        self.zoom_percentage_var.set('{}%'.format(round(self.zoom * 100)))

        width, height = self.zoom * self.image_raw.width, self.zoom * self.image_raw.height
        width, height = int(width), int(height)
        self.img_size = width, height

        self.image_resized = self.image_raw.resize((width, height), resample=Image.BICUBIC)
        self.canvasUtil.image_resized = self.image_resized

        self.image_pi = ImageTk.PhotoImage(image=self.image_resized)
        self.image_canvasID = self.canvas.create_image(self.image_pi.width()/2, self.image_pi.height()/2, anchor=tk.CENTER, image=self.image_pi)

        for area in self.areas:
            area.img_size = self.img_size
            area.draw_to_canvas()

    def setup_viewport(self):
        viewport = Frame(self.root, bg=UIColors.canvas_col)
        viewport.grid(row=0, column=0, sticky="nswe")

        
        width, height = self.zoom * self.image_raw.width, self.zoom * self.image_raw.height
        self.img_size = int(width), int(height)

        self.image_resized = self.image_raw.resize(self.img_size, resample=Image.BICUBIC)
        self.image_pi = ImageTk.PhotoImage(image=self.image_resized)

        # Keep image references to avoid Garbage Collector

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

        if self.active_area is not None:
            self.canvas.bind("<Leave>", self.active_area.destroy_possible_line)


        self.container = self.canvas.create_rectangle(0, 0, *self.img_size, width=0)
        self.id_mouse_oval = self.canvas.create_oval(self.canvasUtil.point_to_size_coords(self.mouse_pos, addOffset=True), fill="blue")

        for area in self.areas:
            area.drawing_init(self.canvas, self.canvasUtil, self.img_size)
            area.draw_to_canvas()

    def select_area(self, choice):
        self.drawer.clear_inspector()
        self.active_area.deselect()

        for area in self.areas:
            if area.name == choice:
                self.active_area = area
                break

        self.active_area.select()
        self.canvas.bind("<Leave>", self.active_area.destroy_possible_line)
        self.active_area.drawing_init(self.canvas, self.canvasUtil, self.img_size)
        self.active_area.draw_to_inspector(self.drawer)
        self.active_area.draw_to_canvas()
        
        

    def setup_statusbar(self):
        frame = Frame(self.root, bg=UIColors.ui_bgm_col)
        frame.grid(row=2, column= 0, sticky="nswe")

        # Coordinates
        status = tk.Label(frame, textvariable=self.status_text, bg=UIColors.ui_bgm_col, fg="white")
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
        zoom_in.pack(side=tk.LEFT, padx=4)

        seperator = tk.Frame(frame, bg='#424242', width=1, bd=0)
        seperator.pack(anchor='w', side=tk.LEFT, fill='y')

        # View mode selector
        view_modes = {}
        view_modes['Google Satelite'] = None
        view_modes['Google Elevation'] = None

        view_mode_dropdown = ttk.Combobox(frame)
        view_mode_dropdown['values'] = list(view_modes.keys())
        view_mode_dropdown['state'] = 'readonly'
        view_mode_dropdown.current(0)
        view_mode_dropdown.pack(anchor='w', side=tk.LEFT, padx=4)


        # view_mode = tk.Label(frame, text='Google Satelite', bg=UIColors.ui_bgm_col, fg='white')
        # view_mode.pack(anchor='w')


        
        

    def setup_blanks(self):
        Frame(self.root, padx=0,pady=0).grid(row=1, column=2, sticky="nswe")
        Frame(self.root, padx=0,pady=0).grid(row=2, column=2, sticky="nswe")


    # -------------------------------------------------------------- #
    # --- Root-UI Drawing ------------------------------------------ #
    def show(self):
        if (self.target == None):
            self.root = CreateLocationView().show(isMainWindow=True)
            self.root.title("None selected")
            return self.root

        INSPECTOR_WIDTH = 260

        self.root.title(self.target.savename + " - Terrain Viewer")
        self.root.minsize(width=500, height=400)
        self.root.iconbitmap(False, str(Path("AppAssets/icon.ico")))
        self.root.config(bg=UIColors.canvas_col)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=5)
        self.root.grid_columnconfigure(2, minsize=INSPECTOR_WIDTH)
        self.root.config(menu=self.setup_menubar(self.root))
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Read pref file for window geometry
        if self.prefsPath.is_file():
            with open(str(self.prefsPath), 'r') as pref_file:
                prefs = pref_file.read().splitlines()

                self.root.geometry(prefs[0])
                self.root.state(prefs[1])

        # UI Drawing
        self.setup_viewport()
        self.setup_statusbar()
        self.setup_inspector()
        self.setup_blanks()

        # Seperators for visual clarity
        Frame(self.root, bg="grey2").grid(row=0, column=1, sticky="nswe")
        Frame(self.root, bg="grey2").grid(row=1, column=0, sticky="nswe")

        return self.root