"""
@author: Adrian Bruno
"""
import cv2

# from PIL import Image
import numpy as np

# import bpy
# import bmesh
import math
import sys
import os
import pandas as pd

#
# dir = os.path.dirname(bpy.data.filepath)
# if not dir in sys.path:
#    sys.path.append(dir )
#    #print(sys.path)

# import MeshFromVertsTesting as mv
from FeatureCreation import PolygonDrawer
from GoogleMapsAPI import SatelliteInterface as si

# this next part forces a reload in case you edit the source after you first start the blender session
# import imp
# imp.reload(mv)


##Hole One Coordinates
NW_lat_long = (35.579718, -82.500727)
SE_lat_long = (35.576171, -82.496849)

# New instance of ApiInterface
# newSi = si("AIzaSyAi63zbrCv-tiXms4o6lnhY1c1") # Maddhatt.pm@gmail.com account
newSi = si("AIzaSyAi63zbrCv-tiXms4o6lnhY1c1W1MpzWZ0")  # Maddhatt.pm@gmail.com account

# image constructed from API interface methods
result = newSi.get_maps_image(NW_lat_long, SE_lat_long, zoom=19)
# result.show()


# Function  Converting the PIL image into a cv compatable
def pilToCv(pil_image):
    open_cv_image = np.array(pil_image)
    # Convert RGB to BGR
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    return open_cv_image


# cv imagef
resultCv = pilToCv(result)


cv2.imwrite("holeImg.tif", resultCv)
# display the image
cv2.namedWindow("hole", flags=cv2.cv2.WINDOW_NORMAL)
cv2.resizeWindow("hole", 1280, 720)
cv2.imshow("hole", resultCv)
if cv2.waitKey():
    cv2.destroyAllWindows()

print(newSi.pixels2latlon(0, 291, 19))


# Outlining feature with vertices

polyD = PolygonDrawer("Polygon", resultCv)
drawing = True
features = polyD.featureCanv


image = None

while drawing:
    polyD.done = False
    type = input("Feature Types:\nFairway-'f', Green-'g' SandTraps-'s',Done-'d'\n")
    if type == "d" or type == "D":
        drawing = False
    else:
        image, features = polyD.run(feature_type=type, recurse_img=features)

cv2.imwrite("polygonMain.png", image)
cv2.imwrite("Features.png", features)

feature_points = pd.DataFrame.from_dict(polyD.points_adj, orient="index")
feature_points = feature_points.transpose()

feature_points.to_excel("Hole_features.xlsx")

print("Polygon = %s" % polyD.points_adj)
print(polyD.x, "\t", polyD.y)

with open("Img_data.txt", "w") as out_file:
    out_file.write(
        "%f %f\n%f %f\n"
        % (NW_lat_long[0], NW_lat_long[1], SE_lat_long[0], SE_lat_long[1])
    )
    out_file.write("%d %d" % (image.shape[0], image.shape[1]))

# holeVerts = polyD.points_adj


# filledVerts = mv.fill_Vertices(10,holeVerts)

# mv.create_Vertices("test", filledVerts)
#
# mv.make_edges('test')
# print(holeVerts)
# bpy.ops.mesh.select_all(action = 'SELECT')

# bpy.ops.mesh.fill_grid(span=3)
# bpy.ops.mesh.subdivide(smoothness=0)
