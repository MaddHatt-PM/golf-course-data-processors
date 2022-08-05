
from functools import partial
import tkinter as tk
from pathlib import Path
from tkinter import StringVar
from tkinter.ttk import Entry, Label, Button


class ConfigAPIsWindow:
    def __init__(self, isMainWindow=False) -> None:
        self.env = Path('.env')

        '''Create file if it doesn't exist'''
        if self.env.exists() is False:
            with self.env.open('w') as file:
                file.write('')

        self.apis = {}
        with self.env.open('r') as file:
            for line in file.read().splitlines():
                split = line.split('=')
                self.apis[split[0]] = split[1]

        if self.apis.get('google_maps', '') == '':
            self.apis['google_maps'] = ''



        if isMainWindow == True:
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
        api_var.set(self.apis['google_maps'])

        def onChangeAPI(*args, **kwargs):
            self.apis['google_maps'] = api_var.get()

        api_var.trace_add('write', onChangeAPI)
        area_entry = Entry(window, textvariable=api_var)
        area_entry.grid(row=0, column=1, sticky='ew')

        '''Confirmation Buttons'''
        cancel_btn = Button(window, text="Cancel", command=window.destroy)
        cancel_btn.grid(row=4, column=0, sticky='ew')

        def write_env(self:ConfigAPIsWindow):
            output = ''
            for key in self.apis.keys():
                output += '{}={}\n'.format(key, self.apis[key])

            with self.env.open('w') as file:
                file.write(output.removesuffix('\n'))
            
            window.destroy()
            
        closure = partial (write_env, self)
        enter_btn = Button(window, text="Enter", command=closure)
        enter_btn.grid(row=4, column=1, sticky='ew')

        window.mainloop()

if __name__ == '__main__':
    ConfigAPIsWindow(isMainWindow=True)