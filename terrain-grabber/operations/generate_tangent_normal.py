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

def generate_tangent_normal(target:str, preview_in_cv=False):
    """
    Take an input of a height map and convert to a tangent normal space image.
    Normal map details: (Might need to double check)\n
      R. Intensity of the normal to face left->right (0->255)\n
      G. Intensity of the normal to face up-down (0->255)\n
      B. Cheap ambient occlusion (not really important)\n

    Reading: http://www.opengl-tutorial.org/intermediate-tutorials/tutorial-13-normal-mapping/
    """

    # Retrieve height map
    height_map = cv.imread(target)
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
    
    if preview_in_cv:
        cv.imshow("normal map - R", normal_map[:,:,0])
        cv.imshow("normal map - G", normal_map[:,:,1])
        cv.imshow("normal map - B", normal_map[:,:,2])
        cv.imshow("normal map - RGB", normal_map)
        cv.waitKey()

if __name__ == "__main__":
    generate_tangent_normal(
        target="C:\\Users\\Patri\\Desktop\\golf-course-data-processors\\SavedAreas\\DemoCourse\\Elevation_Linear.png",
        preview_in_cv=True
        )