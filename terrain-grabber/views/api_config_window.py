"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022
"""

from functools import partial
import tkinter as tk
from pathlib import Path
from tkinter import StringVar
from tkinter.ttk import Entry, Label, Button

def show_api_config(is_main_window=False) -> None:
    """
    Ensure that a .env file exists, then prompts the user for api keys.
    Currently just Google Maps.
    """
    env = Path('.env')

    # Create file if it doesn't exist
    if env.exists() is False:
        with env.open('w', encoding='utf8') as file:
            file.write('')

    apis = {}
    with env.open('r', encoding='utf8') as file:
        for line in file.read().splitlines():
            split = line.split('=')
            apis[split[0]] = split[1]

    if apis.get('google_maps', '') == '':
        apis['google_maps'] = ''

    if is_main_window:
        window = tk.Tk()
    else:
        window = tk.Toplevel()
        window.grab_set()
        window.focus_force()

    window.title("API Request")
    window.geometry("350x200")
    window.grid_columnconfigure(0, weight = 1)
    window.grid_columnconfigure(1, weight = 1)

    google_maps = Label(window, text="Google Maps")
    google_maps.grid(row=0, column=0)

    api_var = StringVar()
    api_var.set(apis['google_maps'])

    def on_change_api(*args, **kwargs):
        apis['google_maps'] = api_var.get()

    api_var.trace_add('write', on_change_api)
    area_entry = Entry(window, textvariable=api_var)
    area_entry.grid(row=0, column=1, sticky='ew')

    # Confirmation Buttons
    cancel_btn = Button(window, text="Cancel", command=window.destroy)
    cancel_btn.grid(row=4, column=0, sticky='ew')

    def write_env():
        output = ''
        for key in apis.keys():
            output += '{}={}\n'.format(key, apis[key])

        with env.open('w', encoding='utf8') as file:
            file.write(output.removesuffix('\n'))

        window.destroy()

    closure = partial (write_env)
    enter_btn = Button(window, text="Enter", command=closure)
    enter_btn.grid(row=4, column=1, sticky='ew')

    window.mainloop()

if __name__ == '__main__':
    show_api_config(is_main_window=True)