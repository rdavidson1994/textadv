import os
from itertools import groupby

import location
import phrase
import parsing
import game_object
import actor
import action
import game_object
import schedule
import ai
from direction import north,south,east,west,up,down
#logging.basicConfig(level=logging.DEBUG, format='%(message)s')

my_schedule = schedule.Schedule()
plains = location.Location(description="You are standing in field of grass.")
house = location.Location(description="You are in a house.")
stronghold = location.Location(description="You are in a stronghold")

sword = game_object.Item(location=plains,
                         name="iron longsword",
                         other_names=["sword", "longsword", "iron sword"])
sword.damage_type = "sharp"
sword.damage_mult = 3

key = game_object.Item(location=plains,
                       name="key")

hamburger = game_object.FoodItem(location=plains,
                                 name="hamburger",
                                 other_names=["burger"])

door = game_object.Portal(locations=[plains, house],
                          name="door",
                          directions=[north, south],
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
