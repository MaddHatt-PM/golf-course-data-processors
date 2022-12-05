"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022
"""

class ColorSet:
    def __init__(self, path:str, fill:str) -> None:
        self.path = path
        self.fill = fill

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ColorSet):
            return NotImplemented
            
        return self.path == other.path and self.fill == other.fill

class UIColors:
    # Colors: https://materialui.co/colors/
    canvas_col:str = "#212121"
    ui_bgm_col:str = "#424242" 

    red = ColorSet(path="#EF5350", fill="#B71C1C")
    pink = ColorSet(path="#EC407A", fill="#880E4F")
    purple = ColorSet(path="#AB47BC", fill="#4A148C")
    indigo = ColorSet(path="#5C6BC0", fill="#1A237E")
    blue = ColorSet(path="#42A5F5", fill="#0D47A1")
    cyan = ColorSet(path="#26C6DA", fill="#006064")
    teal = ColorSet(path="#26A69A", fill="#004D40")
    green = ColorSet(path="#7CB342", fill="#66BB6A")
    orange = ColorSet(path="#FFA726", fill="#FF6F00")
    brown = ColorSet(path="#A1887F", fill="#4E342E")

    colors = [
        red,
        pink,
        purple,
        indigo,
        blue,
        cyan,
        teal,
        green,
        orange,
        brown
    ]

    names = [
        "red",
        "pink",
        "purple",
        "indigo",
        "blue",
        "cyan",
        "teal",
        "green",
        "orange",
        "brown"
    ]