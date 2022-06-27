
import tkinter as tk
from tkinter import Tk
from tkinter.ttk import Button, Entry, Label
from loaded_asset import LoadedAsset

class create_new_area_window:
    def __init__(self, target:LoadedAsset, isMainWindow:bool=False) -> None:
        if isMainWindow == True:
            self.popup = tk.Tk()
        else:
            self.popup=tk.Toplevel()
            self.popup.grab_set()
            self.popup.focus_force()

        self.popup.resizable(False,False)

        Label(self.popup, text="Area Name").grid(row=0, columnspan=2, pady=10)

        self.error_text = tk.StringVar()
        Label(self.popup, textvariable=self.error_text).grid(row=1, columnspan=2)

        self.new_area_name = tk.StringVar()
        Entry(self.popup, textvariable=self.new_area_name).grid(row=2, columnspan=2)

        enter_btn = Button(self.popup, text="Enter", command=self.validate_and_send)
        enter_btn.grid(row=3, column=0, pady=10, padx=10)

        cancel_btn = Button(self.popup, text="Cancel", command=self.popup.destroy)
        cancel_btn.grid(row=3, column=1, pady=10, padx=10)

        self.popup.mainloop()


    def validate_and_send(self) -> bool:
        invalid_char = list("#%&{}\\<>*?/$!\'\":@+`|=")
        if '\\' in self.new_area_name.get():
            self.error_text.set("Invalid characters in area name, this is a long error")
            return

if __name__ == "__main__":
    create_new_area_window(None, isMainWindow=True)
