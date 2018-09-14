class Direction:
    def __init__(self, name, letter, vector=None, opposite=None):
        self.vector = vector
        self.letter = letter
        self.name = name
        if opposite is not None:
            self.opposite = opposite
            opposite.opposite = self

    def __str__(self):
        return self.name


n = Direction("north", "n", (0,1))
s = Direction("south", "s", (0,-1), opposite=n)
e = Direction("east", "e", (1,0))
w = Direction("west", "w", (-1,0), opposite=e)
u = Direction("up", "u")
d = Direction("down", "d", opposite=u)
direction_list = [n, s, e, w, u, d]
letter_dict = {direct.letter: direct for direct in direction_list}
name_dict = {direct.name: direct for direct in direction_list}
# The good way: full_dict = {**letter_dict, **name_dict}
# This crappy implementation is for compatibility with the old python at work.
full_dict = {}
for i in letter_dict.keys():
    full_dict[i] = letter_dict[i]
for i in name_dict.keys():
    full_dict[i] = name_dict[i]
