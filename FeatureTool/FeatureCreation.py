"""
Orginal Concept by Dan Mašek (https://stackoverflow.com/questions/37099262/drawing-filled-polygon-using-mouse-events-in-open-cv-using-python)

Adapted by Adrian Bruno
Changes:
*Debugged
*Added use of background images
*Output changed for use with blender
*
"""

import pandas as pd
import numpy as np
import cv2
import pyautogui as pag


# ============================================================================

# CANVAS_SIZE = (600,800)
FINAL_LINE_COLOR = (255, 255, 255)
WORKING_LINE_COLOR = (255, 0, 0)

ROUGH_COLOR = (34, 139, 34)
FAIRWAY_COLOR = (60, 192, 3)
GREEN_COLOR = (128, 178, 194)
SAND_COLOR = (119, 221, 119)
FEATURE_COLORS = (FAIRWAY_COLOR, GREEN_COLOR, SAND_COLOR)
FEATURE_NAMES = ("Fairway", "Green", "SandTraps")
# ============================================================================


class PolygonDrawer(object):
    def __init__(self, window_name, cvImage):
        self.screen_res = pag.size()
        self.window_name = window_name  # Name for our window

        self.done = False  # Flag signalling we're done
        self.current = (0, 0)  # Current position, so we can draw the line-in-progress
        # Lists of points defining our polygons
        self.points = {
            "f": [],  # Fairway
            "g": [],  # Green
            "s": [],  # Sand
            #'t': [], #Trees
        }
        # list of coordinates adjusted for the bottom left origin
        self.points_adj = {
            "f": [],  # Fairway
            "g": [],  # Green
            "s": [],  # Sand
            # 't': [], #Trees
        }

        if type(cvImage) == str:
            self.canvas = cv2.imread(cvImage)
        else:
            self.canvas = cvImage

        if self.canvas.shape[0] > self.canvas.shape[1]:
            self.canvas = cv2.rotate(self.canvas, cv2.ROTATE_90_CLOCKWISE)

        self.y, self.x = self.canvas.shape[:2]
        self.featureCanv = np.zeros((self.y, self.x, 3), np.uint8)
        self.featureCanv[:] = ROUGH_COLOR
        self.holder_list = []
        self.holder_list_adj = []

    def on_mouse(
        self, event, x, y, buttons, user_param
    ):  # , holder_list, holder_list_adj):
        # Mouse callback that gets called for every mouse event (i.e. moving, clicking, etc.)
        adj_y = self.canvas.shape[0] - y
        if self.done:  # Nothing more to do
            return
        if event == cv2.EVENT_MOUSEMOVE:
            # We want to be able to draw the line-in-progress, so update current mouse position
            self.current = (x, y)
        elif event == cv2.EVENT_LBUTTONDOWN:
            # Left click means adding a point at current position to the list of points
            print(
                "Adding point #%d with position(%d,%d)"
                % (len(self.holder_list), x, adj_y)
            )
            # self.points[feature_type][len(self.points[feature_type])-1].append((x, y))
            self.holder_list.append((x, y))
            self.holder_list_adj.append((x, adj_y, 0))
            # self.points_adj[feature_type][len(self.points[feature_type])-1].append((x,adj_y,0))
        elif event == cv2.EVENT_RBUTTONDOWN:
            # Right click means we're done
            print("Completing polygon with %d points." % len(self.holder_list))
            self.done = True

    def getIndex(self, item, inList):
        for i, j in enumerate(inList):
            if j == item:
                return i
            else:
                print("item not found")

    # 960x540
    # feature types fairway = 0, green = 1, sandtraps = 2, done = 3
    def run(self, feature_type, recurse_img):
        self.holder_list = []
        self.holder_list_adj = []

        # print("Length: %d\n" % len(self.holder_list))
        self.featureCanv = recurse_img
        if not feature_type in ("f", "s", "g", "d"):
            return "incorrect feature type"

        working_index = len(self.points[feature_type]) - 1
        # Let's create our working window and set a mouse callback to handle events
        cv2.namedWindow(self.window_name, flags=cv2.cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, 1280, 720)
        cv2.imshow(self.window_name, self.canvas)
        cv2.waitKey(1)
        cv2.setMouseCallback(self.window_name, self.on_mouse)

        canvasOrig = self.canvas.copy()
        while not self.done:
            self.canvas = canvasOrig.copy()
            # This is our drawing loop, we just continuously draw new images
            # and show them in the named window
            if len(self.holder_list) > 0:
                # Draw all the current polygon segments
                cv2.polylines(
                    self.canvas,
                    np.array([self.holder_list]),
                    False,
                    FINAL_LINE_COLOR,
                    1,
                )
                # And  also show what the current segment would look like
                cv2.line(
                    self.canvas, self.holder_list[-1], self.current, WORKING_LINE_COLOR
                )
            # Update the window
            cv2.imshow(self.window_name, self.canvas)
            # And wait 50ms before next iteration (this will pump window messages meanwhile)
            if cv2.waitKey(50) == 27:  # ESC hit
                self.done = True

        # add the temp arrays to
        self.points[feature_type].append(self.holder_list)
        self.points_adj[feature_type].append(self.holder_list_adj)

        # User finised entering the polygon points, so let's make the final drawing
        ##canvas = cv2.imread("PIL_IMAGE.tif")
        # of a filled polygon
        print(type(feature_type))
        print(feature_type)
        feature_index = self.getIndex(feature_type, ("f", "s", "g", "d"))
        #        for i,j in enumerate(('f','s','g','d')):
        #            if j == feature_type:
        #                fill_index = i
        if len(self.points[feature_type][working_index]) > 0:
            # np.array([self.points[feature_type][working_index]])
            # cv2.fillPoly(self.canvas, np.array([self.points[feature_type][working_index]]), FINAL_LINE_COLOR)
            cv2.fillPoly(self.canvas, np.array([self.holder_list]), FINAL_LINE_COLOR)
            cv2.fillPoly(
                self.featureCanv,
                np.array([self.holder_list]),
                FEATURE_COLORS[feature_index],
            )

        self.canvas = cv2.addWeighted(self.canvas, 0.2, canvasOrig, 0.8, 0)
        # And show it
        cv2.imshow(self.window_name, self.canvas)

        cv2.namedWindow(FEATURE_NAMES[feature_index], flags=cv2.cv2.WINDOW_NORMAL)
        cv2.resizeWindow(FEATURE_NAMES[feature_index], 1280, 720)
        cv2.imshow(FEATURE_NAMES[feature_index], self.featureCanv)
        # Waiting for the user to press any key
        cv2.waitKey()
        cv2.waitKey()

        cv2.destroyWindow(self.window_name)
        cv2.destroyWindow(FEATURE_NAMES[feature_index])
        return self.canvas, self.featureCanv


# ============================================================================

if __name__ == "__main__":
    pd = PolygonDrawer("Polygon", "PIL_IMAGE.tif")
    feature_image = pd.featureCanv
    image = pd.run(0, feature_image)
    # cv2.imwrite("polygon.png", image)
    print("Polygon = %s" % pd.points_adj)
    print(pd.x, "\t", pd.y)
