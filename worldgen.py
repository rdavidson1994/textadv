from name_object import Name
import schedule, actor, wide, action, namemaker, sites, game_object
import ai
import direction
from world import make_player
from random import random
from population import Population
from abc import ABC


class TestAI(ai.AI):
    def get_local_action(self):
        return action.LongWait(self.actor)


class WorldAgent(actor.Actor):
    rendered = False
    update_period = 20000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai = TestAI(self)
        self.destroyed = False
        self.unrest = 0
        self.update_keyword = "agent update"
        self.set_timer(self.update_period, self.update_keyword)

    def take_turn(self):
        # abstract
        pass

    def hear_timer(self, keyword):
        if keyword == self.update_keyword:
            self.take_turn()
            self.set_timer(self.update_period, self.update_keyword)


class Town(WorldAgent):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site = sites.TownSite.at_point(
            location=self.location,
            direction=direction.random(),
            coordinates=self.coordinates,
            landmark_name=self.name_object+"city",
        )

    def take_turn(self):
        if self.destroyed:
            return

        if random() < 1/100:
            tomb_name = namemaker.make_name()
            print(f"{self.name} built a tomb named {tomb_name.get_text()}")
            tomb = sites.Tomb.at_point(
                world_map,
                direction.random(),
                world_map.random_in_circle(self.coordinates, 5),
                landmark_name=tomb_name+"tomb",
            )
            tomb_roll = random()

            # if tomb_roll<1/3:
            #     tomb.add_morph(sites.KoboldHabitation())
            # elif tomb_roll<2/3:
            #     tomb.add_morph(sites.GhoulHabitation())
            # assert tomb.schedule == self.schedule

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


class PopulationAgent(WorldAgent, Population):
    def __init__(self, *args, **kwargs):
        Population.__init__(self)
        WorldAgent.__init__(self, *args, **kwargs)

    def vanish(self):
        if self.site:
            self.destroy()
        WorldAgent.vanish(self)


class BanditGroup(PopulationAgent):
    # These are meant to be human bandits
    # They are temporarily kobolds until I write better room descriptions
    def __init__(self, *args, target, **kwargs):
        super().__init__(*args, **kwargs)
        self.target = target
        self.power = 5
        self.number_of_members = 5

    def take_turn(self):
        if not self.site:
            candidate_hideouts = self.location.sites(
                center=self.coordinates,
                radius=5,
            )
            for site in candidate_hideouts:
                if site.allows_population(self):
                    self.change_site(site)
                    site.add_morph(sites.KoboldHabitation())
                    site_name = site.landmark.name.get_text()
                    print(f"The kobold group {self.name} took {site_name}")
                    break
        self.power -= 0.2
        if random() < 1/10 and not self.target.destroyed:
            print(f"The kobold group {self.name} raided {self.target.name}")
            self.target.unrest += self.power
            self.power += 10/self.target.unrest
        if self.power <= 0:
            self.vanish()
            print(f"The kobold group {self.name} was disbanded")

    def build_actors(self):
        for m in range(self.number_of_members):
            if random() < 0.5:
                weapon_kind = "sword"
                damage_type = "sharp"
                damage_mult = 2+self.power/10
            else:
                weapon_kind = "mace"
                damage_type = "blunt"
                damage_mult = 3+self.power/10

            title = f"kobold {weapon_kind}sman"
            given_name = namemaker.make_name()
            name_and_title = given_name.add(title, template="{}, {}")

            bandit = actor.SquadActor(
                location=None,
                name=name_and_title
            )
            self.actors.append(bandit)

            weapon = game_object.Item(
                location=bandit,
                name=Name(weapon_kind)
            )
            weapon.damage_type = damage_type
            weapon.damage_mult = damage_mult


if __name__ == "__main__":
    world_schedule = schedule.Schedule()
    world_map = wide.Location(
        sched=world_schedule,
        width=50,
        height=50,
    )
    town_n = 6
    cave_n = 24
    caves = [
        sites.Cave.at_point(
            location=world_map,
            coordinates=world_map.random_point(),
            direction=direction.down,
            landmark_name=namemaker.make_name()+"cave"
        )
        for i in range(cave_n)
    ]


    towns = [
        Town(
            name=namemaker.NameMaker().create_word(),
            location=world_map,
            coordinates=world_map.random_point(),
        )
        for i in range(town_n)
    ]
    world_schedule.run_game(15000000)
    for cave in caves:
        cave.update_region()

    dude = make_player(
        location=world_map,
        coordinates=(15, 15),
        landmarks=set(town.site.landmark for town in towns),
        use_web_output=False,
    )
    # dude.view_location()
    world_schedule.run_game()

