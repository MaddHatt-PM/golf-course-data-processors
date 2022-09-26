from utilities.image_utils import crop
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


def inverted_rectangle(img: Mat, x0, y0, x1, y1, zoom, color: tuple, opacity) -> Mat:
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


def make_checker_img(img: Mat) -> Mat:
    output = img.copy()
    light_color = (230, 230, 230)
    dark_color = (215, 215, 215)
    sqr_l = 10
    tile_l = sqr_l * 2

    pattern = np.zeros((tile_l, tile_l, 3), dtype=np.uint8)
    pattern[:, :] = light_color
    pattern[:sqr_l:, :sqr_l:] = dark_color
    pattern[sqr_l:tile_l:, sqr_l:tile_l:] = dark_color

    w, h, channels = output.shape
    print(w, h)
    pattern = np.tile(pattern, ((w // tile_l) + 1, (h // tile_l) + 1, 1))
    output = crop(pattern, 0, 0, h, w, 1.0)
    print(output.shape)
    return output
