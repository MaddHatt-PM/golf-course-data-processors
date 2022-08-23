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

from api_keys import read_env
from view_config_apis_window import ConfigAPIsWindow
from view_main_window import MainWindow
from asset_project import ProjectAsset
from pathlib import Path
import sys




# Attempt to load dot file
apis = read_env()
if len(apis) == 0:
    ConfigAPIsWindow(isMainWindow=True)

    '''Give the user another chance for API'''
    apis = read_env()
    if (len(apis) == 0):
        # TODO: Would be nice to have a prompt window
        print('No APIS Given. Terminating program.')
        sys.exit()


if len(sys.argv) == 1:
    target=None
else:
    target=ProjectAsset(savename=sys.argv[1])

    


app = MainWindow(target).show()
app.mainloop()