from name_object import Name
import ai
import game_object
import errors
import dungeonrooms
import actor
import unittest


class Population:
    built = False
    rendered = False

    def get_location(self, actor, region):
        try:
            return self.location_functions[actor](region)
        except KeyError:
            return region.random_location(exclude_entrance=True)

    def __init__(self):
        self.built = False
        self.site = None
        self.rendered = False
        self.actors = []
        self.location_functions = {}

    def render(self, region):
        if not self.built:
            self.build_actors()
            self.built = True
        if not self.rendered:
            self.show_actors(region)
        self.rendered = True

    def allows_other(self, population):
        return False

    def hide_actors(self):
        assert self.rendered
        self.actors = [a for a in self.actors if a.location is not None]
        # Filter out dead actors
        for actor in self.actors:
            actor.vanish()
        self.rendered = False

    def show_actors(self, region):
        for actor in self.actors:
            actor.materialize(self.get_location(actor, region))

    def build_actors(self):
        pass


class Kobold(Population):
    minions = 6
    adjectives = [
        "skinny", "tall", "hairy", "filthy", "pale", "short",
    ]

    def allows_other(self, population):
        return False

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
        for adjective in self.adjectives:
            kobold = actor.SquadActor(
                location=None,
                name=Name(adjective)+"kobold"
            )
            self.actors.append(kobold)

        boss = actor.Person(
            location=None,
            name=Name("kobold leader"),
        )
        self.actors.append(boss)
        boss.ai = ai.WanderingMonsterAI(boss)
        sword = game_object.Item(location=boss, name=Name("crude sword"))
        sword.damage_type = "sharp"
        sword.damage_mult = 6
        self.location_functions[boss] = self.boss_location_function


class TestPopulation(unittest.TestCase):
    def test_hide_actors(self):
        import direction
        from sites import Cave
        import wide
        from schedule import Schedule
        world = wide.Location(sched=Schedule(), name="world")
        cave = Cave.at_point(
            world,
            coordinates=(15, 15),
            direction=direction.random(),
            landmark_name="cave"
        )
        assert (world.schedule.current_time == 0)
        p = Kobold()
        cave.add_population(p)
        world.schedule.run_game(3000)
        assert(world.schedule.current_time == 0)
        cave.update_region()
        world.schedule.run_game(3000)
        assert (world.schedule.current_time == 3000)
        p.hide_actors()
        world.schedule.run_game(3000)
        assert (world.schedule.current_time == 3000)
        cave.update_region()
        world.schedule.run_game(3000)
        assert (world.schedule.current_time == 6000)
        p.hide_actors()
        cave.update_region()
        world.schedule.run_game(3000)
        assert (world.schedule.current_time == 9000)

if __name__ == "__main__":
    unittest.main()