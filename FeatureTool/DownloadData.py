from pickle import NONE
import cv2
import numpy as np
import pandas as pd
import APIKeys as keys
from pathlib import Path
from FeatureCreation import PolygonDrawer
from GoogleMapsAPI import SatelliteInterface as si
from TerrainEditor import loaded_asset

google_satelite = "google_satelite"
google_elevation = "google_elevation"

def __via_google_satelite(NW:float, SE:float) -> Path:
    pass

def download(fileName:loaded_asset, service:str, NW:float, SE:float):
    if service == google_satelite:
        return __via_google_satelite(NW=NW, SE=SE)

    if service == google_elevation:
        return NONE