import os
import sys
import cv2 as cv
import numpy as np

import modes
from controls_handler import ControlsHandler
from utilities import process_sys_args
from utilities.image_utils import zoom, crop, apply_zoom, unapply_zoom
from utilities.window_utils import does_window_exist
from utilities.canvas_drawers import crosshair, inverted_rectangle, make_checker_img


inpath, outpath = process_sys_args()


ctrl_mode = modes.M_DEFAULT
crosshair_modes = [modes.M_CROP]


bgr_img = cv.imread(str(inpath), 1)
hsv_img = cv.cvtColor(bgr_img, cv.COLOR_BGR2HSV)
# mask_img: cv.Mat = cv.threshold(bgr_img[:, :, 2], 0, 255, cv.THRESH_BINARY)[1]
mask_img = bgr_img.copy()
mask_img.fill(255)
mask_img = cv.rectangle(mask_img, (200, 200), (500, 600), 0, -1)

combined_img = bgr_img.copy()
combined_dirty = True


base_imgs = {
    modes.VIEW_BGR: bgr_img,
    modes.VIEW_HSV: hsv_img,
    modes.VIEW_MASK: mask_img,
    modes.VIEW_COMBINED: combined_img,
}

util_imgs = {
    modes.UTIL_CHECKER: make_checker_img(bgr_img),
}

view_mode = modes.VIEW_BGR
viewport_img = bgr_img.copy()
ZOOM_MULTIPLIER = 1.25
zoom_level = 1.0

win_title = "Input Image"
cv.imshow(win_title, viewport_img)
controls_win = ControlsHandler(win_title)

click_positions = []
click_pos_restrict = 100


def rerender():
    global combined_dirty
    if view_mode == modes.VIEW_COMBINED and combined_dirty is True:
        print("happened")
        combined_dirty = False
        mask = base_imgs[modes.VIEW_MASK]
        checker = util_imgs[modes.UTIL_CHECKER]
        combined_img[np.where(mask == 0)] = checker[np.where(mask == 0)]

    viewport_img = base_imgs[view_mode]
    viewport_img = zoom(viewport_img, zoom_level)

    if ctrl_mode in crosshair_modes:
        for pos in click_positions:
            x, y = pos[0] * zoom_level, pos[1] * zoom_level
            viewport_img = crosshair(viewport_img, x, y)

        if len(click_positions) == 2:
            viewport_img = inverted_rectangle(
                viewport_img,
                *apply_zoom(*click_positions[-1], zoom_level),
                *apply_zoom(*click_positions[-2], zoom_level),
                zoom_level,
                (0, 0, 255),
                0.5,
            )

    cv.imshow(win_title, viewport_img)


def onclick(event, x, y, flags, param):
    if ctrl_mode in crosshair_modes:
        left_click = 1
        if event == left_click:
            x, y = unapply_zoom(x, y, zoom_level)
            click_positions.append((x, y))
            if len(click_positions) > 2:
                click_positions.pop(0)
            rerender()

        right_click = 2
        if event == right_click:
            if len(click_positions) != 0:
                click_positions.pop()
                rerender()


cv.setMouseCallback(win_title, onclick)

while does_window_exist(win_title):
    action = cv.waitKey(0)
    print(action)

    """Reset Zoom"""
    if action == ord("0"):
        zoom_level = 1.0
        rerender()

    """Zoom in"""
    if action == ord("+") or action == ord("="):
        zoom_level *= ZOOM_MULTIPLIER
        zoom_level = min(zoom_level, ZOOM_MULTIPLIER**3)
        rerender()

    """Zoom out"""
    if action == ord("-"):
        zoom_level /= ZOOM_MULTIPLIER
        zoom_level = max(zoom_level, ZOOM_MULTIPLIER**-3)
        rerender()

    """Change view mode"""
    if action == ord("`") or action == ord("~"):
        keys = list(base_imgs.keys())
        index = keys.index(view_mode)
        index = (1 + index) % len(base_imgs)
        view_mode = keys[index]

        if view_mode == modes.VIEW_COMBINED:
            pass
            # if np.any(base_imgs[modes.VIEW_COMBINED], axis=3, ):
            #     keys = list(base_imgs.keys())
            #     index = keys.index(view_mode)
            #     index = (1 + index) % len(base_imgs)
            #     view_mode = keys[index]
        rerender()

    """Return to default view mode"""
    ESC = 27
    if action == ESC:
        view_mode = modes.VIEW_BGR
        rerender()

    if ctrl_mode == modes.M_DEFAULT:
        """--> Crop Mode"""
        if action == ord("1"):
            ctrl_mode = modes.M_CROP
            controls_win.switch_to(ctrl_mode)

        """--> Rotate Mode"""
        if action == ord("2"):
            ctrl_mode = modes.M_ROTATE
            controls_win.switch_to(ctrl_mode)

        """Save result"""
        if action == ord("s"):
            result = base_imgs[modes.VIEW_BGR]
            mask = cv.split(base_imgs[modes.VIEW_MASK])[0]
            result = np.dstack((result, mask))

            cv.imwrite(str(outpath), result)
            os.startfile(str(outpath.parent))

    if ctrl_mode == modes.M_CROP:
        """Crop"""
        ENTER = 13
        if action == ENTER or action == ord("c"):
            if len(click_positions) >= 2:
                for img in list(base_imgs.keys()):
                    base_imgs[img] = crop(
                        base_imgs[img],
                        *apply_zoom(*click_positions[-1], zoom_level),
                        *apply_zoom(*click_positions[-2], zoom_level),
                    )

                zoom_level = 1.0
                click_positions.clear()
                click_pos_restrict = 2
                rerender()

    if ctrl_mode == modes.M_ROTATE:
        """Flip vertically"""
        if action == ord("w"):
            bgr_img = cv.flip(bgr_img, flipCode=0)
            rerender()

        """Flip horizontally"""
        if action == ord("s"):
            bgr_img = cv.flip(bgr_img, flipCode=1)
            rerender()

        """Rotate Clockwise 90°"""
        if action == ord("a"):
            bgr_img = cv.rotate(bgr_img, cv.ROTATE_90_CLOCKWISE)
            rerender()

        """Rotate Counterclockwise 90°"""
        if action == ord("d"):
            bgr_img = cv.rotate(bgr_img, cv.ROTATE_90_COUNTERCLOCKWISE)
            rerender()

    if ctrl_mode == modes.M_COLOR_MASKER:
        ENTER = 13
        """Dilate selection"""
        if action == ord("w"):
            pass

        """Erode selection"""
        if action == ord("s"):
            pass

        """Apply to mask"""
        if action == ENTER:
            pass

    """Return to default or quit"""
    if action == ord("q"):
        if ctrl_mode != modes.M_DEFAULT:
            ctrl_mode = modes.M_DEFAULT
            controls_win.switch_to(ctrl_mode)
            rerender()
            continue

        else:
            break


controls_win.kill()
cv.destroyAllWindows()
