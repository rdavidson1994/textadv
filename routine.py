"""
import action
class Routine():
    priority = 5
    time_elapsed = 0
    cooldown_time = 0
    def __init__(self, actor, *target_list):
        super().__init__(actor, *target_list)
        self.routine = None
        self.action_list = self.build_action_list()
        self.complete = False
    def build_action_list(self):
        return list()
    def attempt(self):
        self.actor.set_routine(self)
        return True, "SILENCE"
    def get_local_action(self):
        while self.action_list:
            next_action = self.action_list.pop()
            if next_action.is_valid()[0]:
                return next_action
            else:
                continue
        else:
            self.complete = True
            return None
    def get_action(self):
        if self.routine:
            sub_action = self.routine.get_action()
            if sub_action != None and sub_action.is_valid()[0]:
                return sub_action
            else:
                self.routine = None
        return self.get_local_action()

class WakeUpRoutine(Routine, action.ZeroTargetAction):
    class WakeUpAction(action.ZeroTargetAction):
        time_elapsed = 5000
        hidden = True
        synonyms = ["awaken"]
        def affect_game(self):
            self.actor.awake = True
    def build_action_list(self):
        return [self.WakeUpAction(self.actor)]

class AttackHeroRoutine(Routine, action.ZeroTargetAction):
    def get_local_action(self):
        no_victims = False
        try:
            next_victim = self.actor.location.things_with_trait(trait.hero)[0]
        except IndexError:
            no_victims = True
        if no_victims:
            return WaitAction(self.actor)
        else:
            self.routine = DefaultWeaponStrikeRoutine(self.actor, next_victim)
            return self.get_action()
"""
