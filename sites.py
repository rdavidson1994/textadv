import region
import game_object
import actor
import ai
import body
from name_object import Name
from dungeonrooms import (
    TreasureRoom, Barracks, Kitchen, MeatChamber, MessHall, Prison, Apothecary,
    BossQuarters, KoboldCaveEntrance, BanditBarracks, BanditMess, BanditKitchen,
)
from abc import ABC, abstractmethod

from region import TownRegion


class Site:
    def __init__(self, sched=None, entrance_portal=None, **kwargs):
        self.schedule = sched
        self.landmark = None
        if self.schedule is None:
            self.schedule = entrance_portal.schedule
        self.morphs = []
        self.populations = []
        self.region = None
        self.entrance_portal = entrance_portal
        entrance_portal.set_site(self)
        self.unused_morph_index = 0

    def get_name(self, viewer=None):
        try:
            return self.landmark.name.get_text()
        except AttributeError:
            return "unnamed site"

    def allows_population(self, population):
        return all(p.allows_other(population) for p in self.populations)

    def add_population(self, population):
        assert self.allows_population(population)
        self.populations.append(population)

    def remove_population(self, population):
        self.populations.remove(population)

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


class Morph(ABC):
    @abstractmethod
    def alter_region(self, region):
        pass


class TownSite(Site):
    # This is a placeholder until two goals are met:
    # 1. Region code is abstracted enough to accommodate towns
    # 2. Towns have proper a region subclass written

    def __init__(self, *args, agent, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent = agent

    def allows_population(self, population):
        return False

    def construct_base_region(self):
        self.region = TownRegion(
            self.entrance_portal, self.schedule, self.agent
        )


class TownBuildingMorph(Morph):
    def __init__(self, building_factory):
        self.building_factory = building_factory

    def alter_region(self, region):
        assert isinstance(region, TownRegion)
        building = self.building_factory(
            region.main_location,
            sched=region.schedule,
        )
        region.add_room(building)
        return region


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
