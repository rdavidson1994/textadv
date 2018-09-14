import os
from itertools import groupby
import phrase
import parsing
import game_object
import actor
import action
import game_object
import schedule
import ai
from direction import n,s,e,w,u,d
#logging.basicConfig(level=logging.DEBUG, format='%(message)s')

my_schedule = schedule.Schedule()
plains = game_object.Location(description="You are standing in field of grass.")
house = game_object.Location(description="You are in a house.")
stronghold = game_object.Location(description="You are in a stronghold")

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
                          directions=[n, s],
                          locked=False,
                          key=key)

john = actor.Hero(plains, name="john", sched=my_schedule)
my_parser = john.ai
joe = actor.Actor(plains, name="joe", sched=my_schedule)
joe.ai = ai.WanderingMonsterAI(joe)

quit_phrase = phrase.QuitPhrase(my_parser, ["quit", "exit"])
inventory_phrase = phrase.InventoryPhrase(my_parser, ["i", "inventory"])
print(john.location.describe(john))
my_schedule.run_game()
