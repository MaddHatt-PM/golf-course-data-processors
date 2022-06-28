from tkinter import Canvas

from loaded_asset import LoadedAsset

class TreeAsset:
    pass

class TreeCollectionAsset:
    def __init__(self, target:LoadedAsset) -> None:
        self.target = target
        self.trees:list[TreeAsset] = []
        self.selected_tree:TreeAsset = None

    def drawing_init(self, canvas:Canvas):
        pass

    def _save_settings(self):
        pass

    def save_data_to_files(self):
        pass

    def draw_to_canvas(self):
        pass

    def draw_to_inspector(self):
        '''
        Mockup:
        
        canvasSelect:Button | trees:Dropdown | new_tree:Button
        
        '''


        pass