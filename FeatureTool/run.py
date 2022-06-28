'''
@Author 2022: Patt Martin
Description:
    Start up the Terrain Editor by user or by the program as a reload system
    through system arguements

TaskList:
    - Check for required packages and output a log of the ones not installed
        - Can a python script install stuff it needs or is that considered malicious?
        - https://stackoverflow.com/questions/12332975/installing-python-module-within-code
'''

from view_main_window import MainWindow
from asset_project import ProjectAsset
import sys


if len(sys.argv) == 1:
    target=None
else:
    target=ProjectAsset(savename=sys.argv[1])

app = MainWindow(target).show()
app.mainloop()