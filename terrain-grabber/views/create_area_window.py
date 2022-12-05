"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022
"""

from tkinter import simpledialog
from tkinter.messagebox import showerror
from asset_area import AreaAsset

def show_create_area(caller, areas:list[AreaAsset], isMainWindow:bool=False, parent=None) -> None:
    """
    Create a prompt for the user to enter a valid area name.
    Then pass the name to view_main_window to handle the rest.
    """
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

    # Can't reference view_main_window due to circular import :(
    # Will have to just trust me on this
    caller.create_new_area(name=new_area_name)