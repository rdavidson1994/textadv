from game_object import Item, Thing, FoodItem, Cage, PortalEdge, Landmark
from location import Location
from name_object import Name
from actor import Prisoner
from namemaker import NameMaker
from random import choice
import logging
from action import Eat
from errors import NotEnoughNodes, MissingNode
import runes
from actor import Person
from ai import WanderingMonsterAI
import parsetemplate
# logging.basicConfig(level=logging.DEBUG,format='%(message)s')
debug = logging.debug


class Preference:
    def __repr__(self):
        return self.__class__.__name__

    def refined_list(self, candidate_list):
        pass


class ExitNumber(Preference):
    def __repr__(self):
        return super().__repr__() + str(self.desired_exit_numbers)

    def __init__(self, number):
        self.desired_exit_numbers = (number,)

    def refined_list(self, candidate_list):
        return [node for node in candidate_list
                if len(node.connected_nodes) in self.desired_exit_numbers]


class NotVertex(ExitNumber):
    def __init__(self):
        super().__init__(0)
        self.desired_exit_numbers = (2, 3, 4,)


class DesiredNeighbor(Preference):
    avoid = False

    def __repr__(self):
        return super().__repr__() + "({})".format(self.desired_neighbor.__name__)

    def __init__(self, desired_neighbor):
        self.desired_neighbor = desired_neighbor

    def refined_list(self, candidate_list):
        return [node for node in candidate_list if
                node.has_neighbor_type(self.desired_neighbor) ^ self.avoid]


class AvoidNeighbor(DesiredNeighbor):
    avoid = True


class MaximizeFunction(Preference):

    def profit(self, node):
        raise NotImplementedError

    def refined_list(self, candidate_list):
        best = max(candidate_list, key=self.profit)
        return [candidate for candidate in candidate_list
                if self.profit(candidate) == self.profit(best)]


class AvoidRoom(MaximizeFunction):
    def __init__(self, avoided_room):
        self.avoided_room = avoided_room

    def profit(self, node):
        try:
            return node.distance_from_type(self.avoided_room)
        except MissingNode:
            return 0


class AvoidEntrance(MaximizeFunction):
    def profit(self, node):
        return node.distance_from_entrance()


class ReplaceRoomType(MaximizeFunction):
    def __init__(self, replaced_type, avoid=False):
        self.replaced_type = replaced_type
        self.avoid = avoid

    def profit(self, node):
        if isinstance(node.location, self.replaced_type):
            if self.avoid:
                return -1
            else:
                return 1
        else:
            return 0


class GeneratedRoom(Location):
    description_file = "room_descriptions.txt"
    preference_list = []
    basic_items = []
    basic_things = []
    is_rally = False

    def __repr__(self):
        return self.__class__.__name__

    def __init__(self, *args, basis_location=None, **kwargs):
        Location.__init__(self, *args, **kwargs)
        self.decor_dict = {}
        self.map_node = None
        self.newer_location = None
        self.basis_location = basis_location
        if basis_location:
            basis_location.add_newer_location(self)
            self.map_node = basis_location.map_node
            movers = list(basis_location.things)
            for thing in movers:
                thing.change_location(self, keep_arranged = True)
            self.decor_dict = dict(basis_location.decor_dict)

        self.generate_items()

    def is_entrance(self):
        # TODO: Implement "RoomMorph"s, instead of overwriting locations
        if self.basis_location:
            return self.basis_location.is_entrance()
        else:
            return False

    def add_newer_location(self, newer_location):
        assert self.newer_location is None
        self.newer_location = newer_location
        
    def evaluate_token(self, token):
        # This is a placeholder - rewrite to use dicts
        if self.newer_location:
            out = self.newer_location.evaluate_token(token)
        elif self.has_furnishing(token):
            out = getattr(self, token, True)
        else:
            out = False
        return out

    def get_description(self, viewer=None):
        if self.basis_location:
            basis_desc = self.basis_location.get_description(viewer)
        else:
            basis_desc = ""

        # parser = parsetemplate.RoomTemplateParser(
        #     self, newer_room=self.newer_location
        # )

        parser = parsetemplate.ParserManager.get_parser(
            self.description_file,
            self.__class__.__name__,
        )

        own_desc = parser.full_parse()

        if basis_desc:
            return basis_desc + "\n" + own_desc
        else:
            return own_desc

    @classmethod
    def choose_node(cls, region):
        debug(region.get_text_map())
        candidate_list = region.unbuilt_nodes
        debug("This is the starting candidate_list: {}".format(candidate_list))
        if not candidate_list:
            debug("Out of room for {}, but these rooms built:".format(cls))
            debug([i.location for i in region.node_list])
            raise NotEnoughNodes
        debug("must choose a node from a list this long:{}".format(len(candidate_list)))
        for preference in cls.preference_list:
            # debug(candidate_list)
            refined_list = preference.refined_list(candidate_list)
            if refined_list:
                candidate_list = refined_list
                debug(f"this is the next candidate_list {candidate_list} for {cls}")
            else:
                debug(f"unable to satisfy {preference} for {cls.__name__}")
        debug([node.coords for node in candidate_list])
        chosen_node = choice(candidate_list)
        return chosen_node

    def generate_items(self):
        for item_name in self.basic_items:
            self.decor_dict[item_name] = Item(location=self, name=item_name)
        for thing_name in self.basic_things:
            self.decor_dict[thing_name] = Thing(location=self, name=thing_name)


class Entrance(GeneratedRoom):
    map_letter = "En"
    preference_list = [ExitNumber(1), ]

    def is_entrance(self):
        return True

    def generate_items(self):
        entrance = self.reg.entrance_portal
        if entrance:
            entrance.change_location(self)
        super().generate_items()


class CaveEntrance(Entrance):
    def build_portals(self):
        for connection in self.map_node.connections:
            connection.build_portal(name="cave mouth")


class KoboldCaveEntrance(Entrance):
    preference_list = (ReplaceRoomType(Entrance),)

    def generate_items(self):
        super().generate_items()
        Item(
            location=self,
            name=Name("animal skulls", "animal skull skulls")
        )
        Item(
            location=self,
            name=Name("animal hides")
        )


class RuneChamber(GeneratedRoom):
    map_letter = "Rn"
    def generate_items(self):
        runes.Rune(
            location=self,
            name=Name("runes", "rune runes")
        )


class CaveFiller(GeneratedRoom):
    map_letter = "##"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.adjective = choice(["narrow", "wide", "low", "tall", ])
        self.noun = "room"

    def get_description(self, viewer=None):
        if self.newer_location is not None:
            return ""
        case = len(self.map_node.connected_nodes)
        if case == 1:
            self.noun = "chamber"
        elif case == 2:
            self.noun = "passage"
        else:
            self.noun = "branching passage"
        return "This {} {} is devoid of furnishings".format(self.adjective,
                                                            self.noun)


class TreasureRoom(GeneratedRoom):
    is_rally = True
    map_letter = "Tr"
    preference_list = [ExitNumber(1),
                       AvoidEntrance(), ]

    def generate_items(self):
        d = self.decor_dict
        d["bones"] = Item(location=self, name="bones")
        d["chest"] = Item(location=self, name="chest")
        d["chest"].price = 1500
        d["pedestal"] = Thing(location=self, name="pedestal")


class Barracks(GeneratedRoom):
    map_letter = "Ba"
    preference_list = [NotVertex(),
                       AvoidNeighbor(CaveEntrance)]

    def generate_items(self):
        d = self.decor_dict
        d["beds"] = Thing(location=self, name="bed", othernames=["beds"])


class BossQuarters(GeneratedRoom):
    map_letter = "LQ"
    preference_list = [ExitNumber(1),
                       DesiredNeighbor(Barracks),
                       AvoidEntrance(), ]

    def generate_items(self):
        # self.reg.make_boss(location=self)
        d = self.decor_dict
        d["bed"] = Thing(
            location=self,
            names=["wooden bed", "bed"],
        )
        d["curtains"] = Item(
            location=self,
            names=["bead curtains", "curtains"],
        )


class HealthPotion(FoodItem):
    def be_targeted(self, act):
        if isinstance(act, Eat):
            act.actor.reset_body()
            act.actor.receive_text_message("You feel brand new.")
            return True, ""
        else:
            return super().be_targeted(act)


class Apothecary(GeneratedRoom):
    map_letter = "Ap"

    def generate_items(self):
        d = self.decor_dict
        d["potion"] = HealthPotion(location=self, name="potion")
        d["pots"] = Item(location=self, names=["pots", "ingredients",
                                               "pot", "ingredient", ])


class Kitchen(GeneratedRoom):
    map_letter = "Ki"
    preference_list = [NotVertex()]

    def generate_items(self):
        d = self.decor_dict
        d["meat"] = Item(location=self, names=["meat", "meats"])
        knife = Item(location=self, names=["cleaver", "knife"])
        knife.damage_mult = 6
        knife.damage_type = "sharp"
        d["knife"] = knife


class BanditKitchen(Kitchen):
    basic_items = ["crates", "rations"]


class MessHall(GeneratedRoom):
    map_letter = "MH"
    preference_list = [DesiredNeighbor(Kitchen),
                       NotVertex()]

    def generate_items(self):
        d = self.decor_dict
        d["table"] = Thing(location=self, names=["table"])
        d["scraps"] = Item(location=self, names=["scraps", "debris"])


class BanditMess(MessHall):
    preference_list = [DesiredNeighbor(BanditKitchen)]

    def generate_items(self):
        d = self.decor_dict
        d["table"] = Thing(self, "table")
        d["crate"] = Thing(self, Name("stool", "stool crate cushion bag"))


class BanditBarracks(Barracks):
    def generate_items(self):
        d = self.decor_dict
        d["bedroll"] = Thing(self, "bedroll")
        d["lamp"] = Item(self, Name("lamp", "lamp lantern"))


class Prison(GeneratedRoom):
    map_letter = "Pr"
    preference_list = [AvoidEntrance()]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cage = None

    def generate_items(self):
        key = Item(location=self, name="key")
        self.cage = Cage(location=self,
                         names=["cage", "iron cage", "padlock", "lock"],
                         key=key, )
        self.decor_dict["cage"] = self.cage
        self.cage.locked = True
        prisoner = Prisoner(name=NameMaker().create_word(),
                            location=self,
                            sched=self.schedule)
        self.cage.add_prisoner(prisoner)

    def evaluate_token(self, token):
        if token == "locked":
            return self.cage.is_locked()
        else:
            return super().evaluate_token(token)


class TombEntrance(Entrance):        
    def build_portals(self):
        for connection in self.map_node.connections:
            connection.build_portal(name="passageway")


class TombSanctum(GeneratedRoom):
    map_letter = "To"
    preference_list = [ExitNumber(1), AvoidEntrance()]
    basic_things = ["coffin"]
    basic_items = ["painting"]


class Crypt(GeneratedRoom):
    map_letter = "Cr"
    preference_list = [AvoidEntrance()]
    basic_items = ["bones"]


class MeatChamber(GeneratedRoom):
    is_rally = True
    map_letter = "Go"
    basic_things = ["corpses"]
    preference_list = [AvoidEntrance(), NotVertex(), DesiredNeighbor(Crypt)]


class OfferingRoom(GeneratedRoom):
    map_letter = "Of"
    preference_list = [NotVertex(),
                       DesiredNeighbor(TombEntrance),
                       DesiredNeighbor(TombSanctum)]
    basic_items = ["candles"]


class Temple(GeneratedRoom):
    map_letter = "Ch"
    preference_list = [DesiredNeighbor(Crypt), DesiredNeighbor(TombSanctum)]
    basic_things = ["pews", "windows"]
