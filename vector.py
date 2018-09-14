from math import sqrt


class Vector:
    def __init__(self, coords):
        self.coords = coords

    def __add__(self, other_vector):
        x = self.coords
        y = other_vector.coords
        new_coords = tuple(x[i] + y[i] for i in range(len(x)))
        return Vector(new_coords)

    def norm(self):
        x,y = self.coords
        return sqrt(x**2 + y**2)
