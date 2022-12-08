"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022
"""

from pathlib import Path

class LocationPaths:
    """
    Utility object to hold filepaths, check for existing files, and to supply location coordinates
    """
    def __init__(self, savename:str, p0:tuple[float, float]=None, p1:tuple[float, float]=None, apis=None):
        self.savename:str = savename

        basepath = "../SavedAreas/" + savename + "/" 
        self.basepath:Path = Path(basepath)
        self.basepath.mkdir(parents=True, exist_ok=True)

        self.env = Path('.env')
        self.apis = apis

        self.loadfile_path:Path = Path(basepath + savename + ".area")
        self.satelite_img_path:Path = Path(basepath + "Satelite.png")
        self.coordinates_path:Path = Path(basepath + "Coordinates.csv")
        self.layers_path:Path = Path(basepath + "Layers.json")
        self.elevation_img_nearest_path:Path = Path(basepath + "Elevation_Nearest.png")
        self.elevation_img_linear_path:Path = Path(basepath + "Elevation_Linear.png")
        self.tangent_normal_path:Path = Path(basepath + "Tangent_Normal.png")
        self.sample_distribution_img_path:Path = Path(basepath + "Sample_Distribution.png")
        self.contour_img_path:Path = Path(basepath + "Contour.png")
        self.elevation_csv_path:Path = Path(basepath + "Elevation.csv")
        self.trees_csv_path:Path = Path(basepath + "Trees.csv")

        self.offset_path:Path = Path(basepath + "offset.csv")

        # If provided, save out coordinates data
        if p0 is not None and p1 is not None:
            with open(self.coordinates_path, 'w', encoding='utf8') as f:
                f.write("latitude,longitude\n")
                f.write(str(p0) + '\n')
                f.write(str(p1) + '\n')

    def coordinates(self) -> list[tuple[float, float]]:
        """
        Load in the location's coordinates, [(N,W), (S,E)]
        """
        if self.coordinates_path.exists():
            with open(self.coordinates_path, "r", encoding='utf8') as f:
                lines = f.read().splitlines()
                p0 = eval(lines[1])
                p1 = eval(lines[2])

            return [p0, p1]

        else:
            # Maybe throw an error and crash the program?
            return [(1.0, 1.0), (0.0, 0.0)]

    def does_satelite_img_exist(self) -> bool:
        """Helper function to determine if the file exists"""
        return self.satelite_img_path.is_file()
