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
color_select_modes = [modes.M_FLOOD_MASKER]
color_sensitivity = [25]

"""DO NOT REFERENCE DIRECTLY - Weird stuff happens"""
bgr_img = cv.imread(str(inpath), 1)
hsv_img = cv.cvtColor(bgr_img, cv.COLOR_BGR2HSV)
mask_img = bgr_img.copy()
mask_img.fill(255)
combined_img = bgr_img.copy()


base_imgs: dict[str, cv.Mat] = {
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
    if view_mode == modes.VIEW_COMBINED:
        base_imgs[modes.VIEW_COMBINED] = base_imgs[modes.VIEW_BGR].copy()
        mask = base_imgs[modes.VIEW_MASK]
        b, g, r = cv.split(mask)
        checker = util_imgs[modes.UTIL_CHECKER]
        base_imgs[modes.VIEW_COMBINED][np.where(b == 0)] = checker[np.where(b == 0)]

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
                color=(0, 0, 255),
                opacity=0.5,
            )

    cv.imshow(win_title, viewport_img)


def onclick(event, x, y, flags, param):
    left_click = 1
    right_click = 2

    if ctrl_mode in crosshair_modes:
        if event == left_click:
            x, y = unapply_zoom(x, y, zoom_level)
            click_positions.append((x, y))
            if len(click_positions) > 2:
                click_positions.pop(0)
            rerender()

        if event == right_click:
            if len(click_positions) != 0:
                click_positions.pop()
                rerender()

    if ctrl_mode in color_select_modes:
        """Floodfill documentation https://docs.opencv.org/2.4/modules/imgproc/doc/miscellaneous_transformations.html?highlight=floodfill"""
        invert = event == right_click
        if event == left_click:
            w, h, channels = base_imgs[view_mode].shape
            print(w, h)
            mask = np.zeros((w + 2, h + 2), np.uint8)  # Add border

            sel_mode = view_mode
            print(sel_mode)
            if sel_mode != modes.VIEW_BGR or sel_mode != modes.VIEW_HSV:
                sel_mode = modes.VIEW_BGR

            sensitivty = color_sensitivity[0]
            sensitivty = (sensitivty, sensitivty, sensitivty, sensitivty)

            flags = 4
            flags |= cv.FLOODFILL_MASK_ONLY
            flags |= 255 << 8

            retval, base_imgs[sel_mode], mask, rect = cv.floodFill(
                base_imgs[sel_mode],
                mask,
                seedPoint=unapply_zoom(x, y, zoom_level),
                newVal=(0, 0, 0),
                loDiff=sensitivty,
                upDiff=sensitivty,
                flags=flags,
            )

            # Delete border
            mask = np.delete(mask, 0, 0)
            mask = np.delete(mask, -1, 0)
            mask = np.delete(mask, 0, 1)
            mask = np.delete(mask, -1, 1)

            # Isolate red channel (bgr)
            r = np.zeros((w, h, channels), np.uint8)
            r[:, :, 2] = 255

            if invert:
                pass
            else:
                base_imgs[modes.VIEW_MASK][np.where(mask == 255)] = r[
                    np.where(mask == 255)
                ]

            rerender()


cv.setMouseCallback(win_title, onclick)

while does_window_exist(win_title):
    action = cv.waitKey(0)
    print(action)

    if ctrl_mode == modes.M_DEFAULT:
        """--> Crop Mode"""
        if action == ord("1"):
            ctrl_mode = modes.M_CROP
            controls_win.switch_to(ctrl_mode)

        """--> Rotate Mode"""
        if action == ord("2"):
            ctrl_mode = modes.M_ROTATE
            controls_win.switch_to(ctrl_mode)

        """--> Rotate Mode"""
        if action == ord("3"):
            ctrl_mode = modes.M_FLOOD_MASKER
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
            for mat in base_imgs:
                base_imgs[mat] = cv.flip(base_imgs[mat], flipCode=0)
            rerender()

        """Flip horizontally"""
        if action == ord("s"):
            for mat in base_imgs:
                base_imgs[mat] = cv.flip(base_imgs[mat], flipCode=1)
            rerender()

        """Rotate Clockwise 90°"""
        if action == ord("a"):
            for mat in base_imgs:
                base_imgs[mat] = cv.rotate(base_imgs[mat], cv.ROTATE_90_CLOCKWISE)
            rerender()

        """Rotate Counterclockwise 90°"""
        if action == ord("d"):
            for mat in base_imgs:
                base_imgs[mat] = cv.rotate(
                    base_imgs[mat], cv.ROTATE_90_COUNTERCLOCKWISE
                )
            rerender()

    if ctrl_mode == modes.M_FLOOD_MASKER:
        """Dilate selection"""
        if action == ord("w"):
            kernal = np.ones((5, 5), np.uint8)

            temp = base_imgs[modes.VIEW_MASK].copy()
            b, green, r = cv.split(temp)

            green = cv.erode(green, kernal, iterations=1)
            temp = cv.merge((b, green, r))

            base_imgs[modes.VIEW_MASK][:, :, :] = temp
            rerender()

        """Erode selection"""
        if action == ord("s"):
            kernal = np.ones((5, 5), np.uint8)

            temp = base_imgs[modes.VIEW_MASK].copy()
            b, green, r = cv.split(temp)
            # temp = cv.bitwise_not(temp)
            green = cv.bitwise_xor(green, r)
            # cv.imshow("red", r)
            # cv.imshow("green", green)

            green = cv.erode(green, kernal, iterations=1)
            green = cv.bitwise_not(green)
            cv.imshow("green", green)
            temp = cv.merge((b, green, r))
            # temp = cv.bitwise_not(temp)

            base_imgs[modes.VIEW_MASK][:, :, :] = temp
            rerender()

        """Increase sensitivity by -5"""
        if action == ord("d"):
            color_sensitivity[0] += 5
            print(color_sensitivity[0])

        """Increase sensitivity by +5"""
        if action == ord("a"):
            color_sensitivity[0] -= 5
            print(color_sensitivity[0])

        """Reject from mask"""
        BACKSPACE = 8
        if action == BACKSPACE:
            _, _, r = cv.split(base_imgs[modes.VIEW_MASK])
            base_imgs[modes.VIEW_MASK] = cv.merge((r, r, r))
            rerender()
            print("cleared")

        """Apply to mask"""
        ENTER = 13
        if action == ENTER:
            b, g, _ = cv.split(base_imgs[modes.VIEW_MASK])
            b = cv.bitwise_or(b, g)
            base_imgs[modes.VIEW_MASK] = cv.merge((b, b, b))
            rerender()

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
