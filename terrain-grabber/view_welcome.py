from functools import partial
import os, sys
import tkinter as tk
from tkinter import ttk
from utilities import restart_with_new_target
from view_create_location import CreateLocationView

def show_welcome():
    popup = tk.Tk()
    popup.title('Terrain Grabber - Welcome')
    popup.resizable(0, 0)
    popup.grid_columnconfigure(0, weight=1)

    def on_close():
        sys.exit()

    popup.protocol("WM_DELETE_WINDOW", on_close)

    tk.Label(popup, text='Open a recent location', fg="#616161").pack(padx=100)

    directories = os.listdir('SavedAreas/')
    for dir in directories:
        closure = partial(restart_with_new_target, popup, dir)
        ttk.Button(popup, text=dir, command=closure).pack(ipadx=32)

    ttk.Separator(popup, orient='horizontal').pack(fill='x', pady=8)

    def show_create_location():
        popup.destroy()
        CreateLocationView().show(True)

    ttk.Button(popup, text='Grab new location', command=show_create_location).pack(ipadx=32, pady=8)

    popup.mainloop()