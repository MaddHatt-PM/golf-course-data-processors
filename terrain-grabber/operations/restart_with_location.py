"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022
"""

import os
import sys
from tkinter import Tk

def restart_with_location(root:Tk, area_name:str):
    """Destroy the UI of the currently in view, spawn off another instance of terrain-grabber with the given location"""
    root.destroy()
    os.system("py run.py " + area_name)
    sys.exit()