import numpy as np
import cv2 as cv
from cv2 import Mat


def crosshair(img: Mat, x, y) -> Mat:

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


def inverted_rectangle(img: Mat, x0, y0, x1, y1, color: tuple, opacity) -> Mat:
    output = np.zeros_like(img, dtype=np.uint8)
    output[:, :, -1] = 255
    if x0 > x1:
        x0, x1 = x1, x0

    if y0 > y1:
        y0, y1 = y1, y0

    x0 = int(x0)
    y0 = int(y0)
    x1 = int(x1)
    y1 = int(y1)

    output[y0:y1, x0:x1] = img[y0:y1, x0:x1]
    cv.addWeighted(img, opacity, output, 1 - opacity, 0, output)

    return output
