'''
Ideas:
    Concurrently download: https://youtu.be/GpqAQxH1Afc
'''

import json
import math
import cv2
import numpy as np
import requests
from copy import copy
from time import sleep
from pathlib import Path
from asset_project import LocationPaths
# from asset_area import AreaAsset
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

from APIs import keys, usage_tracker
from APIs.google_maps_api import SatelliteInterface as gmap_si

from geographiclib.geodesic import Geodesic
from geographiclib.geodesicline import GeodesicLine
from operations.generate_imagery import generate_imagery

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
def __via_google_satelite(target:LocationPaths, p0:tuple[float, float], p1:tuple[float, float]) -> Path:
    grabber = gmap_si(keys.google_maps())
    result = grabber.get_maps_image(p0, p1, zoom=19)
    image_ct = grabber.get_image_count(p0, p1, zoom=19)
    
    resultCv = pil_to_cv(result)
    cv2.imwrite(filename=str(target.sateliteImg_path), img=resultCv)

    usage_tracker.add_api_count(services.google_satelite, image_ct)
    print("{} Images downloaded".format(image_ct))

    return target.sateliteImg_path

def download_imagery(target:LocationPaths, service:str) -> Path:
    '''Pull data from specified service'''
    if service == services.google_satelite:
        return __via_google_satelite(target, *target.coordinates())

# -------------------------------------------------------------- #
# --- Elevation functions -------------------------------------- #
def download_elevation_for_location(target:LocationPaths, service:services, sample_dist=5) -> Path:
    '''
    Sample the entire location with points sample_dist meters apart.
    '''
    coords = target.coordinates()
    NW,SE = coords[0], coords[1]

    # lats =  [NW[0], SE[1], SE[1], NW[0]]
    # longs = [NW[0], NW[0], SE[1], SE[1]]
    points = get_points(*coords, dist=sample_dist, boundry_pts=None)
    return __via_google_elevation(target, points, target.elevationCSV_path)


def download_elevation_for_area(target:LocationPaths, area:"AreaAsset", service: services) -> Path: # type: ignore
    pass

def download_elevation_for_points(target:LocationPaths) -> Path:
    pass

def download_elevation(target:LocationPaths, points:tuple[list[float], list[float]], service:services, sample_dist=5, output_path:Path=None, sample_inside_polygon=True) -> Path:
    '''
    Remove in the future as there's starting to be too many parameters.
    Instead use download_elevation_for_location(), download_elevation_for_area(), download_elevation_for_points()
    as they are more specialized.
    '''
    if sample_inside_polygon is True:
        coords = target.coordinates()
        points = get_points(*coords, dist=5, boundry_pts=points)

    if service is services.google_elevation:
        return __via_google_elevation(target, points, output_path)

def __via_google_elevation(target:LocationPaths, points, output_path:Path) -> Path:
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
    print(len(points))

    # if (input("{} requests for {} points will be used. Type 'y' to confirm: ".format(len(urls), len(points))) != 'y'):
    #     print("request denied")
    #     return

    output = "latitude,longitude,elevation,resolution,offset-x,offset-y\n"
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
    pt_id = 0
    for url in urls:
        response = requests.request("GET", url)
        print('[{}] Retrieved results: {}'.format(count, response), end=" ")
        data = json.loads(response.text)["results"]
        print('{} points recieved'.format(len(data)))

        for item in data:
            output += "{},{},{},{},{},{}\n".format(
                item["location"]['lat'],
                item["location"]['lng'],
                item["elevation"],
                item["resolution"],
                points[pt_id][-2], # Horizontal Offset
                points[pt_id][-1], # Vertical Offset
                )
            pt_id += 1
        
        print('Sleeping...')
        sleep(0.5)
        count += 1

    print('Completed elevation requests')
    output = output.removesuffix('\n')
    with output_path.open(mode='w') as outfile:
        outfile.write(output)

    print("Generating imagery (may take some time)...")
    generate_imagery (target)
    print("Completed imagery generation")

    usage_tracker.add_api_count(services.google_elevation, len(urls))
    return output_path

def get_points(p0, p1, dist=5, boundry_pts=None):
    geod:Geodesic = Geodesic.WGS84
    lat_line:GeodesicLine = geod.InverseLine( *p0, p0[0], p1[1] )
    lat_line_pts = []

    count = int(math.ceil(lat_line.s13 / dist))
    for i in range(count + 1):
        hor_offset = min(dist * i, lat_line.s13)
        g = lat_line.Position(hor_offset, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
        lat_line_pts.append((g['lat2'], g['lon2'], hor_offset))

    polygon = None
    if boundry_pts is not None:
        np_lat_long = np.column_stack(boundry_pts)
        polygon = Polygon(np_lat_long)

    output_pts = []
    for lat_pts in lat_line_pts:
        long_line = geod.InverseLine (lat_pts[0], lat_pts[1], p1[0], lat_pts[1])
        count = int(math.ceil(long_line.s13 / dist))
        
        for i in range(count + 1):
            ver_offset = min(dist * i, long_line.s13)
            g = long_line.Position(ver_offset, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
            pt = (g['lat2'], g['lon2'], lat_pts[2], ver_offset)
            if (polygon is None):
                output_pts.append(pt)

            else:
                pt_test = Point(g['lat2'], g['lon2']) 
                if pt_test.within(polygon):
                    output_pts.append(pt)

    return output_pts