import tkinter as tk
from tkinter.ttk import Button, Entry, Frame, Label

class grab_location_window:
    def __init__(self, isMainWindow:bool=False) -> None:
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
                        #    command=self.execute_download_btn,
                           width=20)

        enter_btn.grid(row=0, column=1, sticky="nswe", pady=10)

        popup.mainloop()

grab_location_window(True)