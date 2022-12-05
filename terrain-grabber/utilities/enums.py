"""
Author: Patt Martin
Email: pmartin@unca.edu or MaddHatt.pm@gmail.com
Written: 2022
"""

from enum import Enum

class CoordMode(Enum):
    normalized = 0,
    pixel = 1,
    earth = 2

class ToolMode(Enum):
    area = 0,
    tree = 1,
    overlays = 2

class CornerID(Enum):
    NW = 0,
    NE = 1,
    SE = 2,
    SW = 3,

def CornerID_to_name(corner: CornerID):
    if corner is CornerID.NW: return 'NW'
    if corner is CornerID.NE: return 'NE'
    if corner is CornerID.SE: return 'SE'
    if corner is CornerID.SW: return 'SW'