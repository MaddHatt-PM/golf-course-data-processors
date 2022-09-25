import numpy as np
import cv2 as cv


def draw_crosshair(x, y, img):

    """White Outline"""
    img = cv.drawMarker(
        img,
        position=(int(x), int(y)),
        color=(255, 255, 255),
        markerType=cv.MARKER_CROSS,
        thickness=2,
    )
    """Red Crosshair"""
    img = cv.drawMarker(
        img,
        position=(int(x), int(y)),
        color=(0, 0, 255),
        markerType=cv.MARKER_CROSS,
        thickness=1,
    )
    """Red Diamond"""
    img = cv.drawMarker(
        img,
        position=(int(x), int(y)),
        color=(0, 0, 255),
        markerType=cv.MARKER_DIAMOND,
        markerSize=5,
        thickness=3,
    )

    return img
