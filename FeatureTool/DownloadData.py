import cv2
import numpy as np
import requests
import APIKeys as keys
from typing import Tuple
from pathlib import Path
from AreaAsset import area_asset
from LoadedAsset import loaded_asset

from GoogleMapsAPI import SatelliteInterface as gmap_si

class services:
    # ... = "specific_service", "shared_service" 
    google_satelite = "google_satelite"
    google_elevation = "google_elevation"

    



# -------------------------------------------------------------- #
# --- Utilitity functions -------------------------------------- #
def pil_to_cv(pil_image):
    '''Convert RGB to BGR'''
    open_cv_image = np.array(pil_image)
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    return open_cv_image

# -------------------------------------------------------------- #
# --- Imagery functions ---------------------------------------- #
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

    if service == services.google_satelite:
        return __via_google_satelite(target, p0, p1)

# -------------------------------------------------------------- #
# --- Elevation functions -------------------------------------- #
def __via_google_elevation(target:loaded_asset, area:area_asset) -> Path:
    '''
    - Google Documentation: https://developers.google.com/maps/documentation/elevation/start#maps_http_elevation_locations-py
    - Submit a single request using https://stackoverflow.com/questions/29418423/how-to-use-an-array-of-coordinates-with-google-elevation-api
    '''


    pt = (35.61747385057783, -82.56616442192929)
    prefix = "https://maps.googleapis.com/maps/api/elevation/json?locations={}%2C{}"
    location = "{}%2C{}"
    sep = "%7C"
    suffix = "&key={}".format(keys.google_maps)
    url = prefix.format(pt[0], pt[1], keys.google_maps)

    request_location_limit = 512
    

    payload = {}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    print(response.text)

def download_elevation(target:loaded_asset, area:area_asset, service:services) -> Path:
    if service is services.google_elevation:
        return __via_google_elevation(target, area)