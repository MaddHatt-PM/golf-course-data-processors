from pathlib import Path
from typing import List, Tuple

class ProjectAsset:

    def __init__(self, savename:str, p0:Tuple[float, float]=None, p1:Tuple[float, float]=None):
        self.savename:str = savename

        basePath = "SavedAreas/" + savename + "/" 
        self.basePath:Path = Path(basePath)
        self.basePath.mkdir(parents=True, exist_ok=True)

        self.loadFile_path:Path = Path(basePath + savename + ".area")
        self.sateliteImg_path:Path = Path(basePath + "Satelite.tif")
        self.__coordinates:Path = Path(basePath + "Coordinates.csv")
        self.elevationImg_path:Path = Path(basePath + "Elevation.tif")
        self.elevationCSV_path:Path = Path(basePath + "Elevation.csv")
        self.treesCSV_path:Path = Path(basePath + "Trees.csv")

        # If provided, save out coordinates data
        if p0 != None and p1 != None:
            with open(self.__coordinates, 'w') as f:
                f.write("latitude,longitude\n")
                f.write(str(p0) + '\n')
                f.write(str(p1) + '\n')

    def coordinates(self) -> List[tuple[float, float]]:
        if self.__coordinates.exists():
            with open(self.__coordinates, "r") as f:
                lines = f.read().splitlines()
                p0 = eval(lines[1])
                p1 = eval(lines[2])

            return [p0, p1]
            
        else:
            # Maybe throw an error and crash the program?
            return [(1.0, 1.0), (0.0, 0.0)]

    def does_satelite_data_exist(self) -> bool:
        return self.sateliteImg_path.is_file()