import name_object
import schedule, actor, wide, action, namemaker, sites
import ai
import direction
from name_object import Name
from random import random


class TestAI(ai.AI):
    def get_local_action(self):
        return action.LongWait(self.actor)


class WorldAgent(actor.Actor):
    update_period = 20000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai = TestAI(self)
        self.destroyed = False
        self.unrest = 0
        self.set_timer(self.update_period, "agent update")

    def take_turn(self):
        # abstract
        pass

    def hear_timer(self, keyword):
        if keyword == "agent update":
            self.take_turn()
            self.set_timer(self.update_period, "agent update")


class Town(WorldAgent):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site = sites.TownSite.at_point(
            location=self.location,
            direction=direction.random(),
            coordinates=self.coordinates,
            landmark_name=name_object.Templated(
                a=("city",),
                template="{} city",
                base_name=self.name_object,
            ),
        )

    def take_turn(self):
        if self.destroyed:
            return

        if random() < 1/100:
            tomb_name = namemaker.make_name()
            print(f"{self.name} built a tomb named {tomb_name}")
            tomb = sites.Tomb.at_point(
                world_map,
                direction.random(),
                world_map.random_in_circle(self.coordinates, 5),
                landmark_name=Name(tomb_name, "tomb"),
            )
            tomb_roll = random()
            if tomb_roll<1/3:
                tomb.add_morph(sites.KoboldHabitation())
            elif tomb_roll<2/3:
                tomb.add_morph(sites.GhoulHabitation())
            assert tomb.schedule == self.schedule

        if random() < 1/1000:
            self.unrest += 20
            print(f"{self.name} suffered a plague")

        roll = random()
        if roll < 1/10:
            print(f"{self.name} had a good harvest")
            if self.unrest > 10:
                self.unrest -= 10
            else:
                self.unrest = 0

        elif roll > 9/10:
            self.unrest += 3
            print(f"{self.name} had a bad harvest")

        if random() < (self.unrest/100)**2:
            print(f"{self.name} spawned a bandit group @ unrest {self.unrest}")
            BanditGroup(
                name=namemaker.NameMaker().create_word(),
                target=self,
                location=self.location,
                coordinates=world_map.random_in_circle(self.coordinates, 5),
            )

        if self.unrest > 40 + random()*40:
            print(f"{self.name} crumbled to ruin amid starvation and rioting.")
            self.destroyed = True
            return


class BanditGroup(WorldAgent):
    def __init__(self, *args, target, **kwargs):
        super().__init__(*args, **kwargs)
        self.target = target
        self.power = 5
        self.destroyed = False

    def take_turn(self):
        if self.destroyed:
            return
        self.power -= 0.2
        if random() < 1/10 and not self.target.destroyed:
            print(f"The bandit group {self.name} raided {self.target.name}")
            self.target.unrest += self.power
            self.power += 10/self.target.unrest
        if self.power <= 0:
            self.destroyed = True
            print(f"The bandit group {self.name} was disbanded")


world_schedule = schedule.Schedule()
world_map = wide.Location(sched=world_schedule)

if __name__ == "__main__":
    town_n = 6
    cave_n = 5
    caves = [
        sites.Cave.at_point(
            location=world_map,
            coordinates=world_map.random_point(),
            direction=direction.down,
            landmark_name=f"cave{i}"
        ).add_morph(sites.KoboldHabitation())
        for i in range(cave_n)
    ]

    for i in range(town_n):
        agent = Town(
            name=namemaker.NameMaker().create_word(),
            location=world_map,
            coordinates=world_map.random_point(),
        )
    world_schedule.run_game(15000000)
    for cave in caves:
        cave.update_region()

    dude = actor.Hero(
        location=world_map,
        name="dude",
        sched=world_schedule,
        coordinates=(15, 15)
    )
    dude.known_landmarks |= {cave.landmark for cave in caves}
    dude.view_location()
    world_schedule.run_game()

