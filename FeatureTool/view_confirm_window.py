import tkinter as tk
from tkinter import Label, Entry, Button

class CreateConfirmView:
    def show(self, text:str, command, isMainWindow:bool=False):
        if isMainWindow == True:
            popup = tk.Tk()
        else:
            popup = tk.Toplevel()
            popup.grab_set()
            popup.focus_force()
        
        popup.resizable(False, False)

        Label(popup, text="Area Name").grid(row=0, columnspan=2, pady=10)

        self.error_text = tk.StringVar()
        Label(popup, textvariable=self.error_text).grid(row=1, columnspan=2)

        self.new_area_name = tk.StringVar()
        Entry(popup, textvariable=self.new_area_name).grid(row=2, columnspan=2)

        enter_btn = Button(popup, text="Enter", command=command)
        enter_btn.grid(row=3, column=0, pady=10, padx=10)

        cancel_btn = Button(popup, text="Cancel", command=popup.destroy)
        cancel_btn.grid(row=3, column=1, pady=10, padx=10)

        if isMainWindow is True:
            popup.mainloop()

if __name__ == "__main__":
    def test_print():
        print("test")

    CreateConfirmView().show(text="Warning", command=test_print, isMainWindow=True)