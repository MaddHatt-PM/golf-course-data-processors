from math import cos, sin, radians, degrees


def clamp01(value) -> float:
    return max(min(value, 1.0), 0.0)

def clamp(value, min_value, max_value) -> float:
    return max(min(value, max_value), min_value)

def meter_to_feet(m:float) -> float:
    return m / 0.3048

def feet_to_meter(f:float) -> float:
    return f * 0.3048

def remap(val, in_min, in_max, out_min, out_max) -> float:
    return out_min + (val - in_min) * (out_max - out_min) / (in_max - in_min)

def rotate_from_2d_point(x, y, from_x, from_y, theta, as_degrees=True) -> tuple:
    if as_degrees:
        theta = radians(theta)

    rot_mat = [
        [cos(theta), -sin(theta)],
        [sin(theta), cos(theta)]
    ]

    x -= from_x
    y -= from_y

    output = (
        x * rot_mat[0][0] + y * rot_mat[0][1] + from_x,
        x * rot_mat[1][0] + y * rot_mat[1][1] + from_y,
    )

    return output