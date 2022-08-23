'''
Based on an implementation from https://scipython.com/blog/quadtrees-2-implementation-in-python/
'''

import numpy as np

class Point:
    def __init__(self, x, y, data=None):
        self.x, self.y = x,y
        self.data = data

    def __repr__(self):
        return '{}: {}'.format((self.x, self.y), repr(self.data))
    def __str__(self) -> str:
        return 'Point ({:.2f}, {:.2f})'.format(self.x, self.y)

    def distance_from(self, target):
        try:
            target_x, target_y = target.x, target.y
        except AttributeError:
            target_x, target_y = target
        
        return np.hypot(self.x - target_x, self.y - target_y)

class Rect:
    def __init__(self, center_x, center_y, width, height):
        self.center_x, self.center_y = center_x, center_y
        self.width, self.height = width, height

        self.north_edge = center_y - height/2
        self.south_edge = center_y + height/2
        self.west_edge = center_x - width/2
        self.east_edge = center_x + width/2

    def __repr__(self):
        return str((self.north_edge, self.east_edge, self.south_edge, self.west_edge))

    def __str__(self):
        return '({:.2f}, {:.2f}, {:.2f}, {:.2f})'.format(
            self.north_edge, self.east_edge, self.south_edge, self.west_edge)

    def contains(self, point):
        try:
            point_x, point_y = point.x, point.y
        except AttributeError:
            point_x, point_y = point

        return (
            point_x >= self.west_edge and
            point_x < self.east_edge and
            point_y >= self.north_edge and
            point_y < self.south_edge
        )
    
    def intersects(self, other:"Rect"):
        return not (
            other.west_edge > self.east_edge or
            other.east_edge < self.west_edge or
            other.north_edge > self.south_edge or
            other.south_edge < self.north_edge
        )

class QuadTree:
    def __init__(self, boundary:Rect, max_points=4, depth=0):
        self.boundary = boundary
        self.max_points = max_points
        self.points = []
        self.depth = depth

        self.subdivided = False

    def __str__(self):
        spacer = ' ' * self.depth * 2
        output = str(self.boundary) + '\n'
        output += spacer + ', '.join(str(point) for point in self.points)

        if not self.subdivided:
            return output
        
        return output + '\n' + '\n'.join([
            spacer + 'nw: ' + str(self.nw),
            spacer + 'ne: ' + str(self.ne),
            spacer + 'se: ' + str(self.se),
            spacer + 'sw: ' + str(self.sw)
        ])

    def __len__(self):
        count = len(self.points)
        if self.subdivided:
            count += len(self.nw) + len(self.ne) + len(self.se) + len(self.sw)
        return count

    def subdivide(self):
        cx, cy = self.boundary.center_x, self.boundary.center_y
        w, h = self.boundary.width/2, self.boundary.height/2

        self.nw = QuadTree(Rect(cx - w/2, cy - h/2, w, h),
                                    self.max_points, self.depth + 1)
        self.ne = QuadTree(Rect(cx + w/2, cy - h/2, w, h),
                                    self.max_points, self.depth + 1)
        self.se = QuadTree(Rect(cx + w/2, cy + h/2, w, h),
                                    self.max_points, self.depth + 1)
        self.sw = QuadTree(Rect(cx - w/2, cy + h/2, w, h),
                                    self.max_points, self.depth + 1)
        self.subdivided = True

    def insert(self, point):
        if not self.boundary.contains(point):
            return False
        if len(self.points) < self.max_points:
            self.points.append(point)
            return True
        
        if not self.subdivided:
            self.subdivided()

        return (
            self.ne.insert(point) or
            self.nw.insert(point) or
            self.se.insert(point) or
            self.sw.insert(point)
            )

    def query(self, boundary, found_points):
        if not self.boundary.intersects(boundary):
            return False
        
        for point in self.points:
            if boundary.contains(point):
                found_points.append(point)
        
        if self.subdivided:
            self.nw.query(boundary, found_points)
            self.ne.query(boundary, found_points)
            self.se.query(boundary, found_points)
            self.sw.query(boundary, found_points)
        
        return found_points