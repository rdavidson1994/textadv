from wide import WideLocation
from actor import Actor
from schedule import Schedule
import ai


class World(WideLocation):
    pass


class WorldAgent(Actor):
    pass


if __name__ == "__main__":
    world_schedule = Schedule()
    world = World(sched=world_schedule)
    town1 = WorldAgent(location=world, coordinates=world.random_point())
    town1.ai = ai.WaitingMonsterAI(town1)
    world_schedule.run_game(50000)
    print("Done")
