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
import tkinter as tk
from tkinter import Button, Canvas, Entry, Frame, Label, Menu, PhotoImage, StringVar, Tk
from pathlib import Path
from PIL import Image, ImageTk
from LoadedAsset import loaded_asset

from DownloadData import download
from DownloadData import services


class ui_colors:
    # Colors: https://materialui.co/colors/
    canvas_col:str = "#212121"
    ui_bgm_col:str = "#424242" 

class main_window:
    def __init__(self, target:loaded_asset):
        self.root = tk.Tk()
        self.target:loaded_asset = target
        self.prefsPath = Path("AppAssets/prefs.windowprefs")

        self.z_scale = 1.0 # unused for now, implement later

        self.canvas:Canvas = None
        self.container = None
        self.image_raw:Image = None
        self.image_pi:PhotoImage = None

    # -------------------------------------------------------------- #
    # --- New Area UI ---------------------------------------------- #
    def new_area_popup(self, isMainWindow:bool=False):
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
        filename_entry = Entry(prompts_f, textvariable=self.filename).grid(row=0, column=1)

        Label(prompts_f, text="Coordinate NW").grid(sticky='w', row=1, column=0)
        pt_a_entry = Entry(prompts_f, textvariable=self.p0).grid(row=1, column=1)

        Label(prompts_f, text="Coordinate SE").grid(sticky='w', row=2, column=0)
        pt_b_entry = Entry(prompts_f, textvariable=self.p1, ).grid(row=2, column=1)

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
        # Move to disabling the button state when I figure tkinter callbacks
        if self.validate_download_btn(self.filename, self.p0, self.p1) == tk.DISABLED:
            print("disabled")
            return

        newArea = loaded_asset(savename=self.filename.get().strip(), p0=eval(self.p0.get()), p1=eval(self.p1.get()))
        print(str(newArea.coordinates()))
        download(target=newArea, service=services.google_satelite)
        
        self.root.destroy()
        os.system("py run.py " + newArea.saveName)

        
    def validate_download_btn(self, filename:StringVar, pt_a:StringVar, pt_b:StringVar) -> str:
        '''
        Check if any variables are empty before allowing a download.
        Returns tk.state:str for a button
        '''
        if filename.get().strip() == False:
            return tk.DISABLED

        try:
            eval(pt_a.get())
            eval(pt_b.get())
        except:
            return tk.DISABLED

        return tk.ACTIVE

    # -------------------------------------------------------------- #
    # --- Event Handling ------------------------------------------- #
    def print_test(self):
        '''Dummy function for quick testing'''
        print("test")

    def on_close(self):
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
        self.redraw_canvas()
    
    def redraw_canvas(self):
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

        self.canvas.configure(scrollregion=scroll_bbox)
        x1 = max(canvas_box[0] - img_box[0], 0)
        y1 = max(canvas_box[1] - img_box[1], 0)
        x2 = min(canvas_box[2], img_box[2]) - img_box[0]
        y2 = min(canvas_box[3], img_box[3]) - img_box[1]

        # show image if it in the visible area
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:
            x = min(int(x2 / self.z_scale), self.image_raw.width)
            y = min(int(y2 / self.z_scale), self.image_raw.height)

            image = self.image_raw.crop((int(x1 / self.z_scale), int(y1 / self.z_scale), x, y))
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1))))
            imageid = self.canvas.create_image(max(canvas_box[0], img_box[0]),
                                               max(canvas_box[1], img_box[1]),
                                               anchor='nw', image=imagetk)

            # Lower image data for overlaying later
            self.canvas.lower(imageid)


    # -------------------------------------------------------------- #
    # --- Sub-UI Drawing ------------------------------------------- #
    def setup_menubar(self, root:Tk):
        menubar = Menu(root)

        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.new_area_popup)
        filemenu.add_command(label="Open", command=self.print_test, state=tk.DISABLED)
        filemenu.add_command(label="Save", command=self.print_test, state=tk.DISABLED)
        filemenu.add_command(label="Revert", command=self.print_test, state=tk.DISABLED)
        filemenu.add_separator()
        filemenu.add_command(label="Quit", command=self.on_close)
        menubar.add_cascade(label="File", menu=filemenu)

        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About Me", command=self.print_test)
        menubar.add_cascade(label="Help", menu=helpmenu)
        return menubar

    def setup_inspector(self):
        inspector = Frame(self.root, bg=ui_colors.ui_bgm_col, padx=0,pady=0)
        inspector.grid(row=0, column=2, sticky="nswe")
        
        Frame(self.root, bg=ui_colors.ui_bgm_col, padx=0,pady=0).grid(row=2, column=2, sticky="nswe")

        widthSize = 36
        tk.Label(inspector, text="", width=widthSize, height=1, bg=ui_colors.ui_bgm_col).pack(anchor="s")

        tk.Label(inspector, text="Inspector for precision editing").pack()
        tk.Button(inspector, text="Download new area", command=self.new_area_popup).pack()

    def setup_viewport(self):
        
        viewport = Frame(self.root, bg=ui_colors.canvas_col)
        viewport.grid(row=0, column=0, sticky="nswe")
        
        satelite_raw = Image.open(self.target.sateliteImg)
        satelite_pi = ImageTk.PhotoImage(image=satelite_raw)

        # Keep image references to avoid Garbage Collector
        self.image_raw = satelite_raw
        self.image_pi = satelite_pi

        self.canvas = Canvas(viewport)
        self.canvas.configure(bg=ui_colors.canvas_col, highlightthickness=0)
        self.canvas.create_image(satelite_pi.width()/2, satelite_pi.height()/2, anchor=tk.CENTER, image=satelite_pi)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<MouseWheel>", self.print_test)
        self.canvas.bind("<Button-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.pan)

        self.container = self.canvas.create_rectangle(0, 0, self.image_raw.width, self.image_raw.height, width=0)

    def setup_statusbar(self):
        statusbar = Frame(self.root, bg=ui_colors.ui_bgm_col)
        statusbar.grid(row=2, column= 0, sticky="nswe")
        status = tk.Label(statusbar, text="Hello World", bg=ui_colors.ui_bgm_col, fg="white")
        status.pack(anchor="w")

    def setup_blanks(self):
        Frame(self.root, bg=ui_colors.ui_bgm_col, padx=0,pady=0).grid(row=1, column=2, sticky="nswe")
        Frame(self.root, bg=ui_colors.ui_bgm_col, padx=0,pady=0).grid(row=2, column=2, sticky="nswe")


    # -------------------------------------------------------------- #
    # --- Root-UI Drawing ------------------------------------------ #
    def define_root(self):
        if (self.target == None):
            self.root.title("None selected")
            self.new_area_popup(isMainWindow=True)
            return self.root

        self.root.title(self.target.saveName + " - Terrain Viewer")
        self.root.minsize(width=500, height=400)
        self.root.iconbitmap(False, str(Path("AppAssets/icon.ico")))
        self.root.config(bg=ui_colors.canvas_col)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=5)
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