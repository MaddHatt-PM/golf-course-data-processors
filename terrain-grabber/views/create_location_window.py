import tkinter as tk
from tkinter.ttk import Button, Entry, Frame, Label
from operations import restart_with_location
from operations.download_data import download_imagery, download_elevation_for_location, services

from asset_project import LocationPaths

def show_create_location(isMainWindow:bool=False) -> tk.Tk:
    '''
    UI for downloading new areas.
    Popup is designated as the rootUI when no loaded_asset is present
    '''
    if isMainWindow == True:
        popup = tk.Tk()
    else:
        popup = tk.Toplevel()
        popup.grab_set()
        popup.focus_force()

    popup.resizable(False, False)
    filename = tk.StringVar()
    error_msg = tk.StringVar()
    p0 = tk.StringVar()
    p1 = tk.StringVar()

    Label(popup, text="Enter two coordinates").grid(row=0)
    Label(popup, text="Via Google Maps, right click on a map to copy coordinates").grid(row=1, padx=20)
    Label(popup, textvariable=error_msg).grid(row=2)

    prompts_f = Frame(popup)
    prompts_f.grid(row=3)

    Label(prompts_f, text="Area Name").grid(sticky='w', row=0, column=0)
    Entry(prompts_f, textvariable=filename).grid(row=0, column=1)

    Label(prompts_f, text="Coordinate NW").grid(sticky='w', row=1, column=0)
    Entry(prompts_f, textvariable=p0).grid(row=1, column=1)

    Label(prompts_f, text="Coordinate SE").grid(sticky='w', row=2, column=0)
    Entry(prompts_f, textvariable=p1, ).grid(row=2, column=1)

    buttons_f = Frame(popup)
    buttons_f.grid(row=4)
    cancel_btn = Button(buttons_f, text="Cancel", command=popup.destroy, width=20)
    cancel_btn.grid(row=0, column=0, sticky="nswe", pady=10)

    def execute_download_btn():
        '''Validate input, setup download environment, pull data via API, then reload program'''
        
        if filename.get().strip() == "":
            error_msg.set("Error: Invalid filename: {}".format(filename))
            return

        try:
            p0_val = eval(p0.get())
            p1_val = eval(p1.get())
        except:
            error_msg.set("Error: Invalid points")
            return

        newArea = LocationPaths(savename=filename.get().strip(), p0=p0_val, p1=p1_val)
        download_imagery(target=newArea, service=services.google_satelite)
        download_elevation_for_location(newArea, services.google_elevation)
        restart_with_location(popup, newArea.savename)

    enter_btn = Button(buttons_f,
                        text="Enter",
                        command=execute_download_btn,
                        width=20)

    enter_btn.grid(row=0, column=1, sticky="nswe", pady=10)

    return popup