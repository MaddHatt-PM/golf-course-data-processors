import tkinter as tk
from tkinter import Button, Canvas, Entry, Frame, Label, Menu, PhotoImage, Tk
from pathlib import Path
from PIL import Image, ImageTk

class utilities:
    # Colors: https://materialui.co/colors/
    canvas_col:str = "#212121"
    ui_bgm_col:str = "#424242" 

class loaded_asset:
    def __init__(self, savename:str):
        self.saveName:str = savename
        self.loadFile:str = Path("SavedAreas/" + savename + "/" + savename + ".area")
        self.sateliteImg:Path = Path("SavedAreas/" + savename + "/Satelite.tif")
        self.coordinates:Path = Path("SavedAreas/" + savename + "/Coordinates.csv")
        self.elevationImg:Path = Path("SavedAreas/" + savename + "/Elevation.tif")
        self.elevationCSV:Path = Path("SavedAreas/" + savename + "/Elevation.csv")
        
    def does_satelite_data_exist(self) -> bool:
        print(self.sateliteImg)
        return self.sateliteImg.is_file()

class TerrainEditor:
    def __init__(self, target:loaded_asset):
        self.root = tk.Tk()
        self.target:loaded_asset = target
        self.prefsPath = Path("AppAssets/prefs.txt")

        self.z_scale = 1.0 # unused for now, implement later

        self.canvas:Canvas = None
        self.container = None
        self.image_raw:Image = None
        self.image_pi:PhotoImage = None

    # -------------------------------------------------------------- #
    # --- Event Handling ------------------------------------------- #
    def do_nothing(self):
        pass

    def new_area_popup(self):
        popup=tk.Toplevel()
        popup.grab_set()
        popup.focus_force()
        popup.resizable(False, False)
        # popup.geometry("600x200")

        Label(popup, text="Enter two coordinates").grid(row=0)
        Label(popup, text="Via Google Maps, right click on a map to copy coordinates").grid(row=1)

        placer = Frame(popup)
        placer.grid(row=2)

        Label(placer, text="Coordinate NW").grid(row=0, column=0)
        pt_a_field = Entry(placer).grid(row=0, column=1)

        Label(placer, text="Coordinate SE").grid(row=1, column=0)
        pt_b_field = Entry(placer).grid(row=1, column=1)


        cancel_btn = Button(placer, text="Cancel", command=self.print_test, width=20)
        cancel_btn.grid(row=2, column=0, sticky="nswe")

        enter_btn = Button(placer, text="Enter", command=self.print_test, width=20)
        enter_btn.grid(row=2, column=1, sticky="nswe")




    def print_test(self, event):
        print("test")

    def on_close(self):
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
    
    def redraw_canvas(self, event=None):
        img_box = self.canvas.bbox(self.container)
        canvas_box = (self.canvas.canvasx(0), 
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))

        overscroll = 600
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

        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            x = min(int(x2 / self.z_scale), self.image_raw.width)
            y = min(int(y2 / self.z_scale), self.image_raw.height)

            image = self.image_raw.crop((int(x1 / self.z_scale), int(y1 / self.z_scale), x, y))
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1))))
            imageid = self.canvas.create_image(max(canvas_box[0], img_box[0]),
                                               max(canvas_box[1], img_box[1]),
                                               anchor='nw', image=imagetk)
            # self.canvas.lower(imageid)  # set image into background


    # -------------------------------------------------------------- #
    # --- Sub-UI Drawing ------------------------------------------- #
    def define_menubar(self, root:Tk):
        menubar = Menu(root)

        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.do_nothing)
        filemenu.add_command(label="Open", command=self.do_nothing)
        filemenu.add_command(label="Save", command=self.do_nothing)
        filemenu.add_command(label="Revert", command=self.do_nothing)
        filemenu.add_separator()
        filemenu.add_command(label="Quit", command=self.do_nothing)
        menubar.add_cascade(label="File", menu=filemenu)

        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="About Me", command=self.do_nothing)
        menubar.add_cascade(label="Help", menu=helpmenu)
        return menubar

    def draw_inspector(self):
        inspector = Frame(self.root, bg=utilities.ui_bgm_col, padx=0,pady=0)
        inspector.grid(row=0, column=2, sticky="nswe")
        
        Frame(self.root, bg=utilities.ui_bgm_col, padx=0,pady=0).grid(row=2, column=2, sticky="nswe")

        widthSize = 36
        tk.Label(inspector, text="", width=widthSize, height=1, bg=utilities.ui_bgm_col).pack(anchor="s")

        tk.Label(inspector, text="Hello World").pack()
        tk.Button(inspector, text="Open popup", command=self.new_area_popup).pack()

    def draw_viewport(self):
        viewport = Frame(self.root, bg=utilities.canvas_col)
        viewport.grid(row=0, column=0, sticky="nswe")
        
        satelite_raw = Image.open(self.target.sateliteImg)
        satelite_pi = ImageTk.PhotoImage(image=satelite_raw)

        # Keep image references to avoid Garbage Collector
        self.image_raw = satelite_raw
        self.image_pi = satelite_pi

        self.canvas = Canvas(viewport)
        self.canvas.configure(bg=utilities.canvas_col, highlightthickness=0)
        self.canvas.create_image(satelite_pi.width()/2, satelite_pi.height()/2, anchor=tk.CENTER, image=satelite_pi)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<MouseWheel>", self.print_test)
        self.canvas.bind("<Button-2>", self.start_pan)
        self.canvas.bind("<B2-Motion>", self.pan)

        self.container = self.canvas.create_rectangle(0, 0, self.image_raw.width, self.image_raw.height, width=0)

    def draw_statusbar(self):
        statusbar = Frame(self.root, bg=utilities.ui_bgm_col)
        statusbar.grid(row=2, column= 0, sticky="nswe")
        status = tk.Label(statusbar, text="Hello World", bg=utilities.ui_bgm_col, fg="white")
        status.pack(anchor="w")

    def draw_blanks(self):
        Frame(self.root, bg=utilities.ui_bgm_col, padx=0,pady=0).grid(row=1, column=2, sticky="nswe")
        Frame(self.root, bg=utilities.ui_bgm_col, padx=0,pady=0).grid(row=2, column=2, sticky="nswe")


    # -------------------------------------------------------------- #
    # --- Root-UI Drawing ------------------------------------------ #
    def define_root(self):
        self.root.title(self.target.saveName + " - Terrain Viewer")
        self.root.minsize(width=500, height=400)
        self.root.iconbitmap(False, str(Path("AppAssets/icon.ico")))
        self.root.config(bg=utilities.canvas_col)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=5)
        self.root.config(menu=self.define_menubar(self.root))
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Read pref file for window geometry
        if self.prefsPath.is_file():
            with open(str(self.prefsPath), 'r') as pref_file:
                prefs = pref_file.read().splitlines()

                self.root.geometry(prefs[0])
                self.root.state(prefs[1])

        # UI Drawing
        self.draw_viewport()
        self.draw_statusbar()
        self.draw_inspector()
        self.draw_blanks()

        # Seperators for visual clarity
        Frame(self.root, bg="grey2").grid(row=0, column=1, sticky="nswe")
        Frame(self.root, bg="grey2").grid(row=1, column=0, sticky="nswe")

        return self.root

if __name__ == "__main__":
    app = TerrainEditor(target=loaded_asset(savename="Demo")).define_root()
    app.mainloop()