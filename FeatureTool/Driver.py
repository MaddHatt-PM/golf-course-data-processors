"""
@author OG: Adrian Bruno

@author 2022: Patt Martin
Changes:
    - Code cleanup
"""

import cv2
import numpy as np
import pandas as pd
import APIKeys as keys
from pathlib import Path
from FeatureCreation import PolygonDrawer
from GoogleMapsAPI import SatelliteInterface as si

# Folder setup
areaBase = Path("SavedAreas/")
areaName = areaBase.joinpath(Path("area_name/"))
sateliteImg = Path("SateliteImg-Test.tif")
areaName.mkdir(parents=True, exist_ok=True)

# New instance of ApiInterface
newSi = si(keys.google_maps)

# Map Coordinates to retrieve
NW_lat_long = (35.579718, -82.500727)
SE_lat_long = (35.576171, -82.496849)

# image constructed from API interface methods
result = newSi.get_maps_image(NW_lat_long, SE_lat_long, zoom=19)

# Function  Converting the PIL image into a cv compatable
def pil_to_cv(pil_image):
    open_cv_image = np.array(pil_image)
    # Convert RGB to BGR
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    return open_cv_image


# cv imagef
resultCv = pil_to_cv(result)
cv2.imwrite(filename=str(areaName.joinpath(sateliteImg)), img=resultCv)


# # display the image
# cv2.namedWindow("hole", flags=cv2.cv2.WINDOW_NORMAL)
# cv2.resizeWindow("hole", result.width, result.height)
# cv2.imshow("hole", resultCv)
# if cv2.waitKey():
#     cv2.destroyAllWindows()

# print(newSi.pixels2latlon(0, 291, 19))


# # Outlining feature with vertices
# polyD = PolygonDrawer("Polygon", resultCv)
# drawing = True
# features = polyD.featureCanv
# image = None

# while drawing:
#     polyD.done = False
#     type = input("Feature Types:\nFairway-'f', Green-'g' SandTraps-'s',Done-'d'\n")
#     if type == "d" or type == "D":
#         drawing = False
#     else:
#         image, features = polyD.run(feature_type=type, recurse_img=features)

# cv2.imwrite("polygonMain.png", image)
# cv2.imwrite("Features.png", features)

# feature_points = pd.DataFrame.from_dict(polyD.points_adj, orient="index")
# feature_points = feature_points.transpose()
# feature_points.to_excel("Hole_features.xlsx")

# print("Polygon = %s" % polyD.points_adj)
# print(polyD.x, "\t", polyD.y)

# with open("Img_data.txt", "w") as out_file:
#     out_file.write(
#         "%f %f\n%f %f\n"
#         % (NW_lat_long[0], NW_lat_long[1], SE_lat_long[0], SE_lat_long[1])
#     )
#     out_file.write("%d %d" % (image.shape[0], image.shape[1]))
