from pickle import TRUE
import tkinter as tk
from tkinter import NSEW, Canvas, Frame, Label, Menu, Tk
from pathlib import Path
from wsgiref.simple_server import demo_app
from PIL import Image, ImageTk


class utilities:
    bgm_color:str = "#212121"




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

    # -------------------------------------------------------------- #
    # --- Event Handling ------------------------------------------- #
    def do_nothing(self):
        pass

    def open_popup(self):
        popup=tk.Toplevel()
        popup.grab_set()
        popup.geometry("600x200")
        Label(popup, text="example").place(x=150, y=80)

    def test(self, event):
        print("testing")

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
        inspector = Frame(self.root, bg=utilities.bgm_color, padx=0,pady=0)
        inspector.grid(row=0, column=2, sticky="nswe")

        tk.Label(inspector, text= "Hello World", width=36).pack()
        tk.Button(inspector, text= "Open popup", command=self.open_popup, width = 36).pack()

    def draw_viewport(self):
        viewport = Frame(self.root, bg=utilities.bgm_color)
        viewport.grid(row=0, column=0, sticky="nswe")
        
        satelite_raw = Image.open(self.target.sateliteImg)
        satelite_pi = ImageTk.PhotoImage(image=satelite_raw)

        # Keep image references to avoid Garbage Collector
        self.root.img = satelite_pi

        canvas = Canvas(viewport)
        canvas.configure(bg=utilities.bgm_color, highlightthickness=0)
        canvas.create_image(satelite_pi.width()/2, satelite_pi.height()/2, anchor=tk.CENTER, image=satelite_pi)
        canvas.bind('<MouseWheel>', self.test)
        canvas.pack(fill=tk.BOTH, expand=True)

    def draw_statusbar(self):
        statusbar = Frame(self.root, bg="white")
        statusbar.grid(row=2, column= 0, sticky="nswe")
        status = tk.Label(statusbar, text= "Hello World", width=36)
        status.pack()


    # -------------------------------------------------------------- #
    # --- Root-UI Drawing ------------------------------------------ #
    def define_root(self):
        self.root.title(self.target.saveName + " - Terrain Viewer")
        self.root.minsize(width=500, height=400)
        self.root.iconbitmap(False, str(Path("AppAssets/icon.ico")))
        self.root.config(bg=utilities.bgm_color)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=5)
        self.root.config(menu=self.define_menubar(self.root))

        self.draw_viewport()
        self.draw_statusbar()
        self.draw_inspector()

        # Seperators for visual clarity
        Frame(self.root, bg="grey2").grid(row=0, column=1, sticky="nswe")
        Frame(self.root, bg="grey2").grid(row=1, column=0, sticky="nswe")

        
        return self.root

app = TerrainEditor(target=loaded_asset(savename="Demo")).define_root()
app.mainloop()