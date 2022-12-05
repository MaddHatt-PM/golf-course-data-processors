"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022

Issues:
    Tangent Space Generator:
     - Swap out the heightmap for coordinates to regenerate a height map at an extreme resolution (maybe 1pt->1px) 
"""

import os
from pathlib import Path
from typing import Callable

from tkinter.messagebox import showwarning
from PIL import Image
from matplotlib import pyplot as plt
import cv2 as cv
import numpy as np
from scipy import ndimage
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter
from loading import LoadingWindowHandler
from asset_area import LocationPaths

def resize_to_satelite(target: LocationPaths, img_path:Path):
    """Take an image and resize it to match the satelite image"""
    img = Image.open(img_path)
    img = img.resize(Image.open(target.satelite_img_path).size)
    img.save(img_path)

def generate_imagery(target: LocationPaths, contour_levels:int=50, contour_thickness:float=1.5):
    """
    Generate images from elevation data.
    1. Sample point distribution map
    2. Nearest/Linear/Combined elevation gradient map
    3. Contour map
    4. Tangent normal map
    """

    generate_sample_distribution_map(target)
    generate_gradient_maps(target)
    generate_contour_map(target, contour_levels, contour_thickness)
    generate_tangent_normal(target)


def __prepare_to_bake(target:LocationPaths):
    """
    Private helper function to load in available data
    """
    with target.coordinates_path.open('r') as file:
        lines = file.read().splitlines()
        headers = lines.pop(0).split(',')
        NW = eval(lines[0])
        SE = eval(lines[1])

    with target.elevation_csv_path.open('r') as file:
        lines = file.read().splitlines()
        headers = lines.pop(0).split(',')

    if 'elevation' not in headers:
        showwarning(title='error', message='No height data available')

    latID = headers.index('latitude')
    lonID = headers.index('longitude')
    eleID = headers.index('elevation')
    xOffsetsID = headers.index('offset-x')
    yOffsetsID = headers.index('offset-y')
    xLats,yLongs, zEle = [], [], []
    xOffsets, yOffsets = [], []
    xyLatLongs = []

    for ln in lines:
        raw = ln.split(',')
        pt = [eval(pt) for pt in raw]
        xLats.append(pt[lonID])
        yLongs.append(pt[latID])
        xyLatLongs.append((pt[lonID], pt[latID]))
        zEle.append(pt[eleID])
        xOffsets.append(pt[xOffsetsID])
        yOffsets.append(pt[yOffsetsID])

    xLats = np.array(xLats)
    yLongs = np.array(yLongs)
    xyLatLongs = np.array(xyLatLongs)
    zEle = np.array(zEle)

    range_x = [NW[1], SE[1]]
    range_y = [NW[0], SE[0]]

    grid_x,grid_y = np.mgrid[
        min(range_x) : max(range_x) : 5000j,
        min(range_y) : max(range_y) : 5000j
    ]

    multiplier = 10000
    width = (SE[1] - NW[1]) * multiplier
    height = (NW[0] - SE[0]) * multiplier
    plt.figure(figsize= (width, height))
    
    return NW,SE,xLats,yLongs,zEle,xOffsets,yOffsets,xyLatLongs,grid_x,grid_y

def generate_gradient_maps(target:LocationPaths):
    NW, SE, xLats, yLongs, zEle, xOffsets, yOffsets, xyLatLongs, grid_x, grid_y = __prepare_to_bake(target)
    """
    Generate gradient maps with nearest (blocky) and linear (smoothed) interpolation
    """

    loadingHandler = LoadingWindowHandler()
    loadingHandler.show("Generating Height Maps... May take some time...")

    grad_configs = [
        ('nearest', target.elevation_img_nearest_path),
        ('linear', target.elevation_img_linear_path),
    ]

    def plot_gradmap(config:tuple[str, str]):
        interpolation, filepath = config
        height_data = griddata(xyLatLongs, zEle, (grid_x, grid_y), method=interpolation)

        plt.imshow(
            height_data,
            extent=(SE[1], NW[1], SE[0], NW[0]),
            origin='lower',
            cmap='gray')

        plt.axis('off')
        plt.savefig(filepath, bbox_inches='tight', pad_inches=0, transparent=True)

        fig_img = Image.open(filepath)
        fig_img = fig_img.rotate(90, expand=True)
        fig_img = fig_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        fig_img = fig_img.resize((fig_img.size[1], fig_img.size[0]))
        fig_img.save(filepath)

        resize_to_satelite(target, filepath)
        print("{} interpolated elevation gradient map generated".format(config[0].title()))
        
    for config in grad_configs:
        plot_gradmap(config)

    loadingHandler.kill()

def generate_contour_map(target:LocationPaths, contour_levels, contour_thickness):
    """
    Generate a contour map to highlight the relative slope of a surface
    """
    NW, SE, xLats, yLongs, zEle, xOffsets, yOffsets, xyLatLongs, grid_x, grid_y = __prepare_to_bake(target)

    loadingHandler = LoadingWindowHandler()
    loadingHandler.show("Generating Contour Map...")

    plt.clf()
    plt.rcParams["contour.linewidth"] = contour_thickness
    plt.tricontour(xLats, yLongs, zEle, levels=contour_levels, cmap='inferno')
    plt.axis('off')
    plt.savefig(target.contour_img_path, bbox_inches='tight', pad_inches=0, transparent=True)
    resize_to_satelite(target, target.contour_img_path)

    loadingHandler.kill()
    print("Tricontour map generated")

def generate_sample_distribution_map(target:LocationPaths):
    NW, SE, xLats, yLongs, zEle, xOffsets, yOffsets, xyLatLongs, grid_x, grid_y = __prepare_to_bake(target)
    """
    Generate an image of dots that correspond to each point used to sample elevation data.
    """
    
    loadingHandler = LoadingWindowHandler()
    loadingHandler.show("Generating Sample Distribution Map...")
    
    '''Plot, crop, and save out sample distribution'''
    width, height = Image.open(target.satelite_img_path).size
    pointmap_alpha:np.ndarray = np.zeros((height, width, 1), dtype=bool)
    minXOffset, maxXOffset = min(xOffsets), max(xOffsets)
    minYOffset, maxYOffset = min(yOffsets), max(yOffsets)
    for i in range(len(xOffsets)):
        x = round((xOffsets[i]-minXOffset)/(maxXOffset-minXOffset), ndigits=6) * width
        x = min(int(width - 1), max(0, int(x)))

        y = round((yOffsets[i]-minYOffset)/(maxYOffset-minYOffset), ndigits=6) * height
        y = min(int(height - 1), max(0, int(y)))
        
        pointmap_alpha[y][x] = True

    dil_iters = 2
    dil_ref = np.array([
        [False, True, False],
        [True, True, True],
        [False, True, False],
    ], dtype=bool)
    
    pointmap_alpha = ndimage.binary_dilation(pointmap_alpha, iterations=dil_iters).astype(np.uint8)
    pointmap_alpha *= 255
    dist_image = np.zeros((height, width, 3), np.uint8)
    dist_image[::] = (255, 0, 0)
    dist_image = np.dstack((dist_image, pointmap_alpha))

    dist_image = Image.fromarray(dist_image, mode="RGBA")
    dist_image.save(target.sample_distribution_img_path)

    loadingHandler.kill()

def generate_tangent_normal(target:LocationPaths, path:Path, preview_in_cv=False):
    """
    Take an input of a height map and convert to a tangent normal space image.
    Normal map details: (Might need to double check)\n
      R. Intensity of the normal to face left->right (0->255)\n
      G. Intensity of the normal to face up-down (0->255)\n
      B. Cheap ambient occlusion (not really important)\n

    Reading: http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-13-normal-mapping/
    """
    # loadingHandler = LoadingWindowHandler()
    # loadingHandler.show("Generating Tangent Space Normal Map...")

    # Retrieve height map
    # height_map = cv.imread(str(target.elevation_img_linear_path))

    height_map = height_map.astype("float32")
    height_map = height_map[:,:,0]

    # Attempt at smoothing data via enlarging/shrinking. Might use later.
    
    # original_size = height_map.shape
    # rescaling_factor = 10
    # enlarged_size = height_map.shape[0] * rescaling_factor, height_map.shape[1] * rescaling_factor
    # height_map = cv.resize(height_map, enlarged_size, interpolation=cv.INTER_CUBIC)
    # height_map = gaussian_filter(height_map, sigma=5)
    # height_map = cv.resize(height_map, original_size, interpolation=cv.INTER_AREA)

    # Prepare data collections
    normal_map = np.zeros((height_map.shape[0], height_map.shape[1], 3))
    tangent_data = np.zeros((height_map.shape[0], height_map.shape[1], 3))
    bitangent_data = np.zeros((height_map.shape[0], height_map.shape[1], 3))

    height_map_padded = np.pad(height_map, 1, mode="edge") 
    top = height_map_padded[:-2,1:-1]
    right = height_map_padded[1:-1,2:]
    bottom = height_map_padded[2:,1:-1]
    left = height_map_padded[1:-1,0:-2]

    scale = 0.05

    while True:
        # Retrieve tangent and bitangent data from surrounded pixels
        tangent_data[:,:,0], tangent_data[:,:,1], tangent_data[:,:,2] = np.asarray([scale, 0, right - left], dtype=object)
        bitangent_data[:,:,0], bitangent_data[:,:,1], bitangent_data[:,:,2] = np.asarray([0, scale, bottom - top], dtype=object)
        
        # With a cross product, the normal upward vector is generated
        normal_map = np.cross(tangent_data, bitangent_data)

        # Attempt to restrict the normal values to a range of [-0.99, 0.99]
        length = np.sqrt(normal_map[:,:,0] ** 2 + normal_map[:,:,1] ** 2 + normal_map[:,:,2] ** 2)
        normal_map[:,:,0] = normal_map[:,:,0] / length
        normal_map[:,:,1] = normal_map[:,:,1] / length
        normal_map[:,:,2] = normal_map[:,:,2] / length

        # Prevent a rogue while loops
        if scale > 5: break

        # Check for values that are out of range
        fail_states = [
            np.max(normal_map[:,:,0]) >= 0.99,
            np.max(normal_map[:,:,1]) >= 0.99,
            np.min(normal_map[:,:,0]) <= -0.99,
            np.min(normal_map[:,:,1]) <= -0.99,
        ]
        if any(fail_states):
            print("Pixel value out of scale. Refining scale to " + str(scale))
            scale += 0.05
        else: break

    # Remap pixels from [-1,1] to [0,1] and change green gradient for opengl direction (personal preference)
    normal_map[:,:,0] = (normal_map[:,:,0] / 2) + 0.5
    normal_map[:,:,1] = 0.5 - (normal_map[:,:,1] / 2)
    normal_map[:,:,2] = (normal_map[:,:,2] / 2) + 0.5

    normal_map = np.clip(normal_map, 0.0, 1.0)
    normal_map = normal_map[:, :, ::-1] # colors: [bgr] -> [rgb]
    
    # loadingHandler.kill()

    if preview_in_cv:
        cv.imshow("normal map - RGB", normal_map)
        cv.imshow("normal map - R", normal_map[:,:,0])
        cv.imshow("normal map - G", normal_map[:,:,1])
        cv.imshow("normal map - B", normal_map[:,:,2])
        cv.waitKey()

if __name__ == "__main__":
    path = Path("C:\Users\Patri\Desktop\golf-course-data-processors\SavedAreas\DemoCourse\Elevation_Linear.png")
    generate_tangent_normal()