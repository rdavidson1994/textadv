import math
from random import choice, random, shuffle
from typing import List

import action
import agentactions
import actor
import ai
import body
import building
import direction
import dungeonrooms
import errors
import game_object
import namemaker
import population
import shopkeeper
import sites
import posture
from field import NuisanceEncounters
from name_object import Name
from population import Population
from region import TownRegion

day = 1000*60*60*24


def set_choice(in_set):
    try:
        return choice(tuple(in_set))
    except IndexError:
        return None


class WaitingAI(ai.AI):
    def get_local_action(self):
        return action.LongWait(self.actor)


class WorldAgent(actor.Actor):
    rendered = False
    update_period = 1*day

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai = self.create_ai()
        assert self.ai is not None
        self.fields = []
        self.create_fields()
        self.destroyed = False
        self.unrest = 0
        self.update_keyword = "agent update"
        self.set_timer(self.update_period, self.update_keyword)

    def create_ai(self):
        return WaitingAI(self)

    def take_turn(self):
        # abstract
        pass

    def hear_timer(self, keyword):
        if keyword == self.update_keyword:
            self.take_turn()
            self.set_timer(self.update_period, self.update_keyword)

    def create_fields(self):
        pass

    def add_field(self, field):
        self.fields.append(field)

    def destroy_field(self, field):
        assert field in self.fields
        self.fields.remove(field)
        field.destroy()

    def destroy_fields(self):
        for field in self.fields:
            field.destroy()
        self.fields = []


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
        if random() < 1/50:
            ants = GiantAntSwarm.in_world(self.world)
            print(f"{ants.name} surfaced, hungry for food")


class Town(WorldAgent):
    tomb_count = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai = WaitingAI(self)
        self.site = sites.TownSite.at_point(
            location=self.location,
            direction=direction.random(),
            coordinates=self.coordinates,
            landmark_name=self.name_object+"village",
            agent=self,
        )
        for factory in (building.WeaponShop, building.Inn):
            pop = population.ShopPopulation(shopkeeper.Person(), )
            self.site.add_population()
        self.site.add_morph(sites.TownBuildingMorph(building.WeaponShop))
        self.site.add_morph(sites.TownBuildingMorph(building.Inn))
        self.traits.add("town")
        self.enemy_priority = {}
        self.last_attacks = {}

    def suffer_attack(self, unrest, source):
        self.unrest += unrest
        if source in self.enemy_priority:
            self.enemy_priority[source] += unrest
        else:
            self.enemy_priority[source] = unrest
        self.last_attacks[source] = self.schedule.current_time

    def worst_problem(self):
        try:
            return max(self.enemy_priority, key=self.enemy_priority.get)
        except ValueError:
            return None

    def priority(self, agent):
        out = self.enemy_priority.get(agent)
        if out is None:
            out = 0
        return out

    def last_attack(self, agent):
        last = self.last_attacks.get(agent)
        return self.schedule.current_time - last

    def take_turn(self):
        for agent in self.enemy_priority:
            self.enemy_priority[agent] *= 0.9**(self.update_period / day)
        if self.destroyed:
            return

        if random() < 1/200:
            self.tomb_count += 1
            tomb_name = namemaker.make_name()
            print(f"{self.name} built a tomb named {tomb_name.get_text()}")
            sites.Tomb.at_point(
                self.location,
                direction.random(),
                self.location.random_in_circle(self.coordinates, 5),
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
                coordinates=self.location.random_in_circle(
                    self.coordinates, 5),
            )
            print(f"{self.name} spawned {group.name} at unrest {self.unrest:.2f}")

        if self.unrest > 60 + random()*40:
            print(f"{self.name} crumbled to ruin amid starvation and rioting.")
            self.teardown()
            return

    def teardown(self):
        self.destroyed = True



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
            self.destroy_fields()
            if self.population.rendered:
                self.population.hide_actors()
        self.site = site
        if site is not None:
            site.add_population(self.population)
            self.create_fields()

    def build_actors(self, number=None) -> List[actor.Actor]:
        pass


class NuisanceAI(WaitingAI):
    def is_hostile_to(self, other):
        return other != self


class ExternalNuisance(PopulationAgent):
    morph_type = None
    member_name = "group"

    def create_ai(self):
        return NuisanceAI(self)

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

    def encounter_quantity(self):
        return 3

    def populate_encounter(self, encounter_pocket):
        # TODO: un-hardcode the AI
        for actor in self.build_actors(self.encounter_quantity()):
            encounter_pocket.add_actor(actor)
            actor.materialize(encounter_pocket)
            actor.ai = ai.WaitingMonsterAI(actor)

    def site_preference(self, site):
        return 0

    def get_morph(self):
        return self.morph_type()

    def create_fields(self):
        if self.site:
            field = NuisanceEncounters(
                self,
                wide_location=self.location,
                radius=5,  # TODO: Configurable
                center=self.site.landmark.coordinates,
                height=0.09,
            )
            self.add_field(field)

    def own_site_preference(self):
        return -float("inf")

    def create_own_site(self):
        return None

    def find_target(self):
        towns = self.location.things_with_trait(
            "town", self.coordinates, 15
        )
        active_towns = set(t for t in towns if not t.destroyed)
        self.target = set_choice(active_towns)
        if self.target is None:
            print(f"Having no suitable targets, {self.name} disbanded")
            self.vanish()
            return False
        print(f"{self.name} turned their eyes to {self.target.name}")
        self.move_to(self.target)
        if self.site:
            print(f"{self.name} abandoned {self.site.get_name()}")
            self.change_site(None)

    def acquire_site(self):
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
            return False
        else:
            shuffle(candidate_sites)
            site = max(candidate_sites, key=self.site_preference)
            if self.site_preference(site) < self.own_site_preference():
                site = self.create_own_site()
            self.change_site(site)
            if self.wants_to_morph(site):
                site.add_morph(self.get_morph())
            print(f"{self.name} took {site.get_name()}")

    def take_turn(self):
        if self.target is None or self.target.destroyed:
            target_found = self.find_target()
            if not target_found:
                return
        if not self.site:
            site_acquired = self.acquire_site()
            if not site_acquired:
                return

        self.power -= 0.1
        if random() < 1/10 and not self.target.destroyed:
            new_unrest = self.target.unrest + self.power/2
            print(
                f"{self.name} attacked {self.target.get_name()} "
                f"(unrest {self.target.unrest:.2f}->{new_unrest:.2f})"
            )
            self.target.suffer_attack(self.power/2, self)
            self.target.unrest = new_unrest
            self.power += 4/self.target.unrest
        if self.power <= 0:
            self.vanish()
            print(f"{self.name} was disbanded")
            return

    def encounter_actor(self, other):
        self.ai.set_action(agentactions.AmbushActor(self, other), now=True)

    def ambush_actor(self, other):
        encounter_pocket = other.location.create_pocket(other)
        self.populate_encounter(encounter_pocket)
        other.change_location(encounter_pocket)


class BanditGroup(ExternalNuisance):
    member_name = "gang"
    morph_type = sites.BanditHabitation

    def build_actors(self, number=None):
        actors = []
        if number is None:
            number = self.number_of_members
        for m in range(number):
            bandit = self.create_bandit()
            actors.append(bandit)
        return actors

    def encounter_quantity(self):
        return max(2, min(5, math.floor(self.power)))

    def populate_encounter(self, encounter_pocket):
        number_of_bandits = self.encounter_quantity()
        for _ in range(number_of_bandits):
            bandit = self.create_bandit()
            bandit.ai = ai.WaitingMonsterAI(bandit)
            bandit.materialize(encounter_pocket)
            encounter_pocket.add_actor(bandit)

    def create_bandit(self):
        if random() < 0.5:
            weapon_kind = "sword"
            damage_type = "sharp"
            damage_mult = 4 + self.power / 5
            title = "bandit swordsman"
        else:
            weapon_kind = "mace"
            damage_type = "blunt"
            damage_mult = 4 + self.power / 5
            title = "bandit maceman"
        given_name = namemaker.make_name()
        name_and_title = given_name.add(title, template="{}, {}")
        bandit = actor.Humanoid(
            location=None,
            name=name_and_title
        )
        bandit.ai = ai.SquadAI(bandit)
        # TODO: Replace this with selection from a world-level posture list
        stance = posture.random_posture(posture.Stance)
        guard = posture.random_posture(posture.Guard)
        for p in (stance, guard):
            bandit.learn_posture(p)
            bandit.adopt_posture(p)


        weapon = game_object.Item(
            location=bandit,
            name=Name(weapon_kind)
        )
        weapon.damage_type = damage_type
        weapon.damage_mult = damage_mult
        return bandit


class GhoulHorde(ExternalNuisance):
    member_name = "ghouls"
    morph_type = sites.GhoulHabitation

    def site_preference(self, site):
        # TODO: Better check for this
        if "tomb" in site.get_name():
            return 1
        else:
            return 0

    def build_actors(self, number=None):
        adjectives = [
            "peeling", "thin", "hairy", "spotted", "bloated", "short",
        ]
        if number is None:
            number = len(adjectives)
            shuffle(adjectives)
        actors = []
        for adjective in adjectives[:number]:
            ghoul = actor.Person(name=Name(adjective + " ghoul"))
            ai.WanderingMonsterAI(ghoul)
            ghoul.body = body.UndeadBody(ghoul)
            ghoul.combat_skill = 60
            actors.append(ghoul)
        return actors


class GiantAntSwarm(ExternalNuisance):
    member_name = "ants"

    def create_own_site(self):
        coordinates = self.location.random_in_circle(
            center=self.coordinates, radius=5
        )
        return sites.Hive.at_point(
            location=self.location,
            coordinates=coordinates,
            direction=direction.down,
            landmark_name=self.name+"'s hive"
        )

    def site_preference(self, site):
        distance = self.location.distance(self, site.landmark.coordinates)
        return 10 - distance

    def own_site_preference(self):
        return 7.5

    def wants_to_morph(self, site):
        return False

    @staticmethod
    def boss_location_function(region):
        try:
            return region.room_with_type(
                room_type=dungeonrooms.QueenApartment,
                randomize=True
            )
        except errors.MissingNode:
            return region.arbitrary_location()

    def build_actors(self, number=None):
        # TODO: Link enemy number to power
        actors = []
        queen = None
        if number is None:
            number = 7
            queen = actor.AntQueen(
                location=None,
                name=Name("giant ant queen")
            )
            actors.append(queen)
            self.population.location_functions[queen] = self.boss_location_function

        for _ in range(number):
            ant = actor.Person(
                location=None,
                name=Name("giant ant")
            )
            ant.damage_type = "sharp"
            ant.damage_mult = 2
            ant.combat_skill = 30
            ant.ai = ai.WanderingMonsterAI(ant)
            actors.append(ant)
            if queen:
                queen.ants.append(ant)
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
            return region.arbitrary_location()

    def build_actors(self, number=None):
        # TODO: Refactor all "number != None" branches into a "make_actor" branch
        actors = []
        if number is None:
            number = len(self.adjectives)
            shuffle(self.adjectives)
        for adjective in self.adjectives[:number]:
            kobold = actor.Humanoid(
                location=None,
                name=Name(adjective) + "kobold"
            )
            kobold.ai = ai.SquadAI(kobold)
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
