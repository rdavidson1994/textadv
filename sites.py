import region
import game_object
import actor
import ai
import body
from name_object import Name
from typing import Optional
from dungeonrooms import (
    TreasureRoom, Barracks, Kitchen, MeatChamber, MessHall, Prison, Apothecary,
    BossQuarters, KoboldCaveEntrance, BanditBarracks, BanditMess, BanditKitchen,
)
from abc import ABC, abstractmethod

from region import TownRegion

class Morph(ABC):
    @abstractmethod
    def alter_region(self, region):
        pass

class AbandonMorph(Morph):
    def __init__(self, building_morph):
        self.building_morph = building_morph
        self.replaced = False
    
    def alter_region(self, region):
        # print(f"Applying abandon morph for building morph {self.building_morph}")
        self.building_morph.become_abandonned()
        return region

class Site:
    def __init__(self, sched=None, entrance_portal=None, agent=None, **kwargs):
        self.schedule = sched
        self.landmark : Optional[game_object.Landmark] = None
        if self.schedule is None:
            self.schedule = entrance_portal.schedule
        self.morphs = []
        self.populations = []
        self.region = None
        self.entrance_portal = entrance_portal
        entrance_portal.set_site(self)
        self.unused_morph_index = 0
        self.agent = agent
    
    def next_abandon_morph(self):
        for morph in self.morphs:
            if isinstance(AbandonMorph, morph):
                if not morph.replaced:
                    return morph
        return None

    def get_name(self, viewer=None):
        try:
            return self.landmark.name.get_text()
        except AttributeError:
            return "unnamed site"

    def allows_population(self, population):
        return all(p.allows_other(population) for p in self.populations)

    def add_population(self, population):
        if not self.allows_population(population):
            print(self.allows_population(population))
        self.populations.append(population)

    def remove_population(self, population):
        self.populations.remove(population)

    def die(self):
        # copy, to avoid iterator invalidation
        for population in list(self.populations):
            population.expel()

    def has_morph_type(self, typ):
        return any(isinstance(m, typ) for m in self.morphs)

    @classmethod
    def at_point(
        cls, location, direction,
        coordinates=None,
        portal_type=game_object.PortalEdge,
        landmark_name=None,
        **kwargs
    ):
        if "name" not in kwargs:
            kwargs["name_pair"] = (
                landmark_name,
                Name("exit")
            )
        portal = portal_type.free_portal(
            location, direction, coordinates, **kwargs
        )
        schedule = location.schedule
        output_site = cls(schedule, portal.target, **kwargs)
        if landmark_name:
            output_site.landmark = portal.source.create_landmark(landmark_name)
        return output_site

    def construct_base_region(self):
        raise NotImplementedError

    def add_morph(self, new_morph):
        self.morphs.append(new_morph)
        return self

    def unused_morphs(self):
        return self.morphs[self.unused_morph_index:]

    def update_region(self):
        print(self.morphs)
        if not self.region:
            self.construct_base_region()
        
        for morph in self.unused_morphs():
            self.region = morph.alter_region(self.region)
        self.unused_morph_index = len(self.morphs)

        for population in self.populations:
            population.render(self.region)

    def offload(self):
        for population in self.populations:
            population.hide_actors()


class TownSite(Site):
    # This is a placeholder until two goals are met:
    # 1. Region code is abstracted enough to accommodate towns
    # 2. Towns have proper a region subclass written

    def allows_population(self, population):
        # Placeholder for better faction logic
        return population.is_town_friendly

    def construct_base_region(self):
        self.region = TownRegion(
            self.entrance_portal, self.schedule, self.agent
        )


class TownBuildingMorph(Morph):
    def __init__(self, building_factory, shopkeeper_actor=None, replaced_abandon_morph=None):
        self.replaced_abandon_morph = replaced_abandon_morph
        self.building_factory = building_factory
        self.building = None
        self.shopkeeper_actor = shopkeeper_actor
        self.abandon = False
    
    def become_abandonned(self):
        # print(f"Attempting to abandon {self}")
        if self.building:
            # print("---- Immediately applying abandon effect")
            self.building.become_abandonned()
        else:
            # print("---- Can't apply yet, marking for later")
            self.abandon = True

    def alter_region(self, region):
        # print(f"Applying building morph {self}")
        assert isinstance(region, TownRegion)
        if self.replaced_abandon_morph:
            replaced_building = self.replaced_abandon_morph.building_morph
            replaced_door = replaced_building.door
        else:
            replaced_door = None

        self.building = self.building_factory(
            region.main_location,
            sched=region.schedule,
            shopkeeper_actor=self.shopkeeper_actor,
            replaced_door=replaced_door 
        )





        if self.abandon:
            # print("---- building morph {self} is abandoned, applying abandon effect")
            self.building.become_abandonned()
        region.add_room(self.building)
        # print(f"Done applying building morph {self}")
        return region

    def has_building(self):
        return self.building is not None

    def get_building(self):
        assert self.has_building()
        return self.building
    
    def get_abandon_morph(self) -> AbandonMorph:
        return AbandonMorph(self)



class RegionSite(Site):
    region_type = None

    def construct_base_region(self):
        self.region = self.region_type(
            entrance_portal=self.entrance_portal,
            sched=self.schedule
        )


# TODO: Make some kind of a class-factory for the following RegionSites?

class Cave(RegionSite):
    region_type = region.EmptyCaves


class RuneCave(RegionSite):
    region_type = region.RuneCave


class Tomb(RegionSite):
    region_type = region.EmptyTomb


class Hive(RegionSite):
    region_type = region.GiantInsectHive


class Habitation(Morph):
    essential_rooms = ()
    optional_rooms = ()
    filler_rooms = ()
    enemy_number = 0

    def alter_region(self, region):
        region.build_locations(
            essential=self.essential_rooms,
            optional=self.optional_rooms,
            filler=self.filler_rooms,
        )
        return region


class KoboldHabitation(Habitation):
    essential_rooms = (TreasureRoom, Barracks, Kitchen, KoboldCaveEntrance)
    optional_rooms = (MessHall, Prison, Apothecary, BossQuarters)
    enemy_number = 6


class BanditHabitation(Habitation):
    essential_rooms = (BanditBarracks, BanditMess, BanditKitchen)


class GhoulHabitation(Habitation):
    essential_rooms = (MeatChamber, )
    enemy_number = 4

    class EnemyPolicy(region.CreaturePolicy):
        adjectives = ["skinny", "tall", "hairy",
                      "filthy", "pale", "short", ]

        def get_creature(self, location=None):
            name = Name(self.get_adjective()+" ghoul")
            ghoul = actor.Person(location, name=name, sched=self.schedule)
            ai.WanderingMonsterAI(ghoul)
            ghoul.body = body.UndeadBody(ghoul)
            ghoul.combat_skill = 60
            return ghoul


def sites_test():
    class Numbers(Site):
        def construct_base_region(self):
            self.region = [10, 20, 30]

    class AddOne(Morph):
        def alter_region(self, region):
            return [x+1 for x in region]

    class TimesTwo(Morph):
        def alter_region(self, region):
            return [x*2 for x in region]

    n = Numbers()
    n.update_region()
    assert n.region == [10, 20, 30]
    n.add_morph(AddOne())
    n.add_morph(TimesTwo())
    assert n.region == [10, 20, 30]
    n.update_region()
    assert n.region == [22, 42, 62]


def cave_site_test():
    cave = Cave()
    cave.update_region()
    print(cave.region.get_text_map())
    cave.add_morph(KoboldHabitation())
    cave.update_region()
    print(cave.region.get_text_map())


if __name__ == "__main__":
    cave_site_test()
