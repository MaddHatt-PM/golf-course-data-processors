from math import pi
from pathlib import Path
import sys
from time import sleep
from PIL import Image, ImageOps
from matplotlib import pyplot as plt
import numpy as np
from scipy.interpolate import griddata
import matplotlib
import api_keys as keys

coordpath = Path('SavedAreas\AshevilleClub\Coordinates.csv')
with coordpath.open('r') as file:
    lines = file.read().splitlines()
    headers = lines.pop(0).split(',')
    NW = eval(lines[0])
    SE = eval(lines[1])

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

grid_x,grid_y = np.mgrid[
    min(range_x):max(range_x):1000j,
    min(range_y): max(range_y):1000j
]

height_data = griddata(xy, z, (grid_x, grid_y), method='linear')

height = NW[0] - SE[0]
width = SE[1] - NW[1]
aspect = width / height
multiplier = 8000
plt.figure(figsize= (width * multiplier, height * multiplier))
print((width * multiplier, height * multiplier))

plt.plot(x, y, 'k.', ms=1)

LEVELS = 50
plt.tricontour(x, y, z, levels=LEVELS, cmap='inferno')

contour_path = Path('contour_buffer.png')
plt.axis('off')
plt.savefig(contour_path, bbox_inches='tight', pad_inches=0, transparent=True)
plt.clf()

plt.imshow(
    height_data,
    extent=(SE[1], NW[1], SE[0], NW[0]),
    origin='lower',
    cmap='cubehelix')

# plt.show()
height_path = Path('example.png')
plt.axis('off')
plt.savefig(height_path, bbox_inches='tight', pad_inches=0, transparent=True)

con_fig = Image.open(contour_path)
# con_fig = con_fig.rotate(180)
# con_fig.
con_fig.save(contour_path)

fig_img = Image.open(height_path)
fig_img = fig_img.rotate(90, expand = True)
fig_img = fig_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
fig_img = fig_img.resize((fig_img.size[1], fig_img.size[0]))
print(fig_img.size)

ref_img = Image.open(Path('SavedAreas\AshevilleClub\Satelite.png'))
print(ref_img.size)

fig_img.paste(con_fig, (0,0), con_fig)

fig_img = fig_img.resize(ref_img.size)
fig_img.save(height_path)