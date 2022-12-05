"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022
"""

import sys
import tkinter as tk
from tkinter.ttk import Button, Entry, Frame, Label, Progressbar

class LoadingWindow():
    def __init__(self, isMainWindow=False, loading_text="Loading...") -> None:
        if isMainWindow == True:
            self.window = tk.Tk()
        else:
            self.window = tk.Toplevel()
            self.window.grab_set()
            self.window.focus_force()

        self.window.title("Loading...")

        progress = Progressbar(self.window, orient=tk.HORIZONTAL, length=250 , mode="indeterminate")
        progress.pack(padx=30,pady=4)

        text = Label(self.window, text=loading_text)
        text.pack(pady=4)

        progress.start(interval=10)
        self.window.mainloop()


    def close(self):
        self.window.destroy()

if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) == 2:
        LoadingWindow(isMainWindow=True, loading_text=sys.argv[1])
    else:
        LoadingWindow(isMainWindow=True)
