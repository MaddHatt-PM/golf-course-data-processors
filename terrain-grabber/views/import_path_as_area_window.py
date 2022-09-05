from functools import partial
from pathlib import Path
import tkinter as tk
from tkinter import Entry, IntVar, Label, StringVar, filedialog
from tkinter import ttk
from asset_area import HEADER
# from view_main_window import MainWindow

def show_import_path_as_area(caller=None, isMainWindow=False) -> None:
    '''Prompt for CSV file'''
    filetypes = (
        ('CSV files', '*.csv'),
        ('All files', '*.*')
    )

    filepath = filedialog.askopenfilename(filetypes=filetypes)
    if filepath == '' or '.csv' not in filepath:
        return

    filepath = Path(filepath)

    '''Preprocess the csv file'''
    with filepath.open() as file:
        lines = file.read().splitlines()

        if len(lines) < 1:
            print("Too few lines in file")
            return

        headers = lines.pop(0).split(',')
        if len(headers) < 1:
            print("Too few headers to work with")
            return

        raw_data = []
        for ln in lines:
            raw_data.append(ln.split(','))


    '''Ask user for info'''
    if isMainWindow == True:
        popup = tk.Tk()
    else:
        popup = tk.Toplevel()
        popup.grab_set()
        popup.focus_force()
    
    popup.title("Import CSV")
    popup.geometry("350x200")
    popup.grid_columnconfigure(0, weight=1)
    popup.grid_columnconfigure(1, weight=1)

    area_label = Label(popup, text="New Area Name")
    area_label.grid(row=0, column=0)

    area_var = StringVar()
    area_entry = Entry(popup, textvariable=area_var)
    area_entry.grid(row=0, column=1, sticky='ew')

    '''[0] Latitude'''
    lat_label = Label(popup, text="Latitude")
    lat_label.grid(row=1, column=0)

    lat_var = StringVar()
    lat_var.set(headers[0])
    lat_dropdown = ttk.OptionMenu(popup, lat_var, lat_var.get(), *headers)
    lat_dropdown.grid(row=1, column=1, sticky='ew')

    '''[1] Longitude'''
    long_label = Label(popup, text="Longitude")
    long_label.grid(row=2, column=0)

    long_var = StringVar()
    long_var.set(headers[1])
    long_dropdown = ttk.OptionMenu(popup, long_var, long_var.get(), *headers)
    long_dropdown.grid(row=2, column=1, sticky='ew')

    '''[2] Elevation'''
    elev_label = Label(popup, text="Elevation (Optional)")
    elev_label.grid(row=3, column=0)

    elev_var = StringVar()
    elev_dropdown = ttk.OptionMenu(popup, elev_var, elev_var.get(), *headers)
    elev_dropdown.grid(row=3, column=1, sticky='ew')

    '''Confirmation Buttons'''
    cancel_btn = ttk.Button(popup, text="Cancel", command=popup.destroy)
    cancel_btn.grid(row=4, column=0, sticky='ew')

    def process_input(caller, area_name, headers:list[str], raw_data:list[str], header_0:str, header_1:str, header_2:str="", header_3:str=""):
        '''Write filedata for area'''
        file_data = HEADER
        header_ids = []
        header_ids.append(headers.index(header_0))
        header_ids.append(headers.index(header_1))
        
        if (header_2 != ""):
            header_ids.append(headers.index(header_2))
        if (header_3 != ""):
            header_ids.append(headers.index(header_3))

        for item in raw_data:
            line = ''
            for id in header_ids:
                line += ',' + item[id]
            file_data += line.removeprefix(',') + '\n'

        popup.destroy()
        caller.create_new_area(name=area_var.get(), data=file_data)
        

    closure = partial (process_input, caller, area_var.get(), headers, raw_data, lat_var.get(), long_var.get())

    enter_btn = ttk.Button(popup, text="Enter", command=closure)
    enter_btn.grid(row=4, column=1, sticky='ew')

    if isMainWindow is True:
        popup.mainloop()
    