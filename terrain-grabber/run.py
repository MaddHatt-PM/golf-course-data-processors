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

import os
import sys
import tkinter as tk
from tkinter.messagebox import showerror 

from api_keys import read_env
from view_config_apis_window import ConfigAPIsWindow
from view_main_window import MainWindow
from asset_project import ProjectAsset

import view_welcome

# '''Ensure that'''
os.chdir(os.path.dirname(os.path.realpath(__file__)))

'''Attempt to load dot file'''
apis = read_env()
if len(apis) == 0:
    ConfigAPIsWindow(isMainWindow=True)

    '''Give the user another chance for API'''
    apis = read_env()
    if (len(apis) == 0):
        print('No APIS Given. Terminating program.')
        sys.exit()

if len(sys.argv) == 1:
    target=None
    view_welcome.show_welcome()

else:
    '''User specified a location to load'''
    if sys.argv[1] not in os.listdir('./SavedAreas'):
        showerror(title='Terrain Grabber - Error',message='"{}" does not exist in the SavedAreas directory.\nTerrain Grabber will now exit.'.format(sys.argv[1]))
        sys.exit()

    target=ProjectAsset(savename=sys.argv[1])
    MainWindow(target).show()