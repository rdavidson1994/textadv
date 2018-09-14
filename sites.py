import levelgenerator
import game_object
import actor
import ai
import body
from dungeonrooms import (TreasureRoom, Barracks, Kitchen, MeatChamber,
                          MessHall, Prison, Apothecary, BossQuarters, )
from abc import ABC, abstractmethod


class Site:
    def __init__(self, sched=None, entrance_portal=None):
        self.schedule = sched
        self.morphs = []
        self.region = None
        self.entrance_portal = entrance_portal
        self.unused_morph_index = 0

    def construct_base_region(self):
        raise NotImplementedError

    def add_morph(self, new_morph):
        self.morphs.append(new_morph)

    def unused_morphs(self):
        return self.morphs[self.unused_morph_index:]

    def update_region(self):
        if not self.region:
            self.construct_base_region()
        
        for morph in self.unused_morphs():
            self.region = morph.alter_region(self.region)
        self.unused_morph_index = len(self.morphs)


class RegionSite(Site):
    region_type = None

    def construct_base_region(self):
        self.region = self.region_type(
            entrance_portal=self.entrance_portal,
            sched=self.schedule
        )


class Cave(RegionSite):
    region_type = levelgenerator.EmptyCaves


class Tomb(RegionSite):
    region_type = levelgenerator.EmptyTomb


class Morph(ABC):
    @abstractmethod
    def alter_region(self, region):
        pass


class Habitation(Morph):
    essential_rooms = ()
    optional_rooms = ()
    filler_rooms = ()
    enemy_number = 0

    EnemyPolicy = levelgenerator.CreaturePolicy
    BossPolicy = levelgenerator.CreaturePolicy

    def alter_region(self, region):
        region.enemy_policy = self.EnemyPolicy(region.schedule)
        region.boss_policy = self.BossPolicy(region.schedule)
        region.enemy_number = self.enemy_number

        region.build_locations(essential=self.essential_rooms,
                               optional=self.optional_rooms,
                               filler=self.filler_rooms, )

        region.create_inhabitants()
        return region


class KoboldHabitation(Habitation):
    essential_rooms = (TreasureRoom, Barracks, Kitchen)
    optional_rooms = (MessHall, Prison, Apothecary, BossQuarters)
    enemy_number = 6

    class EnemyPolicy(levelgenerator.CreaturePolicy):
        adjectives = ["skinny", "tall", "hairy",
                      "filthy", "pale", "short", ]
        enemy_type = actor.KoboldActor
        enemy_name = "kobold"

    class BossPolicy(levelgenerator.CreaturePolicy):
        def get_creature(self, location=None, adjective=None):
            name = game_object.Name(a=["kobold", "leader"],
                                    n=["leader", "kobold"])
            boss = actor.Actor(location=location,
                               name=name,
                               sched=self.schedule)
            boss.combat_skill = 75
            boss.ai = ai.WanderingMonsterAI(boss)
            spear = game_object.Item(location=boss,
                                     name=game_object.Name("crude", "sword"))
            spear.damage_type = "sharp"
            spear.damage_mult = 3
            return boss


class GhoulHabitation(Habitation):
    essential_rooms = (MeatChamber, )
    enemy_number = 4

    class EnemyPolicy(levelgenerator.CreaturePolicy):
        adjectives = ["skinny", "tall", "hairy",
                      "filthy", "pale", "short", ]

        def get_creature(self, location=None):
            name = game_object.Name(self.get_adjective(), "ghoul")
            ghoul = actor.Actor(location, name=name, sched=self.schedule)
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
