from pathlib import Path
from tkinter.messagebox import showwarning
from PIL import Image
from matplotlib import pyplot as plt
import numpy as np
from scipy.interpolate import griddata
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
        min(range_x):max(range_x) :5000j,
        min(range_y): max(range_y):5000j
    ]

    def resize_to_satelite(img_path:Path):
        img = Image.open(img_path)
        img = img.resize(Image.open(target.sateliteImg_path).size)
        img.save(img_path)

    '''Plot, crop, and save out sample distribution'''
    # print(Image.open(target.sateliteImg_path).info['dpi'])

    height = NW[0] - SE[0]
    width = SE[1] - NW[1]
    multiplier = 10000
    
    plt.figure(figsize= (width * multiplier, height * multiplier))
    plt.plot(x, y, 'r.')
    plt.axis('off')
    plt.savefig(target.sampleDistributionImg_path, bbox_inches='tight', pad_inches=0, transparent=True)
    plt.clf()

    img = Image.open(target.sampleDistributionImg_path)
    img.crop(img.getbbox())
    img.save(target.sampleDistributionImg_path)

    resize_to_satelite(target.sampleDistributionImg_path)
    print("Point distribution generated")

    '''Save out gradient maps in all three interpolation methods'''
    grad_configs = [
        ('nearest', target.elevationImg_nearest_path),
        ('linear', target.elevationImg_linear_path),
    ]

    def plot_gradmap(config:tuple[str, str]):
        interpolation, filepath = config
        height_data = griddata(xy, z, (grid_x, grid_y), method=interpolation)

        plt.imshow(
            height_data,
            extent=(SE[1], NW[1], SE[0], NW[0]),
            origin='lower',
            cmap='cubehelix')

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
    plt.tricontour(x, y, z, levels=levels, cmap='inferno')
    plt.axis('off')
    plt.savefig(target.contourImg_path, bbox_inches='tight', pad_inches=0, transparent=True)
    resize_to_satelite(target.contourImg_path)
    print("Tricontour map generated")