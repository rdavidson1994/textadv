from random import choice

class Direction:
    def __init__(self, name, letter, vector=None, opposite=None):
        self.vector = vector
        self.letter = letter
        self.name = name
        if opposite is not None:
            self.opposite = opposite
            opposite.opposite = self

    def __eq__(self, other):
        try:
            if self.name == other.name:
                return True
            else:
                return False
        except AttributeError:
            return False

    def __str__(self):
        return self.name

north = Direction("north", "n", (0, 1))
south = Direction("south", "s", (0, -1), opposite=north)
east = Direction("east", "e", (1, 0))
west = Direction("west", "w", (-1, 0), opposite=east)
up = Direction("up", "u")
down = Direction("down", "d", opposite=up)

cardinal_directions = [north, south, east, west]
direction_list = [north, south, east, west, up, down]


def random(up_and_down=False):
    if up_and_down:
        return choice(direction_list)
    else:
        return choice(cardinal_directions)


letter_dict = {direct.letter: direct for direct in direction_list}
name_dict = {direct.name: direct for direct in direction_list}
# The good way: full_dict = {**letter_dict, **name_dict}
# This crappy implementation is for compatibility with the old python at work.
full_dict = {}
for i in letter_dict.keys():
    full_dict[i] = letter_dict[i]
for i in name_dict.keys():
    full_dict[i] = name_dict[i]
