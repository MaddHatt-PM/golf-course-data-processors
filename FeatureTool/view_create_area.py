
import tkinter as tk
from tkinter.ttk import Button, Entry, Label
from asset_area import AreaAsset

class CreateAreaView:
    def show(self, areas:list[AreaAsset], isMainWindow:bool=False) -> None:
        if isMainWindow == True:
            self.popup = tk.Tk()
        else:
            self.popup=tk.Toplevel()
            self.popup.grab_set()
            self.popup.focus_force()

        self.areas = areas
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

    # def show(self):
    #     self.popup.mainloop()


    def validate_and_send(self) -> bool:
        invalid_char = list("#%&{}\\<>*?/$!\'\":@+`|=")
        for character in invalid_char:
            if character in self.new_area_name.get():
                self.error_text.set("Invalid character: [{}]".format(character))
                return

        for area in self.areas:
            if area.name == self.new_area_name.get():
                self.error_text.set("Name taken")
                return
            

if __name__ == "__main__":
    CreateAreaView(None, isMainWindow=True)