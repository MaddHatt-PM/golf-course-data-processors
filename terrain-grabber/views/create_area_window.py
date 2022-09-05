from tkinter import simpledialog
from tkinter.messagebox import showerror
from asset_area import AreaAsset

def show_create_area(caller, areas:list[AreaAsset], isMainWindow:bool=False, parent=None) -> None:
    spacer = '                    '
    new_area_name = simpledialog.askstring(
        title='New area name',
        prompt= spacer + 'Enter a name for the new area' + spacer,
        parent=parent
    )

    if new_area_name is None or new_area_name == "":
        return

    invalid_char = list("#%&{\\}<>*?/$!\'\":@+`|=")
    for c in invalid_char:
        if c in new_area_name:
            showerror(title='error', message='Invalid character: {}'.format(c))
            return

    for area in areas:
        if area.name == new_area_name:
            showerror(title='error', message='Name is already assigned')
            return

    caller.create_new_area(name=new_area_name)