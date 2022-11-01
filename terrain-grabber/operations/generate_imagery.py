from pathlib import Path
from tkinter.messagebox import showwarning
from PIL import Image
from matplotlib import pyplot as plt
import numpy as np
from scipy.interpolate import griddata
from scipy import ndimage
from asset_area import LocationPaths

def generate_imagery(target: LocationPaths, levels:int=50):
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

    def resize_to_satelite(img_path:Path):
        img = Image.open(img_path)
        img = img.resize(Image.open(target.sateliteImg_path).size)
        img.save(img_path)

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

    # dilate all the points
    
    # plt.plot(xLats, yLongs, 'r.')
    # plt.axis('off')
    # plt.savefig(target.sampleDistributionImg_path, bbox_inches='tight', pad_inches=0, transparent=True)
    # plt.clf()

    # img = Image.open(target.sampleDistributionImg_path)
    # img.crop(img.getbbox())
    # img.save(target.sampleDistributionImg_path)

    # resize_to_satelite(target.sampleDistributionImg_path)
    # print("Point distribution generated")

    '''Save out gradient maps in all three interpolation methods'''
    multiplier = 10000
    width = (SE[1] - NW[1]) * multiplier
    height = (NW[0] - SE[0]) * multiplier
    plt.figure(figsize= (width, height))

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

        resize_to_satelite(filepath)
        print("{} interpolated elevation gradient map generated".format(config[0].title()))

    for config in grad_configs:
        plot_gradmap(config)

    '''Save out contour map'''
    plt.clf()
    plt.tricontour(xLats, yLongs, zEle, levels=levels, cmap='inferno')
    plt.axis('off')
    plt.savefig(target.contourImg_path, bbox_inches='tight', pad_inches=0, transparent=True)
    resize_to_satelite(target.contourImg_path)
    print("Tricontour map generated")