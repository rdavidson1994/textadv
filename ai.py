import action
import logging
import trait
from action import (AttackHeroRoutine,
                    Routine,
                    Wait,
                    ZeroTargetAction,
                    Enter,
                    WanderOnceRoutine,
                    WalkToRandomRoutine,
                    Speak,
                    WrapperRoutine,
                    WalkToEntranceRoutine,
                    DefaultStrikeRoutine,
                    LeaveDungeonRoutine,
                    DestinationRoutine, )
from squad import Squad

debug = logging.debug


def element(set_):
    for e in set_:
        return e


def test(obj, method_str, *args, **kwargs):
    try:
        return getattr(obj, method_str)(*args, **kwargs)
    except AttributeError:
        return False


class AI(Routine):

    def __init__(self, actor, *args, **kwargs):
        self.actor = actor
        actor.ai = self
        self.routine = None

    """
    def start_routine(self, routine):
        act = routine.get_action()
        if act != None:
            self.routine = routine
        return act
    """

    def get_action(self):
        if not self.actor.awake:
            return Wait(self.actor)
        else:
            act = super().get_action()
            assert act is not None
            return act
        # if self.routine is not None:
        #     routine_action = self.routine.get_action()
        #     if routine_action is not None and routine_action.is_valid()[0]:
        #         return routine_action
        #     else:
        #         self.routine = None
        # return self.get_local_action()

    def get_current_action(self):
        try:
            event = self.actor.scheduled_event
            if event.is_cooldown:
                return None
            else:
                return event.action
        except AttributeError:
            return None

    def taking_hostile_action(self):
        act = self.get_current_action()
        if act is not None:
            self_hostile = getattr(act, "is_hostile", False)
            # we shouldn't ask to interrupt the player's attacks.
            return self_hostile
        else:
            return False

    def display(self, text):
        pass

    def final_transaction_check(self, action):
        return True, ""

    def get_local_action(self):
        return action.Wait(self.actor)

    def cancel_actions(self):
        self.actor.cancel_actions()

    def set_routine(self, routine, now=False):
        self.routine = routine
        if now:
             self.actor.cancel_actions()

    def set_action(self, action, now=False):
        routine = WrapperRoutine(action)
        self.set_routine(routine, now)
    
    """
    def hear_announcement(self, action):
        super().hear_announcement(action)
    """

    def is_hostile_to(self, other):
        return False

    def notice_damage(self, amt, typ):
        pass

    def offer_price(self, other, item):
        return 0


class WaitingMonsterAI(AI):
    def get_local_action(self):
        act = self.start_routine(AttackHeroRoutine(self.actor))
        if act:
            return act
        else:
            return Wait(self.actor)


class WanderingMonsterAI(AI):
    def is_hostile_to(self, other):
        return other.has_trait(trait.hero)

    def hear_announcement(self, act):
        super().hear_announcement(act)
        if getattr(act, "traverses_portals", False):
            if act.actor.has_trait(trait.hero):
                self.cancel_actions()

    def get_local_action(self):
        act = self.start_routine(AttackHeroRoutine(self.actor))
        if act:
            return act
        act = self.start_routine(WalkToRandomRoutine(self.actor))
        if act:
            return act
        return Wait(self.actor)


class SquadAI(AI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enemies = {}  # Note: Others have enemies as a set
        self.morale_level = "fight"  # also "rally" and "flee"
        self.squad = None

    def get_rally_point(self):
        return self.actor.location.rally_point()

    def attack_enemies(self, targets):
        target = next(iter(targets))
        act = self.start_routine(DefaultStrikeRoutine(self.actor, target))
        return act

    def join_other_squad(self, other):
        assert other.has_trait(trait.kobold)
        if other.squad:
            other.squad.add_member(self)
        else:
            self.squad = Squad(self)
            self.squad.add_member(other)

    def is_hostile_to(self, other):
        return other.has_trait(trait.hero)

    class Sighting:
        def __init__(self, viewer, thing):
            self.time = viewer.schedule.current_time
            self.location = thing.location

        def __repr__(self):
            return "Sighted in {} at {}".format(str(self.location), self.time)

    def new_sighting(self, thing):
        return self.Sighting(self.actor, thing)

    def share_enemy_knowledge(self, ally):
        try:
            method = ally.ai.hear_enemy_knowledge
        except AttributeError:
            pass
        else:
            method(self.enemies)

    def hear_enemy_knowledge(self, updated_enemies):
        for enemy, sighting in updated_enemies.items():
            if enemy not in self.enemies:
                debug("TATTLE to "+self.actor.name)
            if (
                    enemy not in self.enemies or
                    sighting.time > self.enemies[enemy].time
            ):
                self.enemies[enemy] = sighting

    def see_thing(self, thing):
        super().see_thing(thing)
        if thing == self.actor:
            return None
        if self.is_hostile_to(thing):
            self.enemies[thing] = self.new_sighting(thing)
            if not self.taking_hostile_action():
                # If not fighting, and see an enemy, cancel so you can fight.
                self.cancel_actions()

        if thing.has_trait(trait.kobold) and self.enemies:
            self.share_enemy_knowledge(thing)

        elif thing.has_trait(trait.corpse):
            # If you see a corpse, stop looking for its owner
            owner = getattr(thing, "owner", None)
            if owner in self.enemies:
                self.enemies.pop(owner)

    class Rally(Routine, ZeroTargetAction):
        class WalkToRallyRoutine(DestinationRoutine):
            def build_portal_list(self):
                return self.actor.location.path_to_rally()

        def see_thing(self, thing):
            nearby_allies = self.ai().nearby_allies()
            if len(nearby_allies) >= 3:
                self.ai().morale_level = "fight"
                self.complete = True

        def get_local_action(self):
            at_rally = self.ai().at_rally()
            nearby_enemies = self.ai().nearby_enemies()
            nearby_allies = self.ai().nearby_allies()
            if at_rally:
                if nearby_enemies:
                    return self.ai().attack_enemies(nearby_enemies)
                else:
                    return Wait(self.actor)
            else:
                rout = self.WalkToRallyRoutine(self.actor)
                act = self.start_routine(rout)
                if act:
                    return act

    class Flee(Routine, ZeroTargetAction):
        def get_local_action(self):
            act = self.start_routine(LeaveDungeonRoutine(self.actor))
            if act:
                return act
            else:
                return Wait(self.actor)

    class HuntEnemiesRoutine(DestinationRoutine):
        def __init__(self, enemies, *args, **kwargs):
            self.enemies = enemies
            super().__init__(*args, **kwargs)

        def build_portal_list(self):
            paths = []
            for enemy, sighting in self.enemies.items():
                target_location = sighting.location
                try:
                    path = self.actor.location.path_to_location(target_location)
                    paths.append(path)
                except AttributeError:
                    pass
            if paths:
                best = min(paths, key=len)
                if best:
                    return best

            return []

    def nearby_enemies(self):
        things = self.actor.location.things
        return things.intersection(self.enemies.keys())

    def nearby_allies(self):
        things = self.actor.location.things
        return {t for t in things if t.has_trait(trait.kobold)}

    def at_rally(self):
        return self.actor.location == self.get_rally_point()

    def get_local_action(self):
        nearby_enemies = self.nearby_enemies()
        if self.enemies:
            if self.morale_level == "fight":
                if nearby_enemies:
                    act = self.attack_enemies(nearby_enemies)
                    if act:
                        return act
                    else:
                        pass # print_("FAILED: Nearby enemies, but couldn't attack")
                else:
                    rout = self.HuntEnemiesRoutine(self.enemies, self.actor)
                    act = self.start_routine(rout)
                    if act:
                        return act
                    debug("RANDOM WALK FALLBACK USED")
                    act = self.start_routine(WalkToRandomRoutine(self.actor))
                    if act:
                        return act
            elif self.morale_level == "rally":
                return self.start_routine(self.Rally(self.actor))
            else:  # if self.morale_level == "flee"
                return self.start_routine(self.Flee(self.actor))
        act = self.start_routine(WalkToRandomRoutine(self.actor))
        if act:
            return act
        return Wait(self.actor)

    def notice_damage(self, amt, typ):
        if self.actor.body.damage > 100:
            self.morale_level = "flee"
        elif amt > 15 and self.actor.body.damage > 50:
            self.morale_level = "rally"


class PeacefulAI(AI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.present_enemies = set()
        self.enemies = set()

    def actor_enters_location(self, act):
        if act.actor in self.enemies:
            self.present_enemies.add(act.actor)
            if not self.taking_hostile_action():
                # If an enemy is present, cancel non-combat actions
                self.cancel_actions()
                self.set_routine(self.CombatRoutine(self.actor), now=True)

    def actor_leaves_location(self, act):
        if act.actor in self.present_enemies:
            self.present_enemies.remove(act.actor)

    def hostile_action_taken(self, act):
        if act.target == self.actor and act.actor not in self.enemies:
            self.enemies.add(act.actor)
            self.present_enemies.add(act.actor)
            if not self.taking_hostile_action():
                self.cancel_actions()
                self.start_routine(self.CombatRoutine(self.actor))

    def hear_announcement(self, act):
        super().hear_announcement(act)
        if act.traverses_portals:
            if self.actor.location.has_thing(act.actor):
                self.actor_enters_location(act)
            else:
                self.actor_leaves_location(act)
        elif getattr(act, "is_hostile", False):
            self.hostile_action_taken(act)

    class CombatRoutine(action.Routine, action.ZeroTargetAction):
        def get_local_action(self):
            ai = self.ai()
            while ai.present_enemies:
                enemy = element(ai.present_enemies)
                rout = DefaultStrikeRoutine(self.actor, enemy)
                act = self.start_routine(rout)
                if act:
                    # Loop breaks
                    return act
                else:
                    # Loop continues to next enemy
                    ai.present_enemies.remove(enemy)
            self.complete = True
            return None  # if no more enemies

    def get_local_action(self):
        if self.present_enemies:
            act = self.start_routine(self.CombatRoutine(self.actor))
            if act:
                return act
        return super().get_local_action()


class PrisonerAI(PeacefulAI):
    has_seen_hero = False
    hostile_to_hero = False

    def is_hostile_to(self, other):
        return other in self.enemies

    def hear_announcement(self, action):
        super().hear_announcement(action)
        if (
               getattr(action, "locks_things", False)
               and action.desired_state == False
               and action.target == self.actor.trapping_item
           ):
            debug("unlocked cage detected")
            text = "Thank you for freeing me, kind stranger."
            self.set_action(Speak(self.actor, text=text), now=True)

    def get_local_action(self):
        if (
            self.actor.location.things_with_trait(trait.hero)
            and self.hostile_to_hero
        ):
            act = self.start_routine(AttackHeroRoutine(self.actor))
            if act:
                return act
        act = self.start_routine(LeaveDungeonRoutine(self.actor))
        if act:
            return act
        return super().get_local_action()

    def actor_enters_location(self, e):
        if e.actor.is_hero():
            if not self.has_seen_hero:
                self.has_seen_hero = True
                text = "Thank God you found me! Please help."
                action = Speak(self.actor, text=text)
                self.set_action(action, now=True)
            elif self.hostile_to_hero:
                routine = AttackHeroRoutine(self.actor)
                self.set_routine(routine, now=True)
            else:
                pass


if __name__ == "__main__":
    import actor
    from location import Location

    place = Location()
    dude = actor.WaitingActor()
    my_action = dude.get_action()
