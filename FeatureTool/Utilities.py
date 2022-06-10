from enum import Enum

class color_set:
    def __init__(self, path:str, fill:str) -> None:
        self.path = path
        self.fill = fill

class ui_colors:
    # Colors: https://materialui.co/colors/
    canvas_col:str = "#212121"
    ui_bgm_col:str = "#424242" 

    red = color_set(path="#EF5350", fill="#B71C1C")
    pink = color_set(path="#EC407A", fill="#880E4F")
    purple = color_set(path="#AB47BC", fill="#4A148C")
    indigo = color_set(path="#5C6BC0", fill="#1A237E")
    blue = color_set(path="#42A5F5", fill="#0D47A1")
    cyan = color_set(path="#26C6DA", fill="#006064")
    teal = color_set(path="#26A69A", fill="#004D40")
    green = color_set(path="#7CB342", fill="#66BB6A")
    orange = color_set(path="#FFA726", fill="#FF6F00")
    brown = color_set(path="#A1887F", fill="#4E342E")
    


class coord_mode(Enum):
    normalized = 0,
    pixel = 1,
    earth = 2

class tool_mode(Enum):
    default = 0