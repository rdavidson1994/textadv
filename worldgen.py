import schedule, actor, wide
import ai

class WorldAgent(actor.Actor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai = ai.WaitingMonsterAI(self)


world_schedule = schedule.Schedule()
world_map = wide.Location(sched=world_schedule)

if __name__ == "__main__":
    for i in range(6):
        agent = WorldAgent(location=world_map,
                           coordinates=world_map.random_point())
        print(agent.schedule)


    world_schedule.run_game(50000)
