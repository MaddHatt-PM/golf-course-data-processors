'''
Super ellipse equation: https://www.desmos.com/calculator/byif8mjgy3
'''

from pathlib import Path
import sys
from tkinter import Canvas

from black import out

from asset_project import ProjectAsset
from utilities import clamp01

class TreeAsset:
    global taper_range; taper_minmax = 0.0, 1.0
    global curvature_range; curvature_range = 0.5, 15.0

    def __init__(self, header:str="", data:str="", position_x=0.5, position_y=0.5) -> None:
        self.trunk_radius = 1.0
        self.trunk_height = 2.0
        self.trunk_offset = 0.0
        self.trunk_lower_taper = 0.0
        self.trunk_upper_taper = 0.0

        self.foliage_radius = 2.5
        self.foliage_height = 5.0
        self.foliage_offset = 0.0
        self.foliage_lower_curv = 2.0
        self.foliage_midpoint = 0.5
        self.foliage_upper_curv = 2.0

        self.position_x = position_x
        self.position_y = position_y

        self._name = ""

        if header != "" and data != "":
            variables = zip(header.split(','), data.split(','))
            for itemset in variables:
                if itemset[0] in self.__dict__:
                    self.__setattr__(itemset[0], eval(itemset[1]))
                else:
                    print("TreeAsset: {} not in __init__ variables".format(itemset[0]))

    def load_preset(self, tree:"TreeAsset"):
        preset = tree.__dict__
        for key in preset.keys():
            if "trunk" in key or "foliage" in key:
                self.__setattr__(key, preset[key])

    def to_csv(self, include_name=False) -> str:
        '''
        Variables beginning with an underscore are omitted
        '''
        output = ""
        if include_name:
            output +="{},".format(self._name)

        for item in self.__dict__:
            if item[0] != '_':
                output += "{},".format(self.__dict__[item])
            
        output = output.removesuffix(',')
        return output

    def header(self, include_name=False) -> str:
        output = ""
        if include_name:
            output +="{},".format("_name")

        for item in self.__dict__:
            if item[0] != '_':
                output += "{},".format(item)
            
        output = output.removesuffix(',')
        return output

    def demo(self):
        print(self.__dict__["trunk_radius"])
        # variables = locals()
        # variables.__setitem__("trunk_radius", 999.999)
        self.__setattr__("trunk_radius", 999.999)

    def sample_point(self, value01):
        '''
        Input values are clamped to 01 space.
        Input values are shifted to their corresponding
        curve (lower or upper)
        '''
        x = clamp01(value01)
        invert = (x <= 0.5)
        x = abs((x-0.5) * 2.0)

        curvature = self.foliage_lower_curv
        if invert:
            self.foliage_upper_curv

        y = pow((1.0 - pow(x , curvature)), 1.0 / curvature)
        if invert:
            y = -y
        return y

    def generate_foliage_profile(self, sample_count=16) -> list[tuple[float, float]]:
        radius = self.foliage_radius
        height = self.foliage_height
        offset = self.foliage_offset

        profile:list[tuple[float, float]] = []
        profile.append([0.0, offset])

        for i in range(1, sample_count-1):
            profile.append([
                radius * abs(self.sample_point((i - 1) / (sample_count - 1))),
                height * ((i - 1) / (sample_count - 1)) + offset
            ])

        profile.append([0.0, offset + height])

    def generate_trunk_profile(self) -> list[tuple[float, float]]:
        radius = self.trunk_radius
        height = self.trunk_height
        offset = self.trunk_offset
        lo_tap = self.trunk_lower_taper
        up_tap = self.trunk_upper_taper

        profile:list[tuple[float, float]] = [
            [0.0, offset],
            [radius * (1.0 - lo_tap), offset],
            [radius * (1.0 - up_tap), offset + height],
            [0.0, offset + height]
        ]

        return profile

    def get_largest_dimension(self):
        radius = max(self.foliage_radius, self.trunk_radius) * 2
        height = max(self.trunk_height + self.trunk_offset, self.foliage_offset + self.foliage_height)
        return max(radius, height)

class TreeCollectionAsset:
    def __init__(self, target:ProjectAsset) -> None:
        self.target = target
        self.trees:list[TreeAsset] = []
        self.selected_tree:TreeAsset = None

        self.presets_path = Path("AppAssets/tree_presets.csv")
        self.presets:list[TreeAsset] = []

        if self.presets_path.is_file() is True:
            with self.presets_path.open('r') as file:
                lines = file.readlines()
                header = lines.pop(0)
                for line in lines:
                    self.presets.append(TreeAsset(header, line))

    def drawing_init(self, canvas:Canvas):
        self.canvas = canvas

    def save_data_to_files(self):
        with self.target.treesCSV_path.open() as file:
            output = TreeAsset().header() + '\n'

            for tree in self.trees:
                output += tree.to_csv() + '\n'

            output = output.removesuffix('\n')
            file.write(output)
            

    # -------------------------------------------------------------- #
    # --- Presets -------------------------------------------------- #
    def add_preset(self, tree:TreeAsset=None):
        '''Adds currently selected tree if None provided'''
        if tree is None:
            tree = self.selected_tree

        self.presets.append(self.selected_tree.to_csv(include_name=True))
        self.save_presets()

    def remove_preset(self, index:int):
        self.presets.pop(index)
        self.save_presets()

    def save_presets(self):
        with self.presets_path.open('w'):
            with self.presets_path.open('w') as file:
                file.write(TreeAsset().header(include_name=True))
                file.write('\n')

                for tree in self.presets:
                    file.write(tree.to_csv)

    def _save_settings(self):
        pass

    def add_tree(self):
        tree = TreeAsset()
        self.trees.append(tree)

    # def 

    def draw_to_canvas(self):
        for tree in self.trees:
            # Draw a dot circle
            # Draw a 
            pass

    def draw_to_inspector(self):
        '''
        Mockup:
        
        canvasSelect:Button | trees:Dropdown | new_tree:Button
        sub_canvas renderer
        '''

        pass

# tree = TreeAsset()
# tree.demo()
# print(tree.header())
# print(tree.export_to_csv())

project = ProjectAsset(savename="AshevilleClub")
treeCol = TreeCollectionAsset(target=project)
treeCol.save_presets()

header = "trunk_radius,trunk_height,trunk_offset,trunk_lower_taper,trunk_upper_taper,foliage_radius,foliage_height,foliage_offset,foliage_lower_curv,foliage_midpoint,foliage_upper_curv"
data = "999.999,2.0,0.0,0.0,0.0,2.5,5.0,0.0,2.0,0.5,123.123"
tree = TreeAsset(header, data)
print(tree.to_csv())

