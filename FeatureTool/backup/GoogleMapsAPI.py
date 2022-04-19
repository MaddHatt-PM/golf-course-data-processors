#!/usr/bin/env python
"""
Stitch together Google Maps images from lat, long coordinates
Based on work by heltonbiker and BenElgar
Changes: 
* updated for Python 3
* added Google Maps API key (compliance with T&C, although can set to None)
* handle http request exceptions

With contributions from Eric Toombs.
Changes:
* Dramatically simplified the maths.
* Set a more reasonable default logo cutoff.
* Added global constants for logo cutoff and max image size.
* Translated a couple presumably Portuguese variable names to English.

Adapted by Adrian Bruno
Changes:
* Object Orientation

"""

import requests
from io import BytesIO
from math import log, exp, tan, atan, ceil, pi
from PIL import Image
import sys

class SatelliteInterface:
    global tau,DEGREE,ZOOM_OFFSET,MAXSIZE,LOGO_CUTOFF
    # circumference/radius
    tau = 2*pi
    # One degree in radians, i.e. in the units the machine uses to store angle,
    # which is always radians. For converting to and from degrees. See code for
    # usage demonstration.
    DEGREE = pi/180
    
    ZOOM_OFFSET = 8
    
    # Max width or height of a single image grabbed from Google.
    MAXSIZE = 640
    # For cutting off the logos at the bottom of each of the grabbed images.  The
    # logo height in pixels is assumed to be less than this amount.
    LOGO_CUTOFF = 32
    
    def __init__(self,key = None):
        self.key = key
    
    def latlon2pixels(self,lat, lon, zoom):
        mx = lon
        my = log(tan((lat + tau/4)/2))
        res = 2**(zoom + ZOOM_OFFSET) / tau
        px = mx*res
        py = my*res
        return px, py
    
    def pixels2latlon(self, px, py, zoom):
        res = 2**(zoom + ZOOM_OFFSET) / tau
        mx = px/res
        my = py/res
        lon = mx
        lat = 2*atan(exp(my)) - tau/4
        return lat, lon
    
    
    def get_maps_image(self,NW_lat_long, SE_lat_long, zoom=18,):
        
        NW_lat_long = [i*DEGREE for i in NW_lat_long]
        SE_lat_long = [i*DEGREE for i in SE_lat_long]
    
        ullat, ullon = NW_lat_long
        lrlat, lrlon = SE_lat_long
    
        # convert all these coordinates to pixels
        ulx, uly = self.latlon2pixels(ullat, ullon, zoom)
        lrx, lry = self.latlon2pixels(lrlat, lrlon, zoom)
    
        # calculate total pixel dimensions of final image
        dx, dy = lrx - ulx, uly - lry
    
        # calculate rows and columns
        cols, rows = ceil(dx/MAXSIZE), ceil(dy/MAXSIZE)
    
        # calculate pixel dimensions of each small image
        width = ceil(dx/cols)
        height = ceil(dy/rows)
        heightplus = height + LOGO_CUTOFF
    
        # assemble the image from stitched
        final = Image.new('RGB', (int(dx), int(dy)))
        for x in range(cols):
            for y in range(rows):
                dxn = width * (0.5 + x)
                dyn = height * (0.5 + y)
                latn, lonn = self.pixels2latlon(
                        ulx + dxn, uly - dyn - LOGO_CUTOFF/2, zoom)
                position = ','.join((str(latn/DEGREE), str(lonn/DEGREE)))
                print(x, y, position)
                urlparams = {
                        'center': position,
                        'zoom': str(zoom),
                        'size': '%dx%d' % (width, heightplus),
                        'maptype': 'satellite',
                        'sensor': 'false',
                        'scale': 1
                    }
                if self.key is not None:
                    urlparams['key'] = self.key
    
                url = 'http://maps.google.com/maps/api/staticmap'
                try:                  
                    response = requests.get(url, params=urlparams)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    print(e)
                    sys.exit(1)
    
                im = Image.open(BytesIO(response.content))                  
                final.paste(im, (int(x*width), int(y*height)))
    
        return final
    
        def getDegree(self):
            return self.DEGREE

############################################

if __name__ == '__main__':
    DEGREE = pi/180
    # Hole #1:
    NW_lat_long =  (35.579921, -82.500321)
    SE_lat_long = (35.578649, -82.497227)

    zoom = 18   # be careful not to get too many images!
    
    newSi = SatelliteInterface("AIzaSyAtIgGHyz_pNogrCaGmDfEU95zyM00i4Q4")
    result = newSi.get_maps_image(NW_lat_long, SE_lat_long, zoom=18)
    result.show()