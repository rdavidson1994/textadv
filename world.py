import actor
import building
import game_object
import phrase
import schedule
import sites
import spells
from direction import n, s, e, w, u, d
from wide import Location


class World:

    def __init__(self, use_web_output = False, save_manager=None):
        self.directions = [n,s,e,w,u,d]
        self.save_manager = save_manager

        plains = Location(description="You stand in a grassy field")

        my_schedule = schedule.Schedule()
        caves_portal = game_object.PortalEdge.free_portal(
            location=plains,
            direction=d,
            coordinates=(15,14),
            name="ladder"
        )
        cave_site = sites.Cave(sched=my_schedule,
                               entrance_portal=caves_portal.target)
        cave_site.add_morph(sites.KoboldHabitation())
        cave_site.update_region()
        caves_name = game_object.Name(a="kobold", n=["cave", "caves"])
        caves_landmark = caves_portal.source.create_landmark(name=caves_name)

        town = game_object.Location(
            name="town",
            description ="You are in a very placeholde-like town"
        )
        town_portal = game_object.PortalEdge.free_portal(
            location=plains,
            direction=n,
            coordinates=(25,10),
            name="gate"
        )
        town_portal.set_target_location(town)
        town_name = game_object.Name("big", "town")
        building.WeaponShop(town, sched=my_schedule)
        town_landmark = town_portal.source.create_landmark(name=town_name)
        john = actor.Hero(
            plains,
            name="john",
            sched=my_schedule,
            coordinates=(15, 15)
        )
        my_parser = john.ai
        my_parser.web_output = use_web_output
        john.view_location()
        john.known_landmarks = {town_landmark, caves_landmark}
        john.spells_known = {spells.Shock, spells.Fireball}
        john.body.max_mana = 50
        john.body.mana = 50
        sword = game_object.Item(
            location=john,
            name=game_object.Name(
                a=["iron", "long"],
                n=["longsword", "sword"]
            ),
        )
        sword.damage_type = "sharp"
        sword.damage_mult = 3
        phrase.QuitPhrase(my_parser, ["quit", "exit"])
        phrase.InventoryPhrase(my_parser, ["i", "inventory"])
        if self.save_manager:
            phrase.SpecialPhrase(
                callback=self.save,
                parser=my_parser,
                synonyms=["<<save>>"]
            )

        self.schedule = my_schedule

    def save(self):
        return self.save_manager.save(self)

    def run_game(self, duration=None):
        self.schedule.run_game(duration)
