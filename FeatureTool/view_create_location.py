import tkinter as tk
from tkinter.ttk import Button, Entry, Frame, Label
from utilities import restart_with_new_target
from data_downloader import download_imagery, services

from loaded_asset import LoadedAsset

class CreateLocationView:
    def show(self, isMainWindow:bool=False) -> tk.Tk:
        '''
        UI for downloading new areas.
        Popup is designated as the rootUI when no loaded_asset is present
        '''
        if isMainWindow == True:
            popup = tk.Tk()
        else:
            popup=tk.Toplevel()
            popup.grab_set()
            popup.focus_force()

        popup.resizable(False, False)
        self.filename = tk.StringVar()
        self.error_msg = tk.StringVar()
        self.p0 = tk.StringVar()
        self.p1 = tk.StringVar()

        Label(popup, text="Enter two coordinates").grid(row=0)
        Label(popup, text="Via Google Maps, right click on a map to copy coordinates").grid(row=1, padx=20)
        Label(popup, textvariable=self.error_msg).grid(row=2)

        prompts_f = Frame(popup)
        prompts_f.grid(row=3)

        Label(prompts_f, text="Area Name").grid(sticky='w', row=0, column=0)
        Entry(prompts_f, textvariable=self.filename).grid(row=0, column=1)

        Label(prompts_f, text="Coordinate NW").grid(sticky='w', row=1, column=0)
        Entry(prompts_f, textvariable=self.p0).grid(row=1, column=1)

        Label(prompts_f, text="Coordinate SE").grid(sticky='w', row=2, column=0)
        Entry(prompts_f, textvariable=self.p1, ).grid(row=2, column=1)

        buttons_f = Frame(popup)
        buttons_f.grid(row=4)
        cancel_btn = Button(buttons_f, text="Cancel", command=popup.destroy, width=20)
        cancel_btn.grid(row=0, column=0, sticky="nswe", pady=10)

        enter_btn = Button(buttons_f,
                           text="Enter",
                        #    state=self.validate_enter_btn(filename=filename, pt_a=pt_a, pt_b=pt_b),
                           command=self.execute_download_btn,
                           width=20)

        enter_btn.grid(row=0, column=1, sticky="nswe", pady=10)

        return popup

    def execute_download_btn(self):
        '''Validate input, setup download environment, pull data via API, then reload program'''
        
        if self.filename.get().strip() == "":
            self.error_msg.set("Error: Invalid points")
            return

        try:
            eval(self.pt_a.get())
            eval(self.pt_b.get())
        except:
            self.error_msg.set("Error: Invalid points")
            return

        newArea = LoadedAsset(savename=self.filename.get().strip(), p0=eval(self.p0.get()), p1=eval(self.p1.get()))
        print(str(newArea.coordinates()))
        download_imagery(target=newArea, service=services.google_satelite)
        
        restart_with_new_target(newArea.savename)
