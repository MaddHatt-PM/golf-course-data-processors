import sys
import tkinter as tk
from tkinter import ttk
import modes


class controls:
    def __init__(s) -> None:
        s.root = tk.Tk()
        s.root.resizable = False
        s.root.title("Controls")
        s.root.geometry("250x300+0+0")
        s.root.attributes("-topmost", True)

        s.main_ctrls = [
            "[0] Reset Zoom",
            "[+] Zoom In",
            "[-] Zoom Out",
            "[~] Toggle views",
            "",
            "[1] Switch to Crop Mode",
            "[2] Switch to Rotate Mode",
            "[3] Switch to Color Masker",
            "",
            "[s] Save result",
            "[q] Quit",
        ]

        s.crop_ctrls = [
            "[0] Reset Zoom",
            "[+] Zoom In",
            "[-] Zoom Out",
            "[~] Toggle views",
            "",
            "[left-click] Add new point",
            "[right-click] Remove last point",
            "[enter] Accept crop from two points",
            "",
            "[q] Exit Crop Mode",
        ]

        s.rotate_ctrls = [
            "[0] Reset Zoom",
            "[+] Zoom In",
            "[-] Zoom Out",
            "[~] Toggle views",
            "",
            "[w] Flip vertically",
            "[s] Flip horizontally",
            "[a] Rotate Clockwise 90°",
            "[d] Rotate Counterclockwise 90°",
            "",
            "[q] Exit Rotate Mode",
        ]

        s.flood_mask_ctrls = [
            "[0] Reset Zoom",
            "[+] Zoom In",
            "[-] Zoom Out",
            "[~] Toggle views",
            "",
            "[left-click] Select color",
            "[w] Dilate selections - Bugged",
            "[s] Erode selections - Bugged",
            "[a] Increase sensitivity by +5",
            "[d] Increase sensitivity by -5",
            "[a] Increase sensitivity by +1",
            "[d] Increase sensitivity by -1",
            "[backspace] Reject color",
            "[enter] Accept color",
            "[q] Exit Color Mask Mode",
        ]

        s.world_mask_ctrls = []

        s.mode_controls = {
            modes.M_DEFAULT: s.main_ctrls,
            modes.M_CROP: s.crop_ctrls,
            modes.M_ROTATE: s.rotate_ctrls,
            modes.M_FLOOD_MASKER: s.flood_mask_ctrls,
        }
        s.ui_items = []

        s.sel_mode = modes.M_DEFAULT
        if len(sys.argv) == 2:
            s.sel_mode = sys.argv[1]

        title = tk.Label(
            s.root,
            text=s.sel_mode.capitalize() + " Controls:",
            font=("Arial", 14),
        )
        title.pack(anchor="w")
        s.ui_items.append(title)

        for control in s.mode_controls[s.sel_mode]:
            if control == "":
                sep = ttk.Separator(s.root, orient="horizontal")
                sep.pack(fill="x", pady=4)
                s.ui_items.append(sep)
                continue

            item = tk.Label(s.root, text=control)
            item.pack(anchor="w")
            s.ui_items.append(item)

        s.root.mainloop()

    def writeout_geometry(s):
        pass


if __name__ == "__main__":
    win = controls()
