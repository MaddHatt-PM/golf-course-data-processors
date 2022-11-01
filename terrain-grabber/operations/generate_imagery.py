import os
from pathlib import Path
from tkinter.messagebox import showwarning
from PIL import Image
from matplotlib import pyplot as plt
import numpy as np
from scipy.interpolate import griddata
from scipy import ndimage
from loading import LoadingWindowHandler
from asset_area import LocationPaths

def resize_to_satelite(target: LocationPaths, img_path:Path):
    img = Image.open(img_path)
    img = img.resize(Image.open(target.sateliteImg_path).size)
    img.save(img_path)

def generate_imagery(target: LocationPaths, contour_levels:int=50, contour_thickness:float=1.5):

    generate_sample_distribution_map(target)
    generate_gradient_maps(target)
    generate_contour_map(target, contour_levels, contour_thickness)


def prepare_to_bake(target):
    with target.coordinates_path.open('r') as file:
        lines = file.read().splitlines()
        headers = lines.pop(0).split(',')
        NW = eval(lines[0])
        SE = eval(lines[1])

    with target.elevationCSV_path.open('r') as file:
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

def generate_gradient_maps(target):
    NW, SE, xLats, yLongs, zEle, xOffsets, yOffsets, xyLatLongs, grid_x, grid_y = prepare_to_bake(target)
    

    loadingHandler = LoadingWindowHandler()
    loadingHandler.show("Generating Height Maps... May take some time...")

    '''Save out gradient maps in all three interpolation methods'''


    grad_configs = [
        ('nearest', target.elevationImg_nearest_path),
        ('linear', target.elevationImg_linear_path),
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

def generate_contour_map(target, contour_levels, contour_thickness):
    NW, SE, xLats, yLongs, zEle, xOffsets, yOffsets, xyLatLongs, grid_x, grid_y = prepare_to_bake(target)

    loadingHandler = LoadingWindowHandler()
    loadingHandler.show("Generating Contour Map...")

    '''Save out contour map'''
    plt.clf()
    plt.rcParams["contour.linewidth"] = contour_thickness
    plt.tricontour(xLats, yLongs, zEle, levels=contour_levels, cmap='inferno')
    plt.axis('off')
    plt.savefig(target.contourImg_path, bbox_inches='tight', pad_inches=0, transparent=True)
    resize_to_satelite(target, target.contourImg_path)

    loadingHandler.kill()
    print("Tricontour map generated")

def generate_sample_distribution_map(target):
    NW, SE, xLats, yLongs, zEle, xOffsets, yOffsets, xyLatLongs, grid_x, grid_y = prepare_to_bake(target)
    
    loadingHandler = LoadingWindowHandler()
    loadingHandler.show("Generating Sample Distribution Map...")
    
    '''Plot, crop, and save out sample distribution'''
    width, height = Image.open(target.sateliteImg_path).size
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
    dist_image.save(target.sampleDistributionImg_path)

    loadingHandler.kill()