import os
from pathlib import Path
import shutil
from tkinter import filedialog, commondialog
from tkinter.messagebox import askyesno
from asset_area import AreaAsset

from asset_project import ProjectAsset

def export_data(target:ProjectAsset, testMode=False) -> list[Path]:
        outputdir = filedialog.askdirectory(
            title='Select directory for export',
            mustexist=True,
        )
        
        outputdir = Path(outputdir) / (target.savename + "Data")
        if outputdir.exists():
            if askyesno(title='Existing folder found', message='Overwrite and merge data?') is False:
                return
        
        outputdir.mkdir(parents=True, exist_ok=True)
        copyfiles:list[Path,Path] = []
        delfiles:list[Path] = []

        '''Satelite'''
        copyfiles.append((target.sateliteImg_path, outputdir / 'Satelite.png'))

        '''Elevation'''
        base_elev_dir = outputdir / 'Elevation'
        base_elev_dir.mkdir(exist_ok=True)
        copyfiles.append((target.elevationImg_nearest_path, base_elev_dir / "Elevation_Nearest.png"))
        copyfiles.append((target.elevationImg_linear_path, base_elev_dir / "Elevation_Linear.png"))
        copyfiles.append((target.datapointImg_path, base_elev_dir / "Distribution.png"))
        copyfiles.append((target.contourImg_path, base_elev_dir / "Contour.png"))
        copyfiles.append((target.elevationCSV_path, base_elev_dir / "ElevationPoints.csv"))

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
                
                mask_file = (file_prefix + area_suffixes[1])
                mask_src = target.basePath / mask_file
                if mask_src.exists():
                    copyfiles.append((mask_src, base_areas_dir / mask_file))
                    delfiles.append(mask_src)
                

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