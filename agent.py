from collections import Counter

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
import shopkeeper
import sites
import posture
from field import NuisanceEncounters
from name_object import Name
from population import Population

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
        self.killer = None
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
        # # Removing the hardcoded towns for now
        # self.site.add_morph(sites.TownBuildingMorph(building.WeaponShop))
        # self.site.add_morph(sites.TownBuildingMorph(building.Inn))
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
            return max((e for e in self.enemy_priority if e.alive), key=self.enemy_priority.get)
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
            self.destroyed = True
            return

    def die(self):
        self.destroyed = True
        self.site.die()


class PopulationAgent(WorldAgent):
    built = False
    rendered = False

    def __init__(self, *args, **kwargs):
        self.is_town_friendly = False
        self.built = False
        self.site = None
        self.rendered = False
        self.actors = []
        self.location_functions = {}
        self.destroyed = False
        super().__init__(*args, **kwargs)

    def cull_absent_actors(self):
        assert self.rendered
        # Filter out dead and absent actors
        self.actors = [a for a in self.actors if a.location is not None]
        for actor in self.actors:
            actor.vanish()
        self.rendered = False

    def get_location(self, actor, region):
        try:
            return self.location_functions[actor](region)
        except KeyError:
            return region.arbitrary_location()

    def refresh(self):
        # Hook for populations to change things up between player visits.
        pass

    def render(self, region):
        if not self.built:
            self.build()
            self.built = True
        if not self.rendered:
            self.refresh()
            self.show(region)
        self.rendered = True

    def allows_other(self, population):
        return False

    def show(self, region):
        for actor in self.actors:
            actor.materialize(self.get_location(actor, region))

    def refresh_population(self):
        self.refresh()

    def die(self):
        print(f"{self.name} were eradicated.")
        self.alive = False
        self.vanish()

    def vanish(self):
        self.change_site(None)
        WorldAgent.vanish(self)

    def change_site(self, site):
        if self.site:
            self.site.remove_population(self)
            self.destroy_fields()
            if self.rendered:
                self.hide_actors()
        self.site = site
        if site is not None:
            site.add_population(self)
            self.create_fields()

    def build(self):
        pass

    def expel(self):
        self.change_site(None)

    def hide_actors(self):
        at_least_one_fighter = False
        for a in self.actors:
            if a.alive and a.awake and getattr(a.ai, "morale_level", "fight") == "fight":
                at_least_one_fighter = True
                break

        if at_least_one_fighter:
            self.cull_absent_actors()
        else:
            # We're about to disband, so calculate whoever did the most damage to our dudes,
            # And give them credit for beating us
            best_attacker_counter = sum((a.damage_log for a in self.actors), Counter())
            best_attacker_list = best_attacker_counter.most_common(1)
            if len(best_attacker_list) != 0:
                attacker, _damage = best_attacker_list[0]
                self.killer = attacker
            self.cull_absent_actors()
            self.die()
            self.destroyed = True


class ShopType:
    def __init__(self, shop_name, shopkeeper_name, building_type):
        self.shop_name = shop_name
        self.shopkeeper_name = shopkeeper_name
        self.building_type = building_type


class ShopkeeperAgent(PopulationAgent):
    morph_type = None
    town = None
    shop_types = [
        ShopType("inn", "innkeeper", building.Inn),
        ShopType("weapon shop", "weaponsmith", building.WeaponShop),
        ShopType("temple", "monk", building.Temple)
    ]

    def shopkeeper_location_function(self, region):
        shop = self.get_building()
        if shop is not None and region.has_location(shop):
            return shop
        else:
            return region.arbitrary_location()

    def __init__(self, *args, shop_type, town, **kwargs):
        super().__init__(*args, **kwargs)
        self.shop_type = shop_type
        self.person = shopkeeper.Person(name=self.name_object)
        self.actors = [self.person]
        self.location_functions[self.person] = self.shopkeeper_location_function
        self.town = town
        self.is_town_friendly = True
        self.building_morph = None

    def get_building(self):
        if self.building_morph is not None and self.building_morph.has_building():
            return self.building_morph.get_building()
        else:
            return None

    @classmethod
    def in_world(cls, world_map):
        shop_type = choice(cls.shop_types)
        return cls(
            name=namemaker.make_name().add(shop_type.shopkeeper_name, "{}, {}"),
            location=world_map,
            coordinates=world_map.random_point(),
            shop_type=shop_type,
            town=None,
        )

    def town_utility(self, town):
        if town.destroyed:
            return -float("inf")
        crowding = len(town.site.populations)+1
        distance = self.location.distance(self, town)
        return -(town.unrest + distance + crowding)

    def find_town(self):
        town_agents = self.location.things_with_trait(
            "town", self.coordinates, 30
        )
        if not town_agents:
            return None
        return max(town_agents, key=self.town_utility)

    def move_towns(self, new_town):
        self.town = new_town
        print(f"{self.name} moved to {self.town.get_name()}")
        self.change_site(self.town.site)
        self.building_morph = sites.TownBuildingMorph(
            self.shop_type.building_type,
            self.person,
        )
        self.town.site.add_morph(
            self.building_morph
        )

    def take_turn(self):
        if self.town is None:
            town = self.find_town()
            if not town:
                print(f"{self.name} gave up on being a {self.shop_type.shopkeeper_name}")
                self.vanish()
            else:
                self.move_towns(town)
            return

        best_town = self.find_town()
        if (
            best_town is not None
            and best_town != self.town
            and self.town_utility(best_town) > self.town_utility(self.town) + 5
        ):
            self.move_towns(best_town)


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

    def create_random_creatures(self, amount=None):
        return []

    def encounter_quantity(self):
        return 3

    def build(self):
        self.actors.extend(self.create_random_creatures())

    def populate_encounter(self, encounter_pocket):
        for actor in self.create_random_creatures(self.encounter_quantity()):
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
        other.view_location()


class BanditGroup(ExternalNuisance):
    member_name = "gang"
    morph_type = sites.BanditHabitation

    def build(self):
        for m in range(self.number_of_members):
            bandit = self.create_bandit()
            self.actors.append(bandit)

    def encounter_quantity(self):
        return max(1, min(5, math.floor(self.power)))

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
    adjectives = [
        "peeling", "thin", "hairy", "spotted", "bloated", "short",
    ]

    def site_preference(self, site):
        # TODO: Better check for this
        if "tomb" in site.get_name():
            return 1
        else:
            return 0

    def create_random_creatures(self, amount=None):
        if amount is None:
            amount = len(self.adjectives)
        shuffle(self.adjectives)
        actors = []
        for adjective in self.adjectives[:amount]:
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

    def create_random_creatures(self, amount=None):
        if amount is None:
            amount = max(7, min(25, int(self.power)))
        out = []
        for _ in range(amount):
            ant = actor.Person(
                location=None,
                name=Name("giant ant")
            )
            ant.damage_type = "sharp"
            ant.damage_mult = 2
            ant.combat_skill = 30
            ant.ai = ai.WanderingMonsterAI(ant)
            out.append(ant)
        return out

    def build(self):
        queen = actor.AntQueen(
            location=None,
            name=Name("giant ant queen")
        )
        self.actors.append(queen)
        self.location_functions[queen] = self.boss_location_function

        for ant in self.create_random_creatures():
            queen.ants.append(ant)
            self.actors.append(ant)

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

    def create_random_creatures(self, amount=None):
        out = []
        if amount is None:
            amount = len(self.adjectives)
            shuffle(self.adjectives)
        for adjective in self.adjectives[:amount]:
            kobold = actor.Humanoid(
                location=None,
                name=Name(adjective) + "kobold"
            )
            kobold.ai = ai.SquadAI(kobold)
            kobold.traits.add("kobold")
            out.append(kobold)
        return out

    def build(self):
        for kobold in self.create_random_creatures():
            self.actors.append(kobold)

        boss = actor.Person(
            location=None,
            name=Name("kobold leader"),
        )
        boss.traits.add("kobold")
        boss.ai = ai.WanderingMonsterAI(boss)
        boss.combat_skill = 75
        sword = game_object.Item(location=boss, name=Name("crude sword"))
        sword.damage_type = "sharp"
        sword.damage_mult = 6
        self.location_functions[boss] = self.boss_location_function
        self.actors.append(boss)

