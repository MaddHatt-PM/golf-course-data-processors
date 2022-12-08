import json
import sys
from tkinter import messagebox
from pathlib import Path

class LayerManager:
    def __init__(self, filepath:Path):
        self.layers:dict[str, int] = {}
        self.filepath = filepath

        self.load()
        self.layers["Default"] = -10

    def generate_default_layers(self):
        self.layers:dict[str, int] = {
            "Trees" : 100,
            "Sandtrap": 80,
            "Green" : 60,
            "Fairway": 40,
            "Rough" : 20,
            "Default" : -10
            }

    def load(self):
        if self.filepath.exists() is False:
            self.generate_default_layers()
            self.save()
            return

        try:
            with self.filepath.open('r', encoding="utf8") as file:
                data = json.load(file)
            self.layers = data
            
        except:
            isCrashing = messagebox.askyesno(
                title="ERROR",
                message="Unable to open layer file. Proceed with location loading?",
            )

            if isCrashing:
                sys.exit(1)


    def save(self):
        with self.filepath.open('w', encoding="utf8") as file:
            json.dump(self.layers, fp=file)

    def get_layer_names(self):
        return self.layers.keys()

if __name__ == "__main__":
    testpath = Path("test_layers.cvs")
    layer_manager = LayerManager(filepath=testpath)
    layer_manager.save()