"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022
"""

from functools import partial
import os, sys
import tkinter as tk
from tkinter import ttk

from operations import restart_with_location
from .create_location_window import show_create_location

def show_welcome():
    """
    Present a window of available areass to choice from and the option to grab another location.
    """
    popup = tk.Tk()
    popup.title('Terrain Grabber - Welcome')
    popup.resizable(0, 0)
    popup.grid_columnconfigure(0, weight=1)

    def on_close():
        sys.exit()

    popup.protocol("WM_DELETE_WINDOW", on_close)

    tk.Label(popup, text='Open a recent location', fg="#616161").pack(padx=100)

    locations = os.listdir('../SavedAreas/')
    
    for location in locations:
        closure = partial(restart_with_location, popup, location)
        ttk.Button(popup, text=location, command=closure).pack(ipadx=32)

    ttk.Separator(popup, orient='horizontal').pack(fill='x', pady=8)

    def setup_for_create_location():
        popup.destroy()
        show_create_location(isMainWindow=True)

    ttk.Button(popup, text='Grab new location', command=setup_for_create_location).pack(ipadx=32, pady=8)

    popup.mainloop()