from pathlib import Path
from typing import List, Tuple

class loaded_asset:

    def __init__(self, savename:str, p0:Tuple[float, float]=None, p1:Tuple[float, float]=None):
        self.saveName:str = savename

        basePath = "SavedAreas/" + savename + "/" 
        Path(basePath).mkdir(parents=True, exist_ok=True)

        self.loadFile:Path = Path(basePath + savename + ".area")
        self.sateliteImg:Path = Path(basePath + "Satelite.tif")
        self.__coordinates:Path = Path(basePath + "Coordinates.csv")
        self.elevationImg:Path = Path(basePath + "Elevation.tif")
        self.elevationCSV:Path = Path(basePath + "Elevation.csv")

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
        return self.sateliteImg.is_file()

    def saveName(self): return self.saveName
    def loadFile_path(self): return self.loadFile
    def sateliteImg_path(self): return self.sateliteImg
    def elevationImg_path(self): return self.elevationImg
    def elevationCSV_path(self): return self.elevationCSV