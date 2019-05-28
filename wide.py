import direction
import game_object
import random
import math
import encounter
from string import ascii_lowercase
from collections import Counter

# logging.basicConfig(level=logging.DEBUG, format='%(message)s')
import location


class Overworld(location.Location):
    view_distance = 10

    def __init__(self, *args, width=30, height=30, **kwargs):
        location.Location.__init__(self, *args, **kwargs)
        self.encounter_fields = []
        self.width = width
        self.height = height
        self.traits.add("wide")

    def describe(self, viewer, full_text=True):
        out = super().describe(viewer, full_text)
        x, y = viewer.coordinates
        out += f"\nCoordinates: ({x:.1f},{y:.1f})"
        return out

    def things_with_trait(self, trait, center=None, radius=None):
        candidates = super().things_with_trait(trait)
        if center is not None and radius is not None:
            out = set(
                x for x in candidates
                if self.distance(x, center) < radius
            )
        else:
            out = candidates
        return out

    def sites(self, center=None, radius=None):
        # If you specify a center/radius, you must specify both
        return set(
            portal.edge.site for portal
            in self.things_with_trait("portal", center, radius)
            if portal.edge.site is not None
        )

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

    def displacement(self, first, second):
        try:
            a = first.get_coordinates(self)
        except AttributeError:
            a = first
        try:
            b = second.get_coordinates(self)
        except AttributeError:
            b = second
        return b[0]-a[0], b[1]-a[1]

    def distance(self, first, second):
        displacement = self.displacement(first, second)
        return math.sqrt(sum(x**2 for x in displacement))

    def create_pocket(self, actor):
        assert actor.has_location(self)
        pocket = encounter.EncounterPocket(
            sched=self.schedule,
            description="You are in a pocket dimension for a random encounter"
        )
        exit_direction = direction.random(up_and_down=False)
        encounter.PocketExit(
            encounter_pocket=pocket,
            locations=(pocket, self),
            directions=(exit_direction, exit_direction.opposite),
            coordinate_pairs=(None, actor.coordinates),
            name_pair=("exit", "entrance")
        )
        return pocket

    def compass_direction(self, first, second):
        x, y = self.displacement(first, second)
        angle = math.atan2(y, x)
        if angle < 0:
            angle += 2*math.pi
        directions = ["e", "ne", "n", "nw", "w", "sw", "s", "se", ]

        petal_width = (2 * math.pi) / len(directions)
        if angle > 2*math.pi - petal_width/2:
            return directions[0]
        else:
            adjusted_angle = angle + petal_width/2
            index = math.floor(adjusted_angle / petal_width)
            return directions[index]

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

    def add_encounter_field(self, field):
        self.encounter_fields.append(field)

    def remove_encounter_field(self, field):
        self.encounter_fields.remove(field)

    def generate_encounters(self, actor):
        assert self.has_thing(actor)
        x, y = actor.coordinates
        random.shuffle(self.encounter_fields)
        for field in self.encounter_fields:
            if (
                field.targets_actor(actor)
                and random.random() < field.probability(actor, x, y)
            ):
                field.affect_actor(actor)
                break

    def broadcast_announcement(self, action):
        out = super().broadcast_announcement(action)
        if getattr(action, "travels_overland", False):
            self.generate_encounters(action.actor)
        return out

    def get_text_map(
        self,
        viewer=None,
        full_size=False,
        stride_x=1.0,
        stride_y=1.0,
        radius=10,
    ):
        # By default, we map each 1.0x1.0 chunk of land to two characters
        if viewer is None:
            return "No map is available"
        count_x = int(self.width / stride_x)
        count_y = int(self.height / stride_y)

        def character(x, y):
            on_vertical = (x % int(5 / stride_x) == 0)
            on_horizontal = (y % int(5 / stride_y) == 0)
            if on_vertical and on_horizontal:
                return "+-"
            elif on_vertical:
                return "| "
            elif on_horizontal:
                return "--"
            else:
                return "  "

        def set_grid(grid, coordinates, value):
            x_index, y_index = indexes_from_coords(coordinates)
            grid[y_index][x_index] = value

        def indexes_from_coords(coordinates):
            x_index = int(coordinates[0] / stride_x)
            y_index = int(coordinates[1] / stride_y)
            return x_index, y_index

        full_grid = [
                [character(x, y) for x in range(count_x)]
                for y in range(count_y)
            ]

        legend_entries = []
        used_symbols = set()
        for landmark in viewer.known_landmarks:
            if full_size or self.distance(viewer, landmark.coordinates) < radius:
                name = landmark.get_name(viewer)
                symbol = name[0:2]
                disambiguation_count = 1
                while symbol in used_symbols and disambiguation_count < 9:
                    disambiguation_count += 1
                    symbol = symbol[0]+str(disambiguation_count)
                used_symbols.add(symbol)
                legend_entries.append(f"{symbol}: {name}")
                set_grid(full_grid, landmark.coordinates, symbol)

        if viewer.has_location(self) and viewer.coordinates is not None:
            set_grid(full_grid, viewer.coordinates, "@ ")
            legend_entries.append("@: You")

        if full_size:
            shown_grid = full_grid
        else:
            viewer_x, viewer_y = indexes_from_coords(viewer.coordinates)
            shown_grid = [
                [
                    full_grid[y][x]
                    for x in range(count_x)
                    if abs(x-viewer_x) < radius / stride_x
                ]
                for y in range(count_y)
                if abs(y-viewer_y) < radius / stride_y
            ]

        map_lines = ["".join(row) for row in shown_grid]
        map_string = "\n".join(map_lines[::-1])

        legend_string = "\n".join(legend_entries)
        return "\n".join((map_string, legend_string))


"""
my_schedule = schedule.Schedule()
plains = thing.Overworld(description="You are standing in field of grass.")
house = thing.Overworld(description="You are in a house.")
stronghold = thing.Overworld(description="You are in a stronghold")

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
