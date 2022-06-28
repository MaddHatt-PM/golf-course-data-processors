'''
Ideas:
    Concurrently download: https://youtu.be/GpqAQxH1Afc
'''

import json
import cv2
import numpy as np
import requests
import api_usage_tracker
import api_keys as keys
from typing import Tuple
from pathlib import Path
from asset_area import AreaAsset
from loaded_asset import LoadedAsset

from google_maps_api import SatelliteInterface as gmap_si

class service:
    def __init__(self, name:str, sku_cost:float, key:str) -> None:
        self.name = name
        self.sku_cost = sku_cost
        self.key = key

class services:
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
def __via_google_satelite(target:LoadedAsset, p0:Tuple[float, float], p1:Tuple[float, float]) -> Path:
    grabber = gmap_si(keys.google_maps)
    result = grabber.get_maps_image(p0, p1, zoom=19)
    image_ct = grabber.get_image_count(p0, p1, zoom=19)
    
    resultCv = pil_to_cv(result)
    cv2.imwrite(filename=str(target.sateliteImg_path()), img=resultCv)

    api_usage_tracker.add_api_count(services.google_satelite, image_ct)
    print("{} Images downloaded".format(image_ct))

    return target.sateliteImg_path()

def download_imagery(target:LoadedAsset, service:str) -> Path:
    '''Pull data from specified service'''

    # Unpack coordinates for readability
    coords = target.coordinates()
    p0 = coords[0]
    p1 = coords[1]

    if service == services.google_satelite:
        return __via_google_satelite(target, p0, p1)

# -------------------------------------------------------------- #
# --- Elevation functions -------------------------------------- #
def __via_google_elevation(target:LoadedAsset, area:AreaAsset) -> Path:
    '''
    - Google Documentation: https://developers.google.com/maps/documentation/elevation/start#maps_http_elevation_locations-py
    - Submit a single request using https://stackoverflow.com/questions/29418423/how-to-use-an-array-of-coordinates-with-google-elevation-api

    Google Elevation Request example:
    {
        'results': [
            {'elevation': 358.2732746783741, 'location': {'lat': 32.1111, 'lng': -82.1111}, 'resolution': 9.543951988220215},
            {'elevation': 398.2074279785156, 'location': {'lat': 36.2222, 'lng': -85.2222}, 'resolution': 9.543951988220215},
            ...
            ],
        'status': 'OK'
    }
    '''

    # old working version
    # pt = (35.61747385057783, -82.56616442192929)
    # url_single = "https://maps.googleapis.com/maps/api/elevation/json?locations={}%2C{}&key={}"
    # url_single = url_single.format(pt[0], pt[1], keys.google_maps)
    # response = requests.request("GET", url_single)

    # new untested version
    # points = area.get_points()
    points = [(35.61246415128191, -82.57430064075014), (35.61230888486478, -82.5697221504971)]

    prefix = "https://maps.googleapis.com/maps/api/elevation/json?locations="
    location = "{}%2C{}"
    sep = "%7C"
    suffix = "&key={}".format(keys.google_maps)
    request_location_limit = 500

    url = prefix
    urls = []

    # Compile the points in a batch call
    for id, pt in enumerate(points):
        if id == request_location_limit:
            # Store url
            url = url.removesuffix(sep)
            url += suffix
            urls.append(url)

            # Reset url for next iteration
            url = prefix

        url += location.format(pt[0], pt[1])
        url += sep

    url = url.removesuffix(sep) + suffix
    urls.append(url)

    output = "latitude,longitude,elevation,resolution\n"
    for url in urls:
        response = requests.request("GET", url)
        data = json.loads(response.text)["results"]

        for item in data:
            output += "{},{},{},{}\n".format(
                item["location"]['lat'],
                item["location"]['lng'],
                item["elevation"],
                item["resolution"])

    output = output.removesuffix('\n')
    with target.elevationCSV_path.open(mode='w') as outfile:
        outfile.write(output)

    api_usage_tracker.add_api_count(services.google_elevation, len(points))
    return target.elevationCSV_path

def download_elevation(target:LoadedAsset, area:AreaAsset, service:services) -> Path:
    if service is services.google_elevation:
        return __via_google_elevation(target, area)

'''

'''