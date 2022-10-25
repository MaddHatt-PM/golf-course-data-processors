import os
from pathlib import Path
import shutil
import subprocess
import sys
from tkinter import filedialog
from tkinter.messagebox import askyesno

from asset_project import LocationPaths
from utilities import CornerID, CornerID_to_name

def export_data(target:LocationPaths, testMode=False) -> list[Paths]:
    outputdir = filedialog.askdirectory(
        title='Select directory for export',
        mustexist=True
    )

    if outputdir == '':
        return

    obj_path = Path(outputdir) / "Model" / (target.savename + ".obj")
    mtl_path = Path(outputdir) / "Model" / (target.savename + ".mtl")
    texture_file = Path(target.savename + "_diff.png")
    texture_path = Path(outputdir) / "Model" / texture_file
    
    '''
    MTL -> Material Info File
    File Format Spec: https://www.loc.gov/preservation/digital/formats/fdd/fdd000508.shtml
    '''
    with mtl_path.open('w') as file:
        output = [
            '# Terrain Grabber File: \'None\'',
            '# Material Count: 1',
            '',
            'newmtl None',
            'Ns 500', # Specular highlights  [0, 1000]
            'Ka 0.8 0.8 0.8', # Ambient Color [0.0, 1.0]
            'Kd 0.8 0.8 0.8', # Diffuse Color [0.0, 1.0]
            'Ks 0.8 0.8 0.8', # Specular Color [0.0, 1.0]
            'd 1', # Transparency [0.0,1.0]
            'illum 2', # Illumination Mode
            'map_kd ' + texture_file, # Diffuse Texture
        ]

        file.write('\n'.join(output))
        