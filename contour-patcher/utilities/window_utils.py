import cv2 as cv


def does_window_exist(win_title):
    try:
        return cv.getWindowProperty(win_title, 1) != -1
    except:
        return False
