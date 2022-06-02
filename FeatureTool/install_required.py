'''
@Author 2022: Patt Martin
@Last Updated: June 2 2022

Description:
    Run this file to pip install 
'''

import sys
import subprocess
from importlib import util as import_util

def try_to_install(import_name:str, pip_name:str = None):
    if pip_name is None:
        pip_name = import_name

    if import_util.find_spec(import_name) is None:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', pip_name])

packages = [
    "numpy",
    "scipy",
    "pandas",
    "plotly",
    "openpyxl",
    "ttkthemes",
    "pyautogui",
    "matplotlib",
    "geographiclib",
]

# Tuple format: ('import name, pip name')
diff_name_packages = [
    ('cv2', "opencv-python")
]




for pkg in packages:
    try_to_install(pkg)

for pkg in diff_name_packages:
    try_to_install(pkg[0], pkg[1])

print("All packages installed and accounted for Terrain Editor")