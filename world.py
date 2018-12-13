import game_object
import phrase
import sys
from direction import n, s, e, w, u, d
import spells
import actor
import schedule
import building
import sites
from wide import Location
use_web_output = ("web" in sys.argv)

plains = Location(description="You stand in a grassy field")

my_schedule = schedule.Schedule()
caves_portal = game_object.PortalEdge.free_portal(location=plains,
                                                  direction=d,
                                                  coordinates=(15,14),
                                                  name="ladder")
cave_site = sites.Cave(sched=my_schedule, entrance_portal=caves_portal.target)
cave_site.add_morph(sites.KoboldHabitation())
cave_site.update_region()
caves_reg = cave_site.region
caves_name = game_object.Name(a="kobold", n=["cave", "caves"])
caves_landmark = caves_portal.source.create_landmark(name=caves_name)

town = game_object.Location(description ="You are in a very placeholdery town")
town_portal = game_object.PortalEdge.free_portal(location=plains,
                                                 direction=n,
                                                 coordinates=(25,10),
                                                 name="gate")
town_portal.set_target_location(town)
town_name = game_object.Name("big", "town")
weapon_shop = building.WeaponShop(town, sched=my_schedule)
town_landmark = town_portal.source.create_landmark(name=town_name)

john = actor.Hero(plains, name="john", sched=my_schedule, coordinates=(15, 15))
my_parser = john.ai
my_parser.web_output = use_web_output
john.view_location()
john.known_landmarks = {town_landmark, caves_landmark}
john.spells_known = {spells.Shock, spells.Fireball}
john.body.max_mana = 50
john.body.mana = 50
sword = game_object.Item(location=john,
                         name=game_object.Name(a=["iron", "long"],
                                               n=["longsword", "sword"]),
                         )
sword.damage_type = "sharp"
sword.damage_mult = 3
quit_phrase = phrase.QuitPhrase(my_parser, ["quit", "exit"])
inventory_phrase = phrase.InventoryPhrase(my_parser, ["i", "inventory"])
my_schedule.run_game()