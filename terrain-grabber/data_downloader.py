'''
Ideas:
    Concurrently download: https://youtu.be/GpqAQxH1Afc
'''

from copy import copy
import json
import math
import sys
from time import sleep
import cv2
import numpy as np
import requests
import api_usage_tracker
import api_keys as keys
from typing import Tuple
from pathlib import Path
# from asset_area import AreaAsset
from asset_project import ProjectAsset

from google_maps_api import SatelliteInterface as gmap_si
from geographiclib.geodesic import Geodesic


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
def __via_google_satelite(target:ProjectAsset, p0:Tuple[float, float], p1:Tuple[float, float]) -> Path:
    grabber = gmap_si(keys.google_maps())
    result = grabber.get_maps_image(p0, p1, zoom=19)
    image_ct = grabber.get_image_count(p0, p1, zoom=19)
    
    resultCv = pil_to_cv(result)
    cv2.imwrite(filename=str(target.sateliteImg_path), img=resultCv)

    api_usage_tracker.add_api_count(services.google_satelite, image_ct)
    print("{} Images downloaded".format(image_ct))

    return target.sateliteImg_path

def download_imagery(target:ProjectAsset, service:str) -> Path:
    '''Pull data from specified service'''

    # Unpack coordinates for readability
    coords = target.coordinates()
    p0 = coords[0]
    p1 = coords[1]

    if service == services.google_satelite:
        return __via_google_satelite(target, p0, p1)

# -------------------------------------------------------------- #
# --- Elevation functions -------------------------------------- #
def download_elevation(target:ProjectAsset, points:tuple[list[float], list[float]], service:services, output_path:Path=None, sample_inside_polygon=True) -> Path:
    if sample_inside_polygon is True:
        coords = target.coordinates()
        points = get_points(*coords, dist=5, boundry_pts=points)

    if service is services.google_elevation:
        return __via_google_elevation(target, points, output_path)

def __via_google_elevation(target:ProjectAsset, points, output_path:Path) -> Path:
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

    prefix = "https://maps.googleapis.com/maps/api/elevation/json?locations="
    location = "{}%2C{}"
    sep = "%7C"
    suffix = "&key={}".format(keys.google_maps())
    request_location_limit = 250
    url = prefix
    urls = []
    print(points)

    # Compile the points in a batch call
    index = 0
    for pt in points:
        if index > request_location_limit:
            # Store url
            url = url.removesuffix(sep)
            url += suffix
            urls.append(copy(url))

            # Reset url for next iteration
            url = prefix
            index -= request_location_limit

        url += location.format(pt[0], pt[1])
        url += sep
        index += 1
    url = url.removesuffix(sep) + suffix
    urls.append(url)

    if (input("{} requests for {} points will be used. Type 'y' to confirm: ".format(len(urls), len(points))) != 'y'):
        print("request denied")
        return

    output = "latitude,longitude,elevation,resolution\n"
    if target is not None:
        output_path = target.elevationCSV_path 

    if output_path.exists():
        with output_path.open('r') as file:
            # Assume a perfect situation where only the program has touched the data
            file_input = file.read()
            output += file_input.removeprefix(output)
            output += '\n'
            print("Joining files")

    count = 0
    for url in urls:
        response = requests.request("GET", url)
        print('[{}] Retrieved results: {}'.format(count, response))
        data = json.loads(response.text)["results"]

        for item in data:
            output += "{},{},{},{}\n".format(
                item["location"]['lat'],
                item["location"]['lng'],
                item["elevation"],
                item["resolution"])
        
        print('Sleeping...')
        sleep(0.75)
        count += 1

    print('Completed elevation requests')
    output = output.removesuffix('\n')
    with output_path.open(mode='w') as outfile:
        outfile.write(output)

    api_usage_tracker.add_api_count(services.google_elevation, len(urls))
    return output_path

def get_points(p0, p1, dist=5, boundry_pts=None):
    geod:Geodesic = Geodesic.WGS84
    lat_line = geod.InverseLine( *p0, p0[0], p1[1] )
    lat_line_pts = []
    count = int(math.ceil(lat_line.s13 / dist))
    for i in range(count + 1):
        s = min(dist * i, lat_line.s13)
        g = lat_line.Position(s, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
        lat_line_pts.append((g['lat2'], g['lon2']))


    polygon = None
    if boundry_pts is not None:
        np_lat_long = np.column_stack(boundry_pts)
        polygon = Polygon(np_lat_long)

    output_pts = []
    for p3 in lat_line_pts:
        long_line = geod.InverseLine (*p3, p1[0], p3[1])
        count = int(math.ceil(long_line.s13 / dist))
        
        for i in range(count + 1):
            s = min(dist * i, long_line.s13)
            g = long_line.Position(s, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
            pt = (g['lat2'], g['lon2'])
            if (polygon is None):
                output_pts.append(pt)

            else:
                tester = Point(g['lat2'], g['lon2']) 
                if tester.within(polygon):
                    output_pts.append(pt)

    return output_pts