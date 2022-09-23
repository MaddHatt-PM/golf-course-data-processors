import os
import sys
from tkinter import Tk

def restart_with_location(root:Tk, area_name:str):
    root.destroy()
    os.system("py run.py " + area_name)
    sys.exit()