import game_object
import random
import math

# logging.basicConfig(level=logging.DEBUG, format='%(message)s')


class Location(game_object.Location):
    view_distance = 10
    width = 30
    height = 30

    def __init__(self, *args, **kwargs):
        game_object.Location.__init__(self, *args, **kwargs)
        self.traits.add("wide")

    def describe(self, viewer, full_text=True):
        out = super().describe(viewer, full_text)
        out += "\nCoordinates: " + str(viewer.coordinates)
        return out

    def random_point(self):
        return (random.uniform(0, self.width),
                random.uniform(0, self.height),)

    def random_in_circle(self, center, radius):
        (x, y) = center
        assert self.includes_point(x, y)
        depth = 0
        while True:
            depth += 1
            assert depth < 1000
            theta = random.uniform(0, 2*math.pi)
            new_radius = random.uniform(0, radius)
            new_x = math.cos(theta)*new_radius+x
            new_y = math.sin(theta)*new_radius+y
            if self.includes_point(new_x, new_y):
                return new_x, new_y

    def distance(self, first, second):
        x1, y1 = first.get_coordinates(self)
        x2, y2 = second.get_coordinates(self)
        return (x1 - x2) ** 2 + (y1 - y2) ** 2

    def line_of_sight(self, first, second, cutoff=None):
        if cutoff is None:
            cutoff = self.view_distance
        assert (first.has_location(self) and
                second.has_location(self))
        x1, y1 = first.get_coordinates(self)
        x2, y2 = second.get_coordinates(self)
        if (x1 - x2)**2 + (y1 - y2)**2 <= cutoff**2:
            return super().line_of_sight(first, second)

    def includes_point(self, x, y):
        return 0 <= x <= self.width and 0 <= y <= self.height
    

"""
my_schedule = schedule.Schedule()
plains = thing.Location(description="You are standing in field of grass.")
house = thing.Location(description="You are in a house.")
stronghold = thing.Location(description="You are in a stronghold")

sword = thing.Item(location=plains,
                   name="iron longsword",
                   other_names=["sword", "longsword", "iron sword"])
sword.damage_type = "sharp"
sword.damage_mult = 3

key = thing.Item(location=plains,
                 name="key")

hamburger = thing.FoodItem(location=plains,
                           name="hamburger",
                           other_names=["burger"])

door = thing.Portal(locations=[plains, house],
                    name="door",
                    directions=[n, s],
                    locked=False,
                    key=key)

john = actor.Hero(plains, name="john", sched=my_schedule)
my_parser = john.ai
joe = actor.Person(plains, name="joe", sched=my_schedule)
joe.ai = ai.WanderingMonsterAI(joe)

quit_phrase = phrase.QuitPhrase(my_parser, ["quit", "exit"])
inventory_phrase = phrase.InventoryPhrase(my_parser, ["i", "inventory"])
print(john.location.describe(john))
my_schedule.run_game()
"""
