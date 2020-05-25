import actor
import agent
import building
import direction
import game_object
import location
import name_object
import namemaker
import phrase
import posture
import schedule
import sites
import spells
import wide
from direction import north, south, east, west, up, down
from direction import random as random_direction
from wide import Overworld
import population

day = 1000 * 60 * 60 * 24

def make_player(location, coordinates, landmarks=(), use_web_output=False, postures=()):
    john = actor.Hero(
        location=location,
        name="john",
        coordinates=coordinates
    )
    for p in postures:
        john.learn_posture(p)
    my_parser = john.ai
    my_parser.web_output = use_web_output
    john.view_location()
    john.known_landmarks = set(landmarks)
    # john.spells_known = {spells.Shock, spells.Fireball}
    john.spells_known = set()
    john.body.max_mana = 50
    john.body.mana = 50
    john.money = 20
    sword = game_object.Item(
        location=john,
        name=name_object.Name("iron sword"),
    )
    sword.damage_type = "sharp"
    sword.damage_mult = 6
    phrase.QuitPhrase(my_parser, ["quit"])
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
        self.test_location = location.Location(
            description="Test Overworld",
            sched=self.schedule,
        )
        self.actor = make_player(
            location=self.test_location,
            coordinates=None,
        )


class SiteTest(World):
    def __init__(self, site_type, save_manager=None):
        super().__init__(save_manager)
        self.overworld = Overworld(
            sched=self.schedule,
            width=10,
            height=10,
        )
        self.site = site_type.at_point(
            location=self.overworld,
            coordinates=(5, 5),
            direction=down,
            landmark_name=name_object.Name("test site"),
        )


class PopulationTest(SiteTest):
    def __init__(self, site_type, population_type, save_manager=None):
        super().__init__(site_type, save_manager)
        self.town = agent.Town(
            name=name_object.Name("test town"),
            location=self.overworld,
            coordinates=(5, 6),
        )
        self.population = population_type(
            name=name_object.Name("test population"),
            location=self.overworld,
            coordinates=(5, 5),
            target=self.town,
        )
        # give time for the population to occupy the site
        # (and reveal bugs if they don't)
        self.schedule.run_game(2 * day)


class Random(World):
    def __init__(self, use_web_output=False, save_manager=None):
        super().__init__(save_manager=save_manager)
        self.schedule = schedule.Schedule()
        world_map = wide.Overworld(
            sched=self.schedule,
            width=50,
            height=50,
        )

        world_events = agent.WorldEvents(world_map)

        town_n = 10
        cave_n = 24
        caves = [
            sites.RuneCave.at_point(
                location=world_map,
                coordinates=world_map.random_point(),
                direction=direction.down,
                landmark_name=namemaker.make_name() + "cave"
            )
            for i in range(cave_n)
        ]

        towns = [
            agent.Town(
                name=namemaker.make_name(),
                location=world_map,
                coordinates=world_map.random_point(),
            )
            for i in range(town_n)
        ]

        for i in range(20):
            testing_shopkeeper_agent = agent.ShopkeeperAgent.in_world(world_map)

        self.schedule.run_game(250 * day)

        self.actor = make_player(
            location=world_map,
            postures=(posture.random_posture(),),
            coordinates=world_map.random_point(),
            landmarks=set(town.site.landmark for town in towns),
            use_web_output=use_web_output,
        )

        if self.save_manager:
            phrase.SpecialPhrase(
                callback=self.save,
                parser=self.actor.ai,
                synonyms=["<<save>>"]
            )
        # dude.view_location()
        # world_schedule.run_game()

class Static(World):
    def __init__(self, use_web_output=False, save_manager=None, site_type=sites.Cave):
        super().__init__(save_manager=save_manager)
        self.directions = [north, south, east, west, up, down]

        plains = Overworld(
            description="You stand in a grassy field",
            sched=self.schedule,
        )

        caves_portal = game_object.PortalEdge.free_portal(
            location=plains,
            direction=down,
            coordinates=(15, 14),
            name="slope",
        )
        cave_site = site_type(
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
            description="You are in a very placeholder-like town"
        )
        town_portal = game_object.PortalEdge.free_portal(
            location=plains,
            direction=north,
            coordinates=(25, 10),
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
