import actor
import building
import game_object
import location
import name_object
import phrase
import schedule
import sites
import spells
from direction import north, south, east, west, up, down
from wide import Location
import population


def make_player(location, coordinates, landmarks=set(), use_web_output=False):
    john = actor.Hero(
        location=location,
        name="john",
        coordinates=coordinates
    )
    my_parser = john.ai
    my_parser.web_output = use_web_output
    john.view_location()
    john.known_landmarks = set(landmarks)
    # john.spells_known = {spells.Shock, spells.Fireball}
    john.spells_known = set()
    john.body.max_mana = 50
    john.body.mana = 50
    sword = game_object.Item(
        location=john,
        name=name_object.Name("iron sword"),
    )
    sword.damage_type = "sharp"
    sword.damage_mult = 3
    phrase.QuitPhrase(my_parser, ["quit", "exit"])
    phrase.InventoryPhrase(my_parser, ["i", "inventory"])
    return john


class World:
    def __init__(self, save_manager=None):
        self.save_manager = save_manager
        self.schedule = schedule.Schedule()

    def save(self):
        return self.save_manager.save(self)

    def run_game(self, duration=None):
        self.schedule.run_game(duration)


class ActorTest(World):
    def __init__(self):
        super().__init__()
        self.test_location = Location(
            description="Test Location",
            sched=self.schedule
        )
        self.actor = make_player(
            location=self.test_location,
            coordinates=None,
        )



class Static(World):
    def __init__(self, use_web_output=False, save_manager=None):
        super().__init__(save_manager=save_manager)
        self.directions = [north, south, east, west, up, down]

        plains = Location(
            description="You stand in a grassy field",
            sched=self.schedule,
        )

        caves_portal = game_object.PortalEdge.free_portal(
            location=plains,
            direction=down,
            coordinates=(15, 14),
            name="slope",
        )
        cave_site = sites.Cave(
            sched=self.schedule,
            entrance_portal=caves_portal.target
        )
        cave_site.add_morph(sites.KoboldHabitation())
        cave_site.add_population(population.Kobold())
        # cave_site.add_morph(sites.GhoulHabitation())
        cave_site.update_region()
        caves_name = name_object.Name("kobold caves")
        caves_landmark = caves_portal.source.create_landmark(name=caves_name)

        town = location.Location(
            name="town",
            description ="You are in a very placeholder-like town"
        )
        town_portal = game_object.PortalEdge.free_portal(
            location=plains,
            direction=north,
            coordinates=(25,10),
            name="gate"
        )
        town_portal.set_target_location(town)
        town_name = name_object.Name("big town")
        building.WeaponShop(town, sched=self.schedule)
        town_landmark = town_portal.source.create_landmark(name=town_name)
        landmarks = {caves_landmark, town_landmark}
        john = make_player(plains, (15, 15), landmarks, use_web_output)
        if self.save_manager:
            phrase.SpecialPhrase(
                callback=self.save,
                parser=john.ai,
                synonyms=["<<save>>"]
            )

