from random import random, randint, sample, shuffle, choice

import location
from direction import north, south, east, west
import spells
from name_object import Name
from vector import Vector
import dungeonrooms
import logging
# these below imports are for testing
import schedule
import actor
import phrase

debug = logging.debug
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

directions = [north, south, east, west]


class InfiniteDeck:
    def __init__(self, lst):
        self.lst = lst

    def __iter__(self):
        return self

    def __next__(self):
        if self.lst:
            return dungeonrooms.choice(self.lst)
        else:
            raise StopIteration


direction_vector = {
    'n': Vector((0, 1)),
    's': Vector((0, -1)),
    'e': Vector((1, 0)),
    'w': Vector((-1, 0)),
}


class CreaturePolicy:
    adjectives = ["skinny", "tall", "hairy",
                  "filthy", "pale", "short", ]
    enemy_type = None
    enemy_name = ""

    def __init__(self, sched=None):
        self.schedule = sched
        self.adjectives = list(self.adjectives)
        shuffle(self.adjectives)

    def get_adjective(self):
        return self.adjectives.pop()

    def get_creature(self, location=None):
        adjective = self.get_adjective()
        name = Name(adjective)+self.enemy_name
        return self.enemy_type(location, name=name, sched=self.schedule)


class Region:
    def __init__(self, sched=None, entrance_portal=None):
        self.node_list = []
        self.connection_list = []
        self.unbred_nodes = []
        self.inhabitants = set()
        self.schedule = sched
        self.entrance_portal = entrance_portal

    def _bounds(self):
        """returns xmin, xmax, ymin, ymax"""

        def x(n):
            return n.coords[0]

        def y(n):
            return n.coords[1]

        x_bounds = [
            min(self.node_list, key=x),
            max(self.node_list, key=x),
        ]

        y_bounds = [
            min(self.node_list, key=y),
            max(self.node_list, key=y),
        ]
        return (
            x_bounds[0].coords[0], x_bounds[1].coords[0],
            y_bounds[0].coords[1], y_bounds[1].coords[1],
        )

    def get_text_map(self, viewer=None, full_size=False):
        """returns a matrix A[y][x] of characters"""
        x_min, x_max, y_min, y_max = self._bounds()
        i_max = 2 * (x_max - x_min)
        j_max = 2 * (y_max - y_min)
        grid = [["  " for i in range(i_max + 1)] for j in range(j_max + 1)]

        # for row in grid:
        #    debug(row)
        def coords_to_indices(coords):
            x, y = coords
            return int(2 * (x - x_min)), int(2 * (y - y_min))
        if viewer:
            visited_locations = viewer.ai.visited_locations
        else:
            visited_locations = []
            # All of the following code not use visited_locations,
        for node in self.node_list:
            try:
                map_letter = node.location.map_letter
            except AttributeError:
                map_letter = "##"
            i, j = coords_to_indices(node.coords)
            if viewer is None:
                if node.coords == (0, 0) and map_letter == "##":
                    grid[j][i] = "Or"
                else:
                    grid[j][i] = map_letter
            elif node.location == viewer.location:
                grid[j][i] = "@ "
            elif node.location not in visited_locations:
                grid[j][i] = "  "
            else:
                grid[j][i] = map_letter
        for c in self.connection_list:
            i, j = coords_to_indices(c.coords)
            if (
                    viewer is not None and
                    c.portal.source.location not in visited_locations
                    and c.portal.target.location not in visited_locations
            ):
                grid[j][i] = "  "
            elif c.is_vertical():
                grid[j][i] = "| "
            elif c.is_horizontal():
                grid[j][i] = "--"
            else:
                grid[j][i] = "xx"
        outlines = ["".join(row) for row in grid]
        out = "\n".join(outlines[::-1])
        try:
            if viewer.ai.web_output:
                return out.replace(" ", "&nbsp;")
        except AttributeError:
            pass
        return out

    def _nodes_with_type(self, room_type):
        return [
            node for node in self.node_list
            if isinstance(node.location, room_type)
        ]

    def node_with_type(self, room_type, randomize=False):
        candidates = self._nodes_with_type(room_type)
        if not candidates:
            raise dungeonrooms.MissingNode
        if randomize:
            return choice(candidates)
        else:
            return candidates[0]

    def room_with_type(self, room_type, randomize=False):
        return self.node_with_type(room_type, randomize).location

    def register_node(self, node):
        self.node_list.append(node)
        self.unbred_nodes.append(node)

    def register_connection(self, connection):
        self.connection_list.append(connection)

    def connection_with_endpoints(self, start, end):
        candidates = [c for c in self.connection_list
                      if (c.start == start and c.end == end)
                      or (c.end == start and c.start == end)]
        assert len(candidates) <= 1
        try:
            return candidates[0]
        except IndexError:
            return None

    def build_blank_locations(self):
        for index, node in enumerate(self.node_list):
            if node.location is None:
                loc = location.Location(description="Place {}".format(index))
                node.set_location(loc)

    def build_portals(self):
        for node in self.node_list:
            try:
                node_build_portals = node.location.build_portals
            except AttributeError as err:
                pass
            else:
                node_build_portals()
        self.build_blank_portals()

    def build_blank_portals(self):
        assert len(self.connection_list) == len(set(self.connection_list))
        for c in self.connection_list:
            if c.portal is None:
                c.build_portal()

    def nodes_with_connections(self, number):
        return [node for node in self.node_list
                if len(node.connected_directions) == number]

    def get_vertices(self):
        return self.nodes_with_connections(1)

    def get_hallways(self):
        return self.nodes_with_connections(2)

    def get_forks(self):
        return self.nodes_with_connections(3) + self.nodes_with_connections(4)

    def node_with_vector(self, vec):
        candidates = [n for n in self.node_list
                      if n.vector.coords == vec.coords]
        assert len(candidates) <= 1
        try:
            return candidates[0]
        except IndexError:
            return None

    def location_a_star(self, start, goal):
        start_node = start.map_node
        goal_node = goal.map_node
        return self.a_star(start_node, goal_node)

    def a_star(self, start, goal):
        assert start, goal in self.node_list
        open_set = set()  # nodes on "to do list"
        closed_set = set()  # set of nodes ruled out
        current = start  # node currently under consideration
        g, h, parent = {}, {}, {}  # dictionaries for storing node properties
        # g = current fastest path from from start to node
        # h = manhattan distance from node to goal
        # start --- g --- current ~~~ h ~~~ goal
        open_set.add(current)  # add current node to the to do list.
        while open_set:  # until no nodes are on to do list,
            # move to the "most promising" node on to do list (minimal h + g)
            current = min(open_set, key=lambda x: g.get(x, 0) + h.get(x, 0))
            if current == goal:  # if you've reached the goal,
                path = []  # begin retracing your steps
                while parent.get(current, None):
                    path.append(current)  # by recursively adding parents
                    current = parent.get(current, None)
                return path
            open_set.remove(current)
            closed_set.add(current)
            for node in current.connected_nodes:
                if node in closed_set:
                    # ignore eliminated nodes
                    continue
                if node in open_set:
                    # when new path to open node found, update the g score.
                    new_g = g.get(current, 0) + 1
                    if g.get(node, 0) > new_g:
                        g[node] = new_g
                        parent[node] = current
                else:
                    # add brand new nodes to the to do list.
                    g[node] = g.get(current, 0) + 1
                    h[node] = node.manhattan(goal)
                    parent[node] = current
                    open_set.add(node)
        else:
            raise ValueError("No path found")

    def portal_with_endpoints(self, start, end):
        connect = self.connection_with_endpoints(start, end)
        for vertex in connect.portal.vertices:
            if vertex.location == start.location:
                return vertex
        else:
            raise Exception

    def path_to_goal(self, start, goal):
        path = self.a_star(start, goal)
        current = start
        portals = []
        while path:
            nxt = path.pop()
            portal = self.portal_with_endpoints(current, nxt)
            portals.append(portal)
            current = nxt
        return portals

    def path_to_location(self, start_location, goal_location):
        goal = goal_location.map_node
        start = start_location.map_node
        if goal is None or start is None:
            raise AttributeError
        return self.path_to_goal(start, goal)

    def get_rally_node(self):
        raise NotImplementedError

    def path_to_rally(self, start):
        goal = self.get_rally_node()
        return self.path_to_goal(start, goal)

    def get_entrance_node(self):
        for node in self.node_list:
            try:
                if node.location.is_entrance():
                    return node
            except AttributeError:
                continue
        else:
            raise Exception # All regions must have an entrance

    def path_to_entrance(self, start):
        goal = self.get_entrance_node()
        return self.path_to_goal(start, goal)

    def path_to_random(self, start):
        goal = dungeonrooms.choice(self.node_list)
        return self.path_to_goal(start, goal)


class Caves(Region):
    enemy_number = 0
    enemy_adjectives = []
    essential_rooms = ()
    optional_rooms = ()
    filler_rooms = ()
    breed_count = 0
    boss_policy = CreaturePolicy()
    enemy_policy = CreaturePolicy()

    def __init__(self, *args, **kwargs):
        self.unbuilt_nodes = []
        n = 0
        while n < 100:
            n += 1
            super().__init__(*args, **kwargs)
            vec = Vector((0, 0))
            self.origin = Node(self, vec)
            self.breed_repeatedly(self.breed_count)
            if (len(self.node_list) >= len(self.essential_rooms)
                    and len(self.get_forks()) >= 2
                    and len(self.get_vertices()) >= 4):
                dungeonrooms.debug('n={}'.format(n))
                break
            else:
                dungeonrooms.debug("rejected the following map:")
                dungeonrooms.debug(self.get_text_map())
        else:
            raise Exception  # I generated 100 maps, and none worked.
        self.build_locations(
            essential=self.essential_rooms,
            optional=self.optional_rooms,
            filler=self.filler_rooms,
        )
        self.build_portals()
        # self.create_inhabitants()

    def make_boss(self, *args, **kwargs):
        return self.boss_policy.get_creature(*args, **kwargs)

    def make_enemy(self, *args, **kwargs):
        return self.enemy_policy.get_creature(*args, **kwargs)

    def breed_repeatedly(self, n):
        for i in range(0, n):
            self.breed_random_node()

    def breed_random_node(self):
        try:
            node = dungeonrooms.choice(self.unbred_nodes)
        except IndexError:
            pass
        else:
            self.unbred_nodes.remove(node)
            node.breed()

    def build_room(self, room_type, node):
        assert self.unbuilt_nodes != []
        self.unbuilt_nodes.remove(node)
        new_location = room_type(sched=self.schedule,
                                 reg=self,
                                 basis_location=node.location, )
        if node.location:
            pass
        node.set_location(new_location)

    def get_rally_node(self):
        for node in self.node_list:
            if node.location.is_rally:
                return node
        else:
            return self.origin

    def get_rally_location(self):
        return self.get_rally_node().location

    def build_locations(self, essential=None, optional=None, filler=None):
        self.unbuilt_nodes = list(self.node_list)
        # self.unbuilt_nodes = [n for n in self.node_list if not n.is_entrance()]
        essential_deck = list(essential)
        optional_deck = list(optional)
        filler_deck = InfiniteDeck(filler)
        shuffle(optional_deck)
        # the essential deck does not get shuffled
        for deck in (essential_deck, optional_deck, filler_deck):
            for room_type in deck:
                try:
                    chosen_node = room_type.choose_node(self)
                except dungeonrooms.NotEnoughNodes:
                    dungeonrooms.debug(
                        "Out of nodes. Ending optional room creation."
                    )
                    break
                self.build_room(room_type, chosen_node)
        self.build_blank_locations()

    def create_inhabitants(self):
        # assert len(self.enemy_adjectives) >= self.enemy_number
        shuffle(self.enemy_adjectives)
        for i in range(self.enemy_number):
            while True:
                node = dungeonrooms.choice(self.node_list)
                if not isinstance(node.location, dungeonrooms.Entrance):
                    break
            loc = node.location
            # adjective = self.enemy_adjectives[i]
            inhabitant = self.make_enemy(loc)
            self.inhabitants.add(inhabitant)

    def arbitrary_location(self):
        # Finds an arbitrary "good" place for a person/thing to show up
        candidates = [
            node for node in self.node_list if not node.location.is_entrance()
        ]
        result_node = choice(candidates)
        return result_node.location


class EmptyCaves(Caves):
    breed_count = 4
    essential_rooms = (dungeonrooms.CaveEntrance,)
    optional_rooms = ()
    filler_rooms = (dungeonrooms.CaveFiller,)


class RuneCave(EmptyCaves):
    essential_rooms = (dungeonrooms.CaveEntrance, dungeonrooms.RuneChamber)


# class KoboldCaves(Caves):
#     essential_rooms = (CaveEntrance, TreasureRoom, Barracks, Kitchen)
#     optional_rooms = (MessHall, Prison, Apothecary, BossQuarters)
#     filler_rooms = (CaveFiller,)
#     breed_count = 4
#     enemy_number = 6
#     enemy_adjectives = ["skinny", "tall", "hairy",
#                         "filthy", "pale", "short", ]
#
#     def make_enemy(self, location=None, adjective=""):
#         name = LegacyName(adjective, "kobold")
#         return actor.SquadActor(location, name=name, sched=self.schedule)
#
#     def make_boss(self, location=None):
#         boss = actor.Person(location=location,
#                            names=["kobold leader", "leader", "kobold"],
#                            sched=self.schedule)
#         boss.combat_skill = 75
#         boss.ai = ai.WanderingMonsterAI(boss)
#         spear = Item(location=boss, name=LegacyName(["crude"],["sword"]))
#         spear.damage_type = "sharp"
#         spear.damage_mult = 3
#         return boss


class EmptyTomb(Caves):
    essential_rooms = (
        dungeonrooms.TombEntrance,
        dungeonrooms.Crypt,
    )
    optional_rooms = (
        dungeonrooms.OfferingRoom,
        dungeonrooms.Temple,
        dungeonrooms.TombSanctum,
    )
    filler_rooms = (dungeonrooms.CaveFiller,)
    breed_count = 2


# class GhoulTomb(Caves):
#     essential_rooms = (TombEntrance, Crypt)
#     optional_rooms = (MeatChamber, OfferingRoom, Temple, TombSanctum)
#     filler_rooms = (CaveFiller,)
#     enemy_number = 4
#     enemy_adjectives = KoboldCaves.enemy_adjectives
#     breed_count = 2
#
#     def make_enemy(self, location=None, adjective=""):
#         name = LegacyName(adjective, "ghoul")
#         ghoul = actor.Person(location, name=name, sched=self.schedule)
#         ai.WanderingMonsterAI(ghoul)
#         ghoul.body = body.UndeadBody(ghoul)
#         ghoul.combat_skill = 60
#         return ghoul
    

class Connection:
    def __init__(self, region, start, end, direction):
        self.region = region
        self.portal = None
        region.register_connection(self)
        self.start = start
        self.end = end
        start.connected_nodes.append(end)
        start.connections.append(self)
        end.connected_nodes.append(start)
        end.connections.append(self)
        self.direction = direction
        start.connected_directions.append(direction)
        end.connected_directions.append(direction.opposite)
        double_vec = self.start.vector + self.end.vector
        self.coords = tuple(coord / 2 for coord in double_vec.coords)

    def locations(self):
        return [self.start.location, self.end.location]

    def directions(self):
        return [self.direction.opposite, self.direction]

    def is_vertical(self):
        return self.coords[0].is_integer()

    def is_horizontal(self):
        return self.coords[1].is_integer()

    def build_portal(self, name="doorway", portal_type=dungeonrooms.PortalEdge):
        if not self.portal:
            self.portal = portal_type(locations=self.locations(),
                                      directions=self.directions(),
                                      name=name, )


class Node:
    number_of_nodes = 0

    def __init__(self, region, vector, parent=None, travel_d=None):
        self.location = None
        self.vector = vector
        self.coords = vector.coords
        self.region = region
        self.connected_directions = []
        self.connected_nodes = []
        self.connections = []
        region.register_node(self)
        if parent is not None:
            Connection(self.region, parent, self, travel_d)

    def set_location(self, loc):
        self.location = loc
        loc.map_node = self

    def distance(self, other_node):
        return len(self.region.a_star(self, other_node))

    def manhattan(self, other_node):
        x = self.coords
        y = other_node.coords
        return abs(x[0] - y[0]) + abs(x[1] - y[1])

    def distance_from_type(self, room_type):
        try:
            other_node = self.region.node_with_type(room_type)
        except IndexError:
            distance = 0  # zero distance, if there's no match
        else:
            distance = self.distance(other_node)
        return distance

    def distance_from_entrance(self):
        entrance = self.region.get_entrance_node()
        return self.distance(entrance)

    def is_entrance(self):
        if self.location:
            return self.location.is_entrance()
        else:
            return False

    def has_neighbor_type(self, room_type):
        for node in self.connected_nodes:
            if isinstance(node.location, room_type):
                return True
        return False

    def breed(self):
        needed_exits = randint(1, 3)
        outgoing_directions = sample(directions, needed_exits)
        for d in outgoing_directions:
            if d in self.connected_directions:
                pass
            target_vector = self.vector + direction_vector[d.letter]
            found_node = self.region.node_with_vector(target_vector)
            if found_node:
                found_con = self.region.connection_with_endpoints(
                    self, found_node
                )
                if found_con is None and random() < 0.5:
                    Connection(self.region, self, found_node, d)
            else:
                Node(self.region, target_vector, self, d)


def a_star_test():
    prison = reg.node_with_type(dungeonrooms.Prison)
    entrance = reg.node_with_type(dungeonrooms.CaveEntrance)
    return reg.a_star(prison, entrance)


# path = a_star_test()
def prison_test():
    # Usage: prisoner, key, cage = prison_test()
    prison = [node.location
              for node in reg.node_list
              if isinstance(node.location, dungeonrooms.Prison)][0]
    john.change_location(prison)
    watches = [
        list(prison.things_with_name(name))[0]
        for name in ("prisoner", "key", "cage")
    ]
    return watches

# prison_test()


if __name__ == "__main__":
    origin = Vector((0, 0))
    my_schedule = schedule.Schedule()
    reg = Caves(sched=my_schedule)
    coords = [node.vector.coords for node in reg.node_list]
    con_sum_vects = [con.start.vector + con.end.vector
                     for con in reg.connection_list]
    con_coords = [(vec.coords[0] / 2, vec.coords[1] / 2) for vec in con_sum_vects]
    vert_cons = [c for c in con_coords if c[0].is_integer()]
    hori_cons = [c for c in con_coords if c[1].is_integer()]
    """
    plt.scatter(*zip(*coords),color="blue", s=750, marker="s")
    plt.scatter(*zip(*vert_cons),color="blue",marker="|",s=500)
    plt.scatter(*zip(*hori_cons),color="blue",marker="_",s=500)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()
    """
    # debug([node.vector.coords for node in reg.node_list])
    # debug([con.direction.letter for con in reg.connection_list])
    vertices = reg.get_vertices()
    # debug([node.vector.coords for node in vertices])
    start_location = reg.node_with_type(dungeonrooms.CaveEntrance).location
    monsters = []
    for st in ["skinny", "tall", "hairy", "filthy", "pale", "short"]:
        while True:
            node = dungeonrooms.choice(reg.node_list)
            if not isinstance(node.location, dungeonrooms.CaveEntrance):
                break
        loc = node.location
        name = dungeonrooms.Name(st)+"kobold"
        zom = actor.SquadActor(loc,
                               name=name,
                               sched=my_schedule, )
        monsters.append(zom)
    debug(reg.get_text_map())
    john = actor.Hero(start_location, name="john", sched=my_schedule)
    john.change_location(start_location)
    john.view_location()
    john.ai.visited_locations = {john.location}
    john.known_landmarks = {john.location.landmark1,
                            john.location.landmark2, }
    john.spells_known = {spells.Shock, spells.Sleep, spells.Fireball}
    john.body.mana = 50
    john.body.max_mana = 50
    sword = dungeonrooms.Item(location=john,
                              name=dungeonrooms.Name("iron sword"),)
    sword.damage_type = "sharp"
    sword.damage_mult = 6
    my_parser = john.ai
    quit_phrase = phrase.QuitPhrase(my_parser, ["quit", "exit"])
    inventory_phrase = phrase.InventoryPhrase(my_parser, ["i", "inventory"])
    my_schedule.run_game()
    debug("Scheduled events:")
    for e in my_schedule.event_list[::-1]:
        debug("{}:{}@t={}".format(e.actor, e.action, e.time))
    debug("Hero damage:")
    debug(john.body.damage)
    debug("Monster damage:")
    debug([(m.name, m.body.damage) for m in my_schedule.actors])
