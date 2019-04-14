from name_object import Name
import schedule, actor, wide, action, namemaker
import sites, game_object, body, dungeonrooms, errors
import ai
import direction
from world import make_player
from random import random, choice, shuffle
from population import Population
from typing import List


day = 1000*60*60*24


def set_choice(in_set):
    try:
        return choice(tuple(in_set))
    except IndexError:
        return None


class TestAI(ai.AI):
    def get_local_action(self):
        return action.LongWait(self.actor)


class WorldAgent(actor.Actor):
    rendered = False
    update_period = 1*day

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


class WorldEvents(WorldAgent):
    def __init__(self, world_map):
        super().__init__(sched=world_map.schedule)
        self.world = world_map

    def take_turn(self):
        if random() < 1/100:
            ghouls = GhoulHorde.in_world(self.world)
            print(f"{ghouls.name} appeared")
        if random() < 1/75:
            kobolds = KoboldGroup.in_world(self.world)
            print(f"{kobolds.name} emerged from underground")


class Town(WorldAgent):
    tomb_count = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site = sites.TownSite.at_point(
            location=self.location,
            direction=direction.random(),
            coordinates=self.coordinates,
            landmark_name=self.name_object+"city",
        )
        self.traits.add("town")

    def take_turn(self):
        if self.destroyed:
            return

        if random() < 1/200:
            self.tomb_count += 1
            tomb_name = namemaker.make_name()
            print(f"{self.name} built a tomb named {tomb_name.get_text()}")
            tomb = sites.Tomb.at_point(
                world_map,
                direction.random(),
                world_map.random_in_circle(self.coordinates, 5),
                landmark_name=tomb_name+"tomb",
            )

        if random() < 1/1000:
            self.unrest += 20
            print(f"{self.name} suffered a plague")

        roll = random()
        if roll < 1/10:
            # print(f"{self.name} had a good harvest")
            if self.unrest > 10:
                self.unrest -= 10
            else:
                self.unrest = 0

        elif roll > 9/10:
            self.unrest += 3
            # print(f"{self.name} had a bad harvest")

        if random() < (self.unrest/100)**2:
            group = BanditGroup(
                name=namemaker.make_name()+"gang",
                target=self,
                location=self.location,
                coordinates=world_map.random_in_circle(self.coordinates, 5),
            )
            print(f"{self.name} spawned {group.name} @ unrest {self.unrest}")

        if self.unrest > 60 + random()*40:
            print(f"{self.name} crumbled to ruin amid starvation and rioting.")
            self.destroyed = True
            return


class SubordinatePopulation(Population):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent

    def build_actors(self):
        self.actors = self.agent.build_actors()

    def hide_actors(self):
        super().hide_actors()
        if all(not actor.alive for actor in self.actors):
            self.agent.die()


class PopulationAgent(WorldAgent):
    site = None
    population = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.population = SubordinatePopulation(self)

    def die(self):
        print(f"{self.name} were eradicated.")
        self.vanish()

    def vanish(self):
        self.change_site(None)
        WorldAgent.vanish(self)

    def change_site(self, site):
        if self.site:
            self.site.remove_population(self.population)
            if self.population.rendered:
                self.population.hide_actors()
        if site:
            site.add_population(self.population)
        self.site = site

    def build_actors(self) -> List[actor.Actor]:
        pass


class ExternalNuisance(PopulationAgent):
    morph_type = None
    member_name = "group"

    def __init__(self, *args, target, **kwargs):
        super().__init__(*args, **kwargs)
        self.target = target
        self.power = 5
        self.number_of_members = 5

    @classmethod
    def in_world(cls, world_map):
        return cls(
            name=namemaker.make_name()+cls.member_name,
            location=world_map,
            coordinates=world_map.random_point(),
            target=None,
        )

    def wants_to_morph(self, site):
        return not site.has_morph_type(self.morph_type)

    def site_preference(self, site):
        return 0

    def get_morph(self):
        return self.morph_type()

    def take_turn(self):
        if self.target is None or self.target.destroyed:
            towns = self.location.things_with_trait(
                "town", self.coordinates, 15
            )
            active_towns = set(t for t in towns if not t.destroyed)
            self.target = set_choice(active_towns)
            if self.target is None:
                print(f"Having no suitable targets, {self.name} disbanded")
                self.vanish()
                return
            print(f"{self.name} turned their eyes to {self.target.name}")
            self.move_to(self.target)
            if self.site:
                print(f"{self.name} abandoned {self.site.get_name()}")
                self.change_site(None)
        if not self.site:
            nearby_sites = self.location.sites(
                center=self.coordinates,
                radius=10,
            )
            candidate_sites = [
                site for site in nearby_sites if site.allows_population(self)
            ]
            if not candidate_sites:
                print(f"Finding no suitable home, {self.name} disbanded")
                self.vanish()
                return
            else:
                shuffle(candidate_sites)
                site = max(candidate_sites, key=self.site_preference)
                self.change_site(site)
                if self.wants_to_morph(site):
                    site.add_morph(self.get_morph())
                print(f"{self.name} took {site.get_name()}")

        self.power -= 0.1
        if random() < 1/10 and not self.target.destroyed:
            print(f"{self.name} attacked {self.target.get_name()}")
            self.target.unrest += self.power/2
            self.power += 4/self.target.unrest
        if self.power <= 0:
            self.vanish()
            print(f"{self.name} was disbanded")
            return


class BanditGroup(ExternalNuisance):
    member_name = "gang"
    morph_type = sites.BanditHabitation

    def build_actors(self):
        actors = []
        for m in range(self.number_of_members):
            if random() < 0.5:
                weapon_kind = "sword"
                damage_type = "sharp"
                damage_mult = 4+self.power/5
                title = "bandit swordsman"
            else:
                weapon_kind = "mace"
                damage_type = "blunt"
                damage_mult = 4+self.power/5
                title = "bandit maceman"

            given_name = namemaker.make_name()
            name_and_title = given_name.add(title, template="{}, {}")

            bandit = actor.SquadActor(
                location=None,
                name=name_and_title
            )
            actors.append(bandit)

            weapon = game_object.Item(
                location=bandit,
                name=Name(weapon_kind)
            )
            weapon.damage_type = damage_type
            weapon.damage_mult = damage_mult

        return actors


class GhoulHorde(ExternalNuisance):
    member_name = "ghouls"
    morph_type = sites.GhoulHabitation

    def site_preference(self, site):
        # TODO: Better check for this
        if "tomb" in site.get_name():
            return 1
        else:
            return 0

    def build_actors(self):
        adjectives = [
            "peeling", "thin", "hairy", "spotted", "bloated", "short",
        ]
        actors = []
        for adjective in adjectives:
            ghoul = actor.Person(name=Name(adjective + " ghoul"))
            ai.WanderingMonsterAI(ghoul)
            ghoul.body = body.UndeadBody(ghoul)
            ghoul.combat_skill = 60
            actors.append(ghoul)
        return actors


class KoboldGroup(ExternalNuisance):
    member_name = "kobolds"
    adjectives = [
        "skinny", "tall", "hairy", "filthy", "pale", "short",
    ]

    morph_type = sites.KoboldHabitation

    @staticmethod
    def boss_location_function(region):
        try:
            return region.room_with_type(
                room_type=dungeonrooms.BossQuarters,
                randomize=True
            )
        except errors.MissingNode:
            return region.random_location(exclude_entrance=True)

    def build_actors(self):
        actors = []
        for adjective in self.adjectives:
            kobold = actor.SquadActor(
                location=None,
                name=Name(adjective) + "kobold"
            )
            kobold.traits.add("kobold")
            actors.append(kobold)

        boss = actor.Person(
            location=None,
            name=Name("kobold leader"),
        )
        boss.traits.add("kobold")

        actors.append(boss)
        boss.ai = ai.WanderingMonsterAI(boss)
        boss.combat_skill = 75
        sword = game_object.Item(location=boss, name=Name("crude sword"))
        sword.damage_type = "sharp"
        sword.damage_mult = 6
        self.population.location_functions[boss] = self.boss_location_function
        return actors


if __name__ == "__main__":
    world_schedule = schedule.Schedule()
    world_map = wide.Location(
        sched=world_schedule,
        width=50,
        height=50,
    )
    WorldEvents(world_map)
    town_n = 10
    cave_n = 24
    caves = [
        sites.RuneCave.at_point(
            location=world_map,
            coordinates=world_map.random_point(),
            direction=direction.down,
            landmark_name=namemaker.make_name()+"cave"
        )
        for i in range(cave_n)
    ]

    towns = [
        Town(
            name=namemaker.make_name(),
            location=world_map,
            coordinates=world_map.random_point(),
        )
        for i in range(town_n)
    ]
    world_schedule.run_game(250*day)

    dude = make_player(
        location=world_map,
        coordinates=world_map.random_point(),
        landmarks=set(town.site.landmark for town in towns),
        use_web_output=False,
    )
    # dude.view_location()
    world_schedule.run_game()

