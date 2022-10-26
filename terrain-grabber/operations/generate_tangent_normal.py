import cv2 as cv
import numpy as np
from pathlib import Path

def generate_tangent_normal(heightmapPath:Path):
    heightmap = cv.imread(str(heightmapPath))
    heightmap = heightmap.astype("float64")

    np.gradient(heightmap)

    normals = np.array(heightmap, dtype="float32")
    h,w,d = heightmap.shape
    for i in range(1,w-1):
        for j in range(1,h-1):
            t = np.array([i,j-1,heightmap[j-1,i,0]],dtype="float64")
            f = np.array([i-1,j,heightmap[j,i-1,0]],dtype="float64")
            c = np.array([i,j,heightmap[j,i,0]] , dtype = "float64")
            d = np.cross(f-c,t-c)
            n = d / np.sqrt((np.sum(d**2)))
            normals[j,i,:] = n

    cv.imwrite("normal.png", normals*255)
    cv.imshow("normals", cv.imread("normal.png"))
    cv.waitKey(0)

if __name__ == "__main__":
    generate_tangent_normal(Path('D:\Golf Project\course_modeling\misc-data\Kbsd_Heightmap_Example.jpg'))