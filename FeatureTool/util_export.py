import os
from pathlib import Path
import shutil
from tkinter import SW, filedialog, commondialog
from tkinter.messagebox import askyesno

import numpy as np
from asset_area import AreaAsset

from asset_project import ProjectAsset
from utilities import CornerID_LatLong

def export_data(target:ProjectAsset, testMode=False, corner:CornerID_LatLong=SW, convert_to_feet=False) -> list[Path]:
    outputdir = filedialog.askdirectory(
        title='Select directory for export',
        mustexist=True,
    )

    if outputdir == '':
        return
    
    outputdir = Path(outputdir) / (target.savename + "Data")
    if outputdir.exists():
        if askyesno(title='Existing folder found', message='Overwrite and merge data?') is False:
            return
    
    outputdir.mkdir(parents=True, exist_ok=True)
    copyfiles:list[Path,Path] = []
    delfiles:list[Path] = []

    '''Satelite'''
    copyfiles.append((target.sateliteImg_path, outputdir / 'Satelite.png'))

    '''Elevation Imagery'''
    base_elev_dir = outputdir / 'Elevation'
    base_elev_dir.mkdir(exist_ok=True)
    copyfiles.append((target.elevationImg_nearest_path, base_elev_dir / "Elevation_Nearest.png"))
    copyfiles.append((target.elevationImg_linear_path, base_elev_dir / "Elevation_Linear.png"))
    copyfiles.append((target.datapointImg_path, base_elev_dir / "Distribution.png"))
    copyfiles.append((target.contourImg_path, base_elev_dir / "Contour.png"))

    '''Point conversion for lat/long to np.arrays for future steps'''
    lats,lons, eles = [],[],[]
    with target.elevationCSV_path.open('r') as file:
        lines = file.read().splitlines()
        headers = lines.pop(0).split(',')

    latID = headers.index('latitude')
    lonID = headers.index('longitude')
    eleID = headers.index('elevation') if 'elevation' not in headers else None

    for ln in lines:
        raw = ln.split(',')
        pt = [eval(pt) for pt in raw]
        lats.append(pt[latID])
        lons.append(pt[lonID])
        if eleID is not None:
            eles.append(pt[eleID])
    
    lats,lons = np.array(lats), np.array(lons)

    '''Corners'''
    operations = {
        'NW' : (np.max, np.min),
        'NE' : (np.max, np.max),
        'SE' : (np.min, np.min),
        'SW' : (np.min, np.max)
    }
    corners = []
    corners_str = []
    for key in operations.keys():
        op = operations[key]
        coords = op[0](lats), op[1](lons)
        corners.append(coords)
        corners_str.append(key + ':' + str(coords[0]) + ',' + str(coords[1]))

    corners_str = '\n'.join(corners_str)

    corners_path = Path(base_elev_dir / "Corners.csv")
    with corners_path.open('w') as file:
        file.write(corners_str)

    '''Elevation conversion'''
    elev_csv = Path( base_elev_dir / "ElevationPoints.csv")

    '''Areas'''
    base_areas_dir = outputdir / 'Areas'
    base_areas_dir.mkdir(exist_ok=True)

    filenames = os.listdir(target.basePath)
    area_suffixes = [
        '_area.csv',
        '_mask.png'
    ]
    for name in filenames:
        if "_area" in name:
            file_prefix = name.split('_area')[0]
            
            '''Copy over mask files if they exist (they should be pregenerated)'''
            mask_file = (file_prefix + area_suffixes[1])
            mask_src = target.basePath / mask_file
            if mask_src.exists():
                copyfiles.append((mask_src, base_areas_dir / mask_file))
                delfiles.append(mask_src)
            
            '''Reorient to points'''


    for item in copyfiles:
        shutil.copy(*item)

    for item in delfiles:
        if testMode:
            print('[TestMode On] {} would have been deleted from project folder'.format(item.name))
            continue
        
        item.unlink(missing_ok=True)

    '''Hierachy Data'''
    
    return [item[1] for item in copyfiles]

if __name__ == '__main__':
    target = ProjectAsset('AshevilleClub')
    filepaths = export_data(target, testMode=True)

    if(input('Press \'y\' key to delete: ') == 'y'):
        for item in filepaths:
            item.unlink()