import tkinter as tk
from tkinter.ttk import Button, Entry, Frame, Label
from utilities import restart_with_new_target
from data_downloader import download_imagery, download_elevation, services, download_elevation_for_location

from asset_project import ProjectAsset

class CreateLocationView:
    def show(self, isMainWindow:bool=False) -> tk.Tk:
        '''
        UI for downloading new areas.
        Popup is designated as the rootUI when no loaded_asset is present
        '''
        if isMainWindow == True:
            self.popup = tk.Tk()
        else:
            self.popup = tk.Toplevel()
            self.popup.grab_set()
            self.popup.focus_force()

        self.popup.resizable(False, False)
        self.filename = tk.StringVar()
        self.error_msg = tk.StringVar()
        self.p0 = tk.StringVar()
        self.p1 = tk.StringVar()

        Label(self.popup, text="Enter two coordinates").grid(row=0)
        Label(self.popup, text="Via Google Maps, right click on a map to copy coordinates").grid(row=1, padx=20)
        Label(self.popup, textvariable=self.error_msg).grid(row=2)

        prompts_f = Frame(self.popup)
        prompts_f.grid(row=3)

        Label(prompts_f, text="Area Name").grid(sticky='w', row=0, column=0)
        Entry(prompts_f, textvariable=self.filename).grid(row=0, column=1)

        Label(prompts_f, text="Coordinate NW").grid(sticky='w', row=1, column=0)
        Entry(prompts_f, textvariable=self.p0).grid(row=1, column=1)

        Label(prompts_f, text="Coordinate SE").grid(sticky='w', row=2, column=0)
        Entry(prompts_f, textvariable=self.p1, ).grid(row=2, column=1)

        buttons_f = Frame(self.popup)
        buttons_f.grid(row=4)
        cancel_btn = Button(buttons_f, text="Cancel", command=self.popup.destroy, width=20)
        cancel_btn.grid(row=0, column=0, sticky="nswe", pady=10)

        enter_btn = Button(buttons_f,
                           text="Enter",
                        #    state=self.validate_enter_btn(filename=filename, pt_a=pt_a, pt_b=pt_b),
                           command=self.execute_download_btn,
                           width=20)

        enter_btn.grid(row=0, column=1, sticky="nswe", pady=10)

        return self.popup

    def execute_download_btn(self):
        '''Validate input, setup download environment, pull data via API, then reload program'''
        
        if self.filename.get().strip() == "":
            self.error_msg.set("Error: Invalid filename: {}".format(self.filename))
            return

        try:
            p0 = eval(self.p0.get())
            p1 = eval(self.p1.get())
        except:
            self.error_msg.set("Error: Invalid points")
            return

        newArea = ProjectAsset(savename=self.filename.get().strip(), p0=p0, p1=p1)
        
        download_imagery(target=newArea, service=services.google_satelite)
        download_elevation_for_location(newArea, services.google_elevation)
        
        restart_with_new_target(self.popup, newArea.savename)
        self.popup.destroy()
