import cv2
import numpy as np
import APIKeys as keys
from typing import Tuple
from pathlib import Path
from LoadedAsset import loaded_asset

from GoogleMapsAPI import SatelliteInterface as gmap_si

class services:
    google_satelite = "google_satelite"
    google_elevation = "google_elevation"

def pil_to_cv(pil_image):
    '''Convert RGB to BGR'''
    open_cv_image = np.array(pil_image)
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    return open_cv_image

def __via_google_satelite(target:loaded_asset, p0:Tuple[float, float], p1:Tuple[float, float]) -> Path:
    grabber = gmap_si(keys.google_maps)
    result = grabber.get_maps_image(p0, p1, zoom=19)
    
    resultCv = pil_to_cv(result)
    cv2.imwrite(filename=str(target.sateliteImg_path()), img=resultCv)

    print(grabber.get_image_count(p0, p1, zoom=19))
    print("Image downloaded")

    return target.sateliteImg_path()

def download(target:loaded_asset, service:str) -> Path:
    '''Pull data from specified service'''

    # Unpack coordinates for readability
    coords = target.coordinates()
    p0 = coords[0]
    p1 = coords[1]

    if service == services.google_satelite:
        return __via_google_satelite(target, p0, p1)

    if service == services.google_elevation:
        return None