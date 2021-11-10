import action
import trait

class AmbushActor(action.SingleTargetAction):
    time_elapsed = 0
    requires_reach = False
    cooldown_time = 0
    is_hostile = True
    target_traits = [trait.actor]
    hidden = True
    synonyms = ["ambush"]

    def affect_game(self):
        self.actor.ambush_actor(self.target)