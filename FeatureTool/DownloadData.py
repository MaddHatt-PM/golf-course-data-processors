import cv2
import numpy as np
import requests
import APIKeys as keys
from typing import Tuple
from pathlib import Path
from AreaAsset import area_asset
from LoadedAsset import loaded_asset

from GoogleMapsAPI import SatelliteInterface as gmap_si



# -------------------------------------------------------------- #
# --- Utilitity functions -------------------------------------- #
def pil_to_cv(pil_image):
    '''Convert RGB to BGR'''
    open_cv_image = np.array(pil_image)
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    return open_cv_image


# -------------------------------------------------------------- #
# --- Imagery functions ---------------------------------------- #
class img_services:
    google_satelite = "google_satelite"

def __via_google_satelite(target:loaded_asset, p0:Tuple[float, float], p1:Tuple[float, float]) -> Path:
    grabber = gmap_si(keys.google_maps)
    result = grabber.get_maps_image(p0, p1, zoom=19)
    
    resultCv = pil_to_cv(result)
    cv2.imwrite(filename=str(target.sateliteImg_path()), img=resultCv)

    print(grabber.get_image_count(p0, p1, zoom=19))
    print("Image downloaded")

    return target.sateliteImg_path()

def download_imagery(target:loaded_asset, service:str) -> Path:
    '''Pull data from specified service'''

    # Unpack coordinates for readability
    coords = target.coordinates()
    p0 = coords[0]
    p1 = coords[1]

    if service == img_services.google_satelite:
        return __via_google_satelite(target, p0, p1)

# -------------------------------------------------------------- #
# --- Elevation functions -------------------------------------- #
class ele_services:
    google_elevation = "google_elevation"

def __via_google_elevation(target:loaded_asset, area:area_asset) -> Path:
    '''Google Documentation: https://developers.google.com/maps/documentation/elevation/start#maps_http_elevation_locations-py'''

    pt = (35.61747385057783, -82.56616442192929)
    url = "https://maps.googleapis.com/maps/api/elevation/json?locations={}%2C{}&key={}"
    url = url.format(pt[0], pt[1], keys.google_maps)

    payload = {}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    print(response.text)

def download_elevation(target:loaded_asset, area:area_asset, service:ele_services) -> Path:
    if service is ele_services.google_elevation:
        return __via_google_elevation(target, area)