import schedule, actor, wide, action
import ai


class TestAI(ai.AI):

    class TestAction(action.ZeroTargetAction):
        hidden = True
        synonyms = ["test action"]
        def affect_game(self):
            print("Action happened!")
    def get_local_action(self):
        return self.TestAction(self.actor)



class WorldAgent(actor.Actor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai = TestAI(self)


world_schedule = schedule.Schedule()
world_map = wide.Location(sched=world_schedule)

if __name__ == "__main__":
    for i in range(6):
        
        agent = WorldAgent(location=world_map,
                           coordinates=world_map.random_point())
    world_schedule.run_game(50000)
