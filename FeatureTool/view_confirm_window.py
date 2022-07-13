import tkinter as tk
from tkinter import Label, Entry, Button
from tkinter import ttk

class CreateConfirmView:
    def __init__(self, text:str, command, isMainWindow:bool=False):
        if isMainWindow == True:
            popup = tk.Tk()
        else:
            popup = tk.Toplevel()
            popup.grab_set()
            popup.focus_force()
        
        popup.resizable(False, False)
        # popup.geometry("330x120")
        popup.title("Confirmation")

        if text == "":
            text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam non."

        Label(popup, text=text, justify='center', wraplength=280).grid(row=0, columnspan=2, pady=10, padx=20)

        enter_btn = ttk.Button(popup, text="  OK  ", command=command)
        enter_btn.grid(row=2, column=0, pady=10, padx=10, sticky='ew')

        cancel_btn = ttk.Button(popup, text="Cancel", command=popup.destroy)
        cancel_btn.grid(row=2, column=1, pady=10, padx=10, sticky='ew')

        popup.grid_columnconfigure((0,1,2), weight=1)
        popup.grid_rowconfigure(0, weight=1)

        if isMainWindow is True:
            popup.mainloop()

if __name__ == "__main__":
    def test_print():
        print("test")

    CreateConfirmView(text="", command=test_print, isMainWindow=True)