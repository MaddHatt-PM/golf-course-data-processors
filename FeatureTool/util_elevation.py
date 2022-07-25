from math import pi
from pathlib import Path
import sys
from matplotlib import pyplot as plt
import numpy as np
from scipy.interpolate import griddata
import matplotlib
import google_maps_api
import api_keys as keys

coordpath = Path('SavedAreas\AshevilleClub\Coordinates.csv')
with coordpath.open('r') as file:
    lines = file.read().splitlines()
    headers = lines.pop(0).split(',')
    NW = eval(lines[0])
    SE = eval(lines[1])

print(NW, SE)

datapath =  Path('SavedAreas\AshevilleClub\Elevation.csv')
with datapath.open('r') as file:
    lines = file.read().splitlines()
    headers = lines.pop(0).split(',')

latID = headers.index('latitude')
lonID = headers.index('longitude')
eleID = headers.index('elevation')
x,y = [],[]
xy, z = [], []
for ln in lines:
    raw = ln.split(',')
    pt = [eval(pt) for pt in raw]
    x.append(pt[lonID])
    y.append(pt[latID])
    xy.append((pt[lonID], pt[latID]))
    z.append(pt[eleID])

x = np.array(x)
y = np.array(y)
xy = np.array(xy)
z = np.array(z)

range_x = [NW[1], SE[1]]
range_y = [NW[0], SE[0]]

xi = np.linspace(max(range_x), min(range_x))
yi = np.linspace(min(range_y), max(range_y))
grid_x,grid_y = np.mgrid[
    max(range_x):min(range_x):500j,
    min(range_y): max(range_y):500j
]

height_data = griddata(xy, z, (grid_x, grid_y), method='nearest')
# ullat, ullon = [i * (pi * 2 / 180) for i in NW]
# lrlat, lrlon = [i * (pi * 2 / 180) for i in SE]

# # convert all these coordinates to pixels
# si = google_maps_api.SatelliteInterface(keys.google_maps())
# ulx, uly = si.latlon2pixels(lat=ullat, lon=ullon)
# lrx, lry = si.latlon2pixels(lat=lrlat, lon=lrlon)

# # calculate total pixel dimensions of final image
# dx, dy = lrx - ulx, uly - lry

# print(dx,dy)

height = pNW[0] - pSE[0]
width = pSE[1] - pNW[1]
aspect = width / height
multiplier = 8000
plt.figure(figsize= (width * multiplier, height * multiplier))

plt.plot(x, y, 'k.', ms=1)
LEVELS = 18
plt.tricontour(x, y, z, cmap=matplotlib.cm.plasma, levels=LEVELS)
plt.imshow(
    height_data,
    extent=(SE[1], NW[1], SE[0], NW[0]),
    origin='lower',
    cmap=matplotlib.cm.gray)

# plt.show()
plt.axis('off')
plt.savefig('example.png', bbox_inches='tight', pad_inches=0)
