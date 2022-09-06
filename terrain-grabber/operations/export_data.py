import os
from pathlib import Path
import shutil
import subprocess
import sys
from tkinter import filedialog
from tkinter.messagebox import askyesno

from asset_project import LocationPaths
from utilities import CornerID, CornerID_to_name

def export_data(target:LocationPaths, testMode=False, corner:CornerID=CornerID.SW, convert_to_feet=True) -> list[Path]:
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

    '''Satelite'''
    copyfiles.append((target.sateliteImg_path, outputdir / 'Satelite.png'))

    '''Elevation Imagery'''
    base_elev_dir = outputdir / 'Elevation'
    base_elev_dir.mkdir(exist_ok=True)
    copyfiles.append((target.elevationImg_nearest_path, base_elev_dir / "Elevation_Nearest.png"))
    copyfiles.append((target.elevationImg_linear_path, base_elev_dir / "Elevation_Linear.png"))
    copyfiles.append((target.sampleDistributionImg_path, base_elev_dir / "Distribution.png"))
    copyfiles.append((target.contourImg_path, base_elev_dir / "Contour.png"))

    '''Point conversion for lat/long to np.arrays for future steps'''
    lats,lons, eles, xOffsets, yOffsets = [],[],[], [], []
    with target.elevationCSV_path.open('r') as file:
        lines = file.read().splitlines()
        headers = lines.pop(0).split(',')

    latID = headers.index('latitude')
    lonID = headers.index('longitude')
    eleID = headers.index('elevation')
    xOffsetID = headers.index('offset-x')
    yOffsetID = headers.index('offset-y')

    for ln in lines:
        raw = ln.split(',')
        pt = [eval(pt) for pt in raw]
        lats.append(pt[latID])
        lons.append(pt[lonID])
        eles.append(pt[eleID])
        xOffsets.append(pt[xOffsetID])
        yOffsets.append(pt[yOffsetID])
    
    if convert_to_feet:
        eles = [pt * 3.28084 for pt in eles]

    '''Elevation Files - Raw'''
    output = 'longitude,latitude,elevation({})\n'.format('ft' if convert_to_feet else 'm')
    for id in range(len(lons)):
        output += '{},{},{}\n'.format(
            lons[id],
            lats[id],
            eles[id]
        )

    elev_raw_path = Path(base_elev_dir / "ElevationPoints_Raw.csv")
    with elev_raw_path.open('w') as file:
        file.write(output)

    '''Elevation Files - Converted & reoriented'''
    x_maxdist, y_maxdist = max(lons), max(lats) 
    if corner is CornerID.NW:
        pass
    elif corner is CornerID.NE:
        xOffsets = [abs(pt - x_maxdist) for pt in xOffsets]
    elif corner is CornerID.SW:
        yOffsets = [abs(pt - y_maxdist) for pt in yOffsets]
    elif corner is CornerID.SE:
        xOffsets = [abs(pt - x_maxdist) for pt in xOffsets]
        yOffsets = [abs(pt - y_maxdist) for pt in yOffsets]

    if convert_to_feet:
        xOffsets = [pt * 3.28084 for pt in xOffsets]
        yOffsets = [pt * 3.28084 for pt in yOffsets]

    output = 'x,y,z\n'
    for id in range(len(xOffsets)):
        output += '{},{},{}\n'.format(
            xOffsets[id],
            yOffsets[id],
            eles[id]
        )

    elev_convert_path = Path(base_elev_dir / "ElevationPoints_From{}".format(CornerID_to_name(corner).upper()))
    with elev_convert_path.open('w') as file:
        file.write(output)

    '''Areas'''
    masks_areas_dir = outputdir / 'Areas' / 'Masks' 
    raw_areas_dir = outputdir / 'Areas' / 'Raw' 
    converted_areas_dir = outputdir / 'Areas' / 'Converted' 
    
    masks_areas_dir.mkdir(exist_ok=True, parents=True)
    raw_areas_dir.mkdir(exist_ok=True, parents=True)
    converted_areas_dir.mkdir(exist_ok=True, parents=True)

    filenames = os.listdir(target.basePath)
    for name in filenames:
        if "_area" in name:
            file_prefix = name.split('_area')[0]

            '''Copy over raw lat/long'''
            raw_pts_file = file_prefix + '_area.csv'
            raw_pts_src = target.basePath / raw_pts_file
            copyfiles.append((raw_pts_src, raw_areas_dir / (file_prefix + '_vertices_raw.csv')))

            '''Reorient to new origin'''
            with raw_pts_src.open('r') as file:
                lines = file.readlines()

            lines.pop(0) # Remove header
            xOffsets, yOffsets = [], []
            for ln in lines:
                values = ln.split(',')
                xOffsets.append(eval(values[1])) # Longitude
                yOffsets.append(eval(values[0])) # Latitude

            if corner is CornerID.NW:
                pass
            elif corner is CornerID.NE:
                xOffsets = [abs(pt - 1.0) for pt in xOffsets]
            elif corner is CornerID.SW:
                yOffsets = [abs(pt - 1.0) for pt in yOffsets]
            elif corner is CornerID.SE:
                xOffsets = [abs(pt - 1.0) for pt in xOffsets]
                yOffsets = [abs(pt - 1.0) for pt in yOffsets]

            reoriented_file = converted_areas_dir / (file_prefix + '_vertices.csv')
            with reoriented_file.open('w') as file:
                file.write('x,y')
                for id in range(len(xOffsets)):
                    file.write('{},{}\n'.format(
                        xOffsets[id] * x_maxdist * 3.28084,
                        yOffsets[id] * y_maxdist * 3.28084,
                    ))
            
            '''Copy over mask files if they exist (they should be pre-generated)'''
            mask_file = file_prefix + '_mask.png'
            mask_src = target.basePath / mask_file
            if mask_src.exists():
                copyfiles.append((mask_src, masks_areas_dir / mask_file))

    '''Hierachy Data'''

    for item in copyfiles:
        shutil.copy(*item)

    '''Open up destination folder'''
    if sys.platform == 'win32':
        os.startfile(str(outputdir))
    elif sys.platform == 'darwin':
        subprocess.check_call(['open', '--', str(outputdir)])

    return [item[1] for item in copyfiles]

if __name__ == '__main__':
    target = LocationPaths('AshevilleClub')
    filepaths = export_data(target, testMode=True)

    if(input('Press \'y\' key to delete: ') == 'y'):
        for item in filepaths:
            item.unlink()