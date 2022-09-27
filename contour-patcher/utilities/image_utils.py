import cv2 as cv
from cv2 import Mat


def zoom(img: Mat, zoom_factor=1) -> Mat:
    return cv.resize(
        img, dsize=None, fx=zoom_factor, fy=zoom_factor, interpolation=cv.INTER_LANCZOS4
    )


def crop(img: Mat, x0, y0, x1, y1) -> Mat:
    if x0 > x1:
        x0, x1 = x1, x0

    if y0 > y1:
        y0, y1 = y1, y0

    x0 = int(x0)
    y0 = int(y0)
    x1 = int(x1)
    y1 = int(y1)

    return img[y0:y1, x0:x1]


def apply_zoom(x, y, zoom_level) -> tuple[float, float]:
    return x * zoom_level, y * zoom_level


def unapply_zoom(x, y, zoom_level) -> tuple[float, float]:
    return x / zoom_level, y / zoom_level
