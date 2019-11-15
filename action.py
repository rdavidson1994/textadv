import logging
# logging.basicConfig(level=logging.DEBUG,format='%(message)s')
from math import sqrt, floor

import location
import mixins
import re
from random import randint, choice
from verb import Verb, StandardVerb, gfl
import direction

debug = logging.debug


def group_from_list(lst):
    group = r"|".join(lst)
    group = r"(?:" + group + r")"
    return group


def match_action_to_string(actor, input_string):
    return Verb.match_action_to_string(actor, input_string)


class ActionMeta(type):
    def __init__(cls, name, bases, dct):
        if cls.VerbClass and cls.synonyms and not cls.hidden:
            cls.verb = cls.VerbClass(cls)

# ABSTRACT ACTIONS


class Action(metaclass=ActionMeta):
    VerbClass = StandardVerb
    hidden = False
    priority = 10
    stamina_cost = 0
    mana_cost = 0
    time_elapsed = 1000  # In milliseconds of imaginary game time.
    cooldown_time = 500
    is_hostile = False
    is_instant = False
    traverses_portals = False
    is_social = False
    synonyms = []
    number_of_targets = 0  # 0, 1, or 2, or more if I go crazy.
    target_traits = []
    tool_traits = []
    not_enough_targets_string = ""
    too_many_targets_string = "That action doesn't require a target."

    def __init__(self, actor, *target_list, quiet=False):
        self.quiet = quiet
        self.actor = actor
        self.target_list = target_list
        self.set_special_targets()

    def set_special_targets(self):
        if len(self.target_list) > 1:
            self.tool = self.target_list[1]
        else:
            self.tool = None
        if len(self.target_list) > 0:
            self.target = self.target_list[0]
        else:
            self.target = None

    @staticmethod
    def is_routine():
        return False

    def moves_actor(self):
        return (
            getattr(self, "traverses_portals", False)
            or getattr(self, "travels_overland", False)
        )

    def check_target_number(self):
        # debug(self.target_list)
        """
        Checks whether target_list is the correct length
        If not, says why not. Fr

        Returns (Bool, String)

        Bool = True if the number and kind of targets is correct, False otherwise

        String = Explanation of the failure if Bool == False, empty string
        if Bool == True."""
        if len(self.target_list) < self.number_of_targets:
            return False, self.not_enough_targets_string
        elif len(self.target_list) > self.number_of_targets:
            return False, self.too_many_targets_string
        else:
            return True, ""

    def check_geometry(self):
        """Returns a Bool, String tuple.
        if action is possible, returns (True, '')
        if not, returns (False, 'some explanatory text')
        """
        return True, ""

    def check_traits(self):
        """Returns (Bool, String)
        Determines if things in target_list have the traits required of them for
        the action to be performed.
        Returns True, "" if so, False, "explanation" otherwise.
        """
        trait_lists = [self.target_traits, self.tool_traits]

        for i in range(self.number_of_targets):
            # check i=0 if you have a target, and also i=1 if you have a tool
            for trait in trait_lists[i]:
                # for each trait required of the target/tool
                if self.target_list[i].has_trait(trait):
                    # check that the target/tool has that trait
                    continue
                else:
                    # if any trait fails, return false and tell the user why.
                    ith_name = self.target_list[i].get_name(self.actor)
                    return False, "{} is not a {}.".format(ith_name, trait)
        else:
            # if nothing fails, the test passes.
            return True, ""

    def final_self_check(self):
        return True, ""

    def is_valid(self):
        for test in [self.check_target_number,
                     self.check_geometry,
                     self.check_traits]:
            permission, explanation = test()
            if not permission:
                return False, explanation
            else:
                pass
        else:
            return True, ""

    def target_responses(self):
        return True, ""

    def attempt(self):
        """Tries to have the actor perform this action on the target_list.
        This is the method called by the parser for the player character,
        or by the ai for the NPCs."""
        debug("Action attempted {}".format(self))

        targets_ok, explanation = self.target_responses()
        if not targets_ok:
            self.actor.receive_action_feedback(False, explanation)
            return

        final_ok, explanation = self.final_self_check()
        if not final_ok:
            self.actor.receive_action_feedback(False, explanation)
            return

        self.succeed()
        try:
            body = self.actor.body
            body.take_fatigue(self.stamina_cost)
            body.lose_mana(self.mana_cost)
        except AttributeError:
            pass

    def succeed(self):
        feedback = self.get_success_string(self.actor)
        if not self.quiet:
            self.actor.receive_action_feedback(True, feedback)
        # Trying to swap these from announce, affect to affect, announce.
        self.affect_game()
        self.actor.announce(self)

    def affect_game(self):
        """No returns.
        Conducts the effects of a successful action.
        For example, if the action is TakeAction, this method moves the
        target into the inventory of the actor.
        """
        pass

    def get_success_string(self, viewer=None):
        """Returns an appropriate string describing the actor completing
        the action with the given target_list.
        """
        return "{} {}.".format(self.actor.get_name(viewer),
                               self.get_name(viewer), )

    def get_raw_name(self, viewer=None):
        return self.synonyms[0]

    def possible_s(self, viewer=None):
        if viewer != self.actor:
            return "s"
        else:
            return ""

    def get_name(self, viewer=None):
        out = self.get_raw_name(viewer) + self.possible_s(viewer)
        return out


ZeroTargetAction = Action
# just to display the fact that the
# base Action class is a fully implemented foundation for actions
# with no targets, not just an abstract class.


class SingleTargetAction(Action):
    number_of_targets = 1
    not_enough_targets_string = "You must specify a target."
    too_many_targets_string = "That action doesn't require a tool."
    requires_reach = True

    def target_responses(self):
        permission, explanation = super().target_responses()
        if permission:
            return self.target.be_targeted(self)
        else:
            return permission, explanation

    # def attempt(self):
    #    target_ok, explanation = self.target.be_targeted(self)
    #    if target_ok:
    #        super().attempt()
    #    else:
    #        self.actor.receive_action_feedback(False, explanation)

    def get_success_string(self, viewer=None):
        return "{} {} {}.".format(self.actor.get_name(viewer),
                                  self.get_name(viewer),
                                  self.target.get_identifier(viewer), )

    def check_geometry(self):
        if not self.requires_reach or self.actor.can_reach(self.target):
            return super().check_geometry()
        else:
            template = "You cannot reach the {}."
            return False, template.format(self.target.get_name(self.actor))


class ToolAction(SingleTargetAction):
    number_of_targets = 2
    tool_traits = []
    not_enough_targets_string = ("You need a target and a "
                                 "tool to perform that action")
    too_many_targets_string = "You need a tool to perform that action."


class FailAction(ZeroTargetAction):
    time_elapsed = 0
    cooldown_time = 0

    def __init__(self, actor, failure_string):
        super().__init__(actor)
        self.failure_string = failure_string

    def is_valid(self):
        return False, self.failure_string

    def attempt(self):
        return False, self.failure_string


# CONCRETE ACTIONS

class DetailAction(ZeroTargetAction):
    time_elapsed = 0
    cooldown_time = 0
    is_instant = True


class Look(DetailAction):
    synonyms = ["look", "examine", "x", "l"]

    def affect_game(self):
        self.actor.view_location()


class Map(DetailAction):
    synonyms = ["recall the surroundings", "map", "show map", "m"]

    def get_success_string(self, viewer=None):
        out = self.actor.location.get_text_map(viewer=viewer, full_size=True)
        if out is None:
            return "No map is available."
        else:
            return out

    # def affect_game(self):
    #     a = self.actor
    #     try:
    #         region = a.location.map_node.region
    #     except AttributeError:
    #         a.ai.display("No map is available.")
    #     else:
    #         a.ai.display(region.get_text_map(a))


class Verbose(DetailAction):
    synonyms = ["verbose", "v"]

    def affect_game(self):
        self.actor.ai.verbose = not self.actor.ai.verbose

    def get_success_string(self, viewer=None):
        if self.actor.ai.verbose:
            return "Verbose mode disabled"
        else:
            return "Verbose mode enabled"


class Diagnose(DetailAction):
    synonyms = ["diagnose", "health", "diagnostic", "hp", "h", "damage",
                "fatigue", "stamina", "mana", ]

    def check_geometry(self):
        if hasattr(self.actor, "body"):
            return super().check_geometry()
        else:
            return False, "You don't have a physical body."

    def get_success_string(self, viewer=None):
        return self.actor.get_health_report(viewer=viewer)


class SpellReport(DetailAction):
    synonyms = ["spells", "magic", "spells"]

    def check_geometry(self):
        if getattr(self.actor, "spells_known", False):
            return super().check_geometry()
        else:
            return False, "You don't know any spells."

    def get_success_string(self, viewer=None):
        spells = self.actor.spells_known
        spell_names = [spell.synonyms[0] for spell in spells]
        mana_costs = [spell.mana_cost for spell in spells]
        width = max(len(s) for s in spell_names)+1

        return "\n".join(
            f"{name+',': <{width}} mana cost {cost}"
            for name, cost in zip(spell_names, mana_costs)
        )


class Examine(DetailAction, SingleTargetAction):
    synonyms = ["x", "look at", "examine", "look", "l"]

    def get_success_string(self, viewer=None):
        return self.target.get_look_text(viewer)


class LoudWait(ZeroTargetAction):
    synonyms = ["wait", "delay"]
    time_elapsed = 1000
    cooldown_time = 0

    def get_success_string(self, viewer=None):
        if self.actor.awake:
            return super().get_success_string(viewer)
        else:
            return "SILENCE"

    def affect_game(self):
        pass


class Wait(LoudWait):
    def __init__(self, *args, **kwargs):
        kwargs["quiet"] = True
        super().__init__(*args, **kwargs)


class LongWait(Wait):
    time_elapsed = float("inf")


class NullAction(Wait):
    synonyms = []
    time_elapsed = 0
    cooldown_time = 0
    is_instant = True

    def affect_game(self):
        pass

    def get_success_string(self, viewer=False):
        return "SILENCE"


class Speak(ZeroTargetAction):
    time_elapsed = 100
    cooldown_time = 100
    hidden = True
    synonyms = ["speak"]

    def __init__(self, actor, *target_list, text="TEXT"):
        super().__init__(actor, *target_list)
        self.text = text

    def affect_game(self):
        self.actor.location.show_text_to_hero('"' + self.text + '"')


class Eat(mixins.HeldTarget, SingleTargetAction):
    synonyms = ["eat", "drink"]
    target_traits = ["food"]
    time_elapsed = 2000

    def affect_game(self):
        self.target.vanish()


class Take(mixins.ItemTarget, SingleTargetAction):
    synonyms = ["take", "get", "pick up", "grab", ]

    def check_geometry(self):
        if self.actor.has_thing(self.target):
            return False, "You already have the item you are trying to take."
        if not self.actor.can_reach(self.target):
            return False, "The item you're trying to pick up isn't here."
        if self.actor == self.target:
            return False, "You cannot take yourself."
        return super().check_geometry()

    def affect_game(self):
        self.target.change_location(self.actor, self.actor.coordinates)


class Drop(mixins.HeldTarget, SingleTargetAction):
    synonyms = ["drop"]

    def affect_game(self):
        self.target.change_location(
            self.actor.location, self.actor.coordinates)


class Enter(mixins.Motion, SingleTargetAction):
    """For when the player says 'Enter the wooden door'.
    the door you enter is the one he/she tells you to."""
    synonyms = ["enter"]
    target_traits = ["portal"]

    def __init__(self, actor, *target_list):
        super().__init__(actor, *target_list)
        self.source_location = self.actor.location
        if self.target == self.actor.nearest_portal:
            self.time_elapsed = 200

    def check_geometry(self):
        if self.actor.trapping_item and self.actor.trapping_item.is_locked():
            name = self.actor.trapping_item.get_name(self.actor)
            return False, "You cannot leave while trapped in the {}.".format(
                name)
        else:
            return super().check_geometry()

    def get_success_string(self, viewer=None):
        if viewer != self.actor:
            return super().get_success_string(viewer)
        else:
            return "SILENCE"

    def get_portal(self):
        return self.target

    def get_raw_name(self, viewer=None):
        if viewer is None:
            return "enter"
        elif viewer.location == self.source_location:
            return "exit"
        else:
            return "enter"


class LockingAction(mixins.HeldTool, ToolAction):
    target_traits = ["lockable"]
    desired_state = None  # True/False
    desired_string = None  # "locked"/"unlocked"
    locks_things = True

    def affect_game(self):
        self.target.lock.locked = self.desired_state


class Lock(LockingAction):
    synonyms = ["lock"]
    desired_state = True
    desired_string = "locked"


class Unlock(LockingAction):
    synonyms = ["unlock"]
    desired_state = False
    desired_string = "unlocked"


class WeaponStrike(mixins.HeldTool, ToolAction):
    synonyms = ["strike", "hit", "attack"]
    time_elapsed = None  # Overwritten in __init__
    cooldown_time = None  # Overwritten in __init__
    is_hostile = True
    is_physical_attack = True
    stamina_cost = 6

    def __init__(self, actor, *target_list):
        super().__init__(actor, *target_list)
        try:
            weapon = self.tool
        except AttributeError:
            weapon = None

        self.attack_roll = actor.get_attack_roll(weapon)
        self.time_elapsed = actor.get_attack_onset_time()
        self.cooldown_time = actor.get_attack_cooldown_time()

    def check_geometry(self):
        if not self.actor.can_reach(self.target):
            return False, "The target of your attack is no longer here."
        else:
            return super().check_geometry()

    def affect_game(self):
        try:
            damage_type = self.tool.damage_type
            damage_mult = self.tool.damage_mult
        except AttributeError:
            damage_type = "blunt"
            damage_mult = 1
        amt = self.actor.get_melee_damage(self.tool) * damage_mult
        self.target.take_damage(amt, damage_type)


class AssumePosture(ZeroTargetAction):
    priority = 20
    time_elapsed = 100
    cooldown_time = 50
    synonyms = ["assume", "adopt"]

    class VerbClass(Verb):
        match_strings = ["VERB POSTURE"]

    def __init__(self, *args, posture, **kwargs):
        super().__init__(*args, **kwargs)
        self.posture = posture

    def check_geometry(self):
        from actor import Humanoid
        if isinstance(self.actor, Humanoid):
            if self.posture in self.actor.postures_known:
                return True, ""
            return False, "You don't know that posture."
        return False, "You can't use stances or grips since you are not humanoid"

    def affect_game(self):
        self.actor.adopt_posture(self.posture)

    def get_success_string(self, viewer=None):
        s = self.possible_s(viewer)
        name = self.actor.get_name(viewer)
        posture_name = self.posture.name.get_text(viewer)
        return f"{name} assume{s} the {posture_name}"


class PostureReport(DetailAction):
    synonyms = ["stances", "guards", "postures"]

    def get_success_string(self, viewer=None):
        from actor import Humanoid
        from posture import Stance, Guard
        if isinstance(self.actor, Humanoid) and len(self.actor.postures_known) != 0:
            out = ["Stances:"]
            out.extend(
                posture.get_summary(self.actor)
                for posture in self.actor.postures_known
                if isinstance(posture, Stance)
            )
            out.append("\nGuards:")
            out.extend(
                posture.get_summary(self.actor)
                for posture in self.actor.postures_known
                if isinstance(posture, Guard)
            )
            return "\n".join(out)
        return "You don't know any postures"


class VectorTravel(ZeroTargetAction):
    hidden = True
    travels_overland = True
    synonyms = ["travel"]

    def __init__(self, *args, vector=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.vector = vector
        try:
            old_x, old_y = self.actor.coordinates
            # TypeError, if actor has no coordinates
            diff_x, diff_y = self.vector
            # TypeError, if action has no vector (up or down movement)
            self.new_coordinates = (old_x + diff_x, old_y + diff_y)
        except TypeError:
            self.new_coordinates = None

    def check_geometry(self):
        if not self.actor.location.has_trait("wide"):
            return False, "You can't travel overland from here."
        if self.new_coordinates is None:
            return False, "You can't travel that way from here."
        elif not self.actor.location.includes_point(*self.new_coordinates):
            return False, "That point is not accessible from here."
        else:
            return super().check_geometry()

    def affect_game(self):
        self.actor.change_location(self.actor.location, self.new_coordinates)


class Transaction(ToolAction):
    is_social = True

    def get_names(self, viewer=None):
        if viewer is None:
            viewer = self.actor
        return (self.target.get_name(viewer),
                self.tool.get_name(viewer))

    def get_success_string(self, viewer=None):
        merchant_name, item_name = self.get_names(viewer)
        # Ordinarily, the target is the object of the verb.
        # Since the shopkeeper is the target here, we must replace
        out = super().get_success_string(viewer)
        return out.replace(merchant_name, item_name)


class Buy(Transaction):
    synonyms = ["buy", "purchase"]

    class VerbClass(Verb):
        match_strings = ["VERB TOOL from TARGET"]

    def check_geometry(self):
        if self.tool.owner != self.target:
            template = "The {} doesn't own the {}."
            return False, template.format(*self.get_names())
        elif self.actor == self.tool.owner:
            return False, "You already own that item."
        elif self.actor.money < self.tool.price:
            return False, "You cannot afford that item."
        else:
            return super().check_geometry()

    def affect_game(self):
        self.actor.money -= self.tool.price
        self.tool.owner = self.actor
        self.target.money += self.tool.price


class Sell(Transaction):
    synonyms = ["sell"]
    proposed_price = None

    class VerbClass(Verb):
        match_strings = ["VERB TOOL to TARGET"]

    def set_price(self, new_price):
        self.proposed_price = new_price

    def final_self_check(self):
        if self.proposed_price is not None and self.actor.agrees_to(self):
            return True, ""
        else:
            return False, "Unable to agree on a price, you cancel the deal."

    def check_geometry(self):
        if self.tool.owner != self.actor and self.tool.owner is not None:
            template = "You don't own the {}"
            return False, template.format(self.tool.get_name(self.actor))
        else:
            return super().check_geometry()

    def affect_game(self):
        self.actor.money += self.proposed_price
        self.target.money -= self.proposed_price
        self.tool.owner = self.target


class RentInnRoom(SingleTargetAction):
    is_social = True
    synonyms = ["rent", "rent room"]
    time_elapsed = 28800000

    class VerbClass(Verb):
        match_strings = ["VERB room from TARGET", "VERB from TARGET"]

    def get_success_string(self, viewer=None):
        s = self.possible_s(viewer)
        name = self.actor.get_name(viewer)
        return f"{name} feel{s} refreshed after a night at the inn."

    def check_geometry(self):
        inn = self.actor.location
        if not inn.has_trait("inn"):
            return False, "This isn't an inn."
        elif inn.room_price > self.actor.money:
            return False, "You can't afford to stay here."
        else:
            return super().check_geometry()

    def affect_game(self):
        price = self.actor.location.room_price
        self.actor.money -= price
        self.target.money += price
        self.actor.full_rest()


class WildernessFlee(ZeroTargetAction):
    synonyms = ["vanish"]
    hidden = True

    def affect_game(self):
        debug("ACTOR VANISHED")
        self.actor.vanish()

    def check_traits(self):
        if self.actor.location.has_trait("wide"):
            return super().check_traits()
        else:
            return False, "This location is too small for that."

# ROUTINES


class Routine:
    priority = 5
    time_elapsed = 0
    cooldown_time = 0
    empty_reason = "That doesn't make sense."

    def __init__(self, actor, *target_list):
        super().__init__(actor, *target_list)
        self.routine = None
        self.complete = False
        self.actor = actor

    @staticmethod
    def is_routine():
        return True

    def agrees_to(self, own_action):
        return True

    def hear_announcement(self, action):
        if self.routine and not self.routine.complete:
            self.routine.hear_announcement(action)
        if (
                getattr(action, "traverses_portals", False)
                and self.actor.awake
        ):
            # question of the day: Why does this not happen?
            # print("Saw thing due to entrance announcement")
            self.see_thing(action.actor)

    def social_response(self, act):
        if self.routine and not self.routine.complete:
            routine_response = self.routine.social_response(act)
            if routine_response is not None:
                return routine_response
            else:
                return True, ""

        if self.actor.awake:
            # Default permissive behavior.
            return True, ""
        else:
            return False, "That person is unconscious."

    def see_thing(self, thing):
        pass

    def is_none(self):
        return self.complete

    def start_routine(self, routine, *args, **kwargs):
        if isinstance(routine, type):
            # if they passed you a class, instantiate it before use.
            routine = routine(self.actor, *args, **kwargs)
        act = routine.get_action()
        if act is not None:
            self.routine = routine
        return act

    def attempt(self):
        print("ROUTINE ATTEMPTED FOR: " + self.actor.name)
        self.actor.set_routine(self)
        # This is bad news, since routines shouldn't make it to the schedule
        return True, "SILENCE"

    def get_local_action(self):
        print("Routine stub hit")
        self.complete = True
        return None

    def invalid_action_fallback(self, failed_action):
        return self.get_local_action()

    def get_action(self):
        if self.routine:
            sub_action = self.routine.get_action()
            if sub_action is None:
                self.routine = None
                return self.get_local_action()
            elif not sub_action.is_valid()[0]:
                self.routine = None
                return self.invalid_action_fallback(sub_action)
            else:
                return sub_action
        else:
            return self.get_local_action()

    def ai(self):
        return self.actor.ai

    def reason_for_empty(self):
        """
        A player-readable string, indicating why this routine does not
        contain any actions.
        """
        return self.empty_reason


class ActionListRoutine(Routine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.action_list = self.build_action_list()

    def build_action_list(self):
        raise NotImplementedError

    def get_local_action(self):
        while self.action_list:
            next_action = self.action_list.pop()
            if next_action.is_routine():
                return self.start_routine(next_action)
            elif next_action.is_valid()[0]:
                return next_action
            else:
                continue
        else:
            self.complete = True
            return None


class SingleActionRoutine(Routine):
    def get_single_action(self):
        raise NotImplementedError

    def get_local_action(self):
        if not self.complete:
            self.complete = True
            return self.get_single_action()
        else:
            return None


class WrapperRoutine(SingleActionRoutine, ZeroTargetAction):
    def __init__(self, action):
        self.action = action
        super().__init__(action.actor)

    def get_single_action(self):
        return self.action


class GeneralBuyRoutine(SingleActionRoutine, SingleTargetAction):
    synonyms = ["buy", "purchase"]
    empty_reason = "The owner of that object is not present."

    def get_single_action(self):
        merchant = self.target.owner
        if merchant:
            item = self.target
            return Buy(self.actor, merchant, item)
        else:
            return None


class GeneralSellRoutine(SingleActionRoutine, SingleTargetAction):
    synonyms = ["sell"]
    empty_reason = "There is no merchant here to deal with."

    def get_single_action(self):
        candidates = self.actor.get_targets_from_trait("merchant")
        if candidates:
            return Sell(self.actor, candidates[0], self.target)
        else:
            return None


class GeneralRentRoutine(SingleActionRoutine, ZeroTargetAction):
    synonyms = ["rent", "rent room", "sleep"]
    empty_reason = "There is no innkeeper here."

    def get_single_action(self):
        candidates = self.actor.get_targets_from_trait("merchant")
        if candidates:
            return RentInnRoom(self.actor, candidates[0])
        else:
            return None


class ReadRoutine(SingleActionRoutine, SingleTargetAction):
    synonyms = ["read"]
    target_traits = ["readable"]

    def get_single_action(self):
        # placeholder, will need to revist when books exist
        return Examine(self.actor, self.target)


class DefaultStrikeRoutine(SingleActionRoutine, SingleTargetAction):
    synonyms = ["strike", "hit", "attack"]
    priority = 15
    empty_reason = "No weapon strike"

    def get_single_action(self):
        weapons_in_inventory = []
        for weapon in self.actor.things:
            try:
                if weapon.damage_mult > 1:
                    weapons_in_inventory.append(weapon)
            except AttributeError:
                pass
        if weapons_in_inventory:
            weapon = max(weapons_in_inventory, key=lambda x: x.damage_mult)
        else:
            weapon = self.actor  # representing an unarmed strike.
        return WeaponStrike(self.actor, self.target, weapon)


class TakeAllRoutine(ActionListRoutine, ZeroTargetAction):
    synonyms = ["take all", "get all"]
    empty_reason = "There is nothing here to take."

    def build_action_list(self):
        return [Take(self.actor, item)
                for item in self.actor.get_valid_targets()]


class RestRoutine(Routine, ZeroTargetAction):
    synonyms = ["rest"]
    empty_reason = "You are already rested."

    def get_local_action(self):
        if self.actor.body.short_fatigue >= 1:
            return Wait(self.actor)
        else:
            return None


class ExitRoutine(SingleActionRoutine, ZeroTargetAction):
    synonyms = ["exit", "leave"]

    def get_single_action(self):
        candidates = self.actor.get_valid_targets()
        portals = [c for c in candidates if c.has_trait("portal")]
        if len(portals) == 0:
            return FailAction(self.actor, "There are no exits from here.")
        elif len(portals) == 1:
            return Enter(self.actor, portals[0])
        else:
            exits = [p for p in portals if p.has_name("exit")]
            if len(exits) == 1:
                return Enter(self.actor, exits[0])
            else:
                return FailAction(self.actor, "There are multiple exits.")


class DurationWaitRoutine(Routine, ZeroTargetAction):
    synonyms = ["wait", "delay"]

    class VerbClass(Verb):
        match_strings = ["VERB for DURATION",
                         "VERB DURATION"]

    def __init__(self, *args, **kwargs):
        self.duration = kwargs.pop("duration")
        self.expended_duration = 0
        super().__init__(*args, **kwargs)

    def get_local_action(self):
        if self.expended_duration < self.duration - 1:
            self.expended_duration += 1
            return Wait(self.actor)
        elif self.expended_duration < self.duration:
            self.expended_duration += 1
            return LoudWait(self.actor)
        else:
            return None


class AttackHeroRoutine(Routine, ZeroTargetAction):
    def get_local_action(self):
        try:
            victim_set = self.actor.location.things_with_trait("hero")
            victim = next(iter(victim_set))
        except StopIteration:
            self.complete = True
            return None
        else:
            rout = DefaultStrikeRoutine(self.actor, victim)
            return self.start_routine(rout)


class WanderOnceRoutine(SingleActionRoutine, ZeroTargetAction):
    def get_single_action(self):
        portals = self.actor.location.things_with_trait("portal")
        if portals:
            portal_list = list(portals)
            portal = choice(portal_list)
            return Enter(self.actor, portal)
        else:
            return None


class DestinationRoutine(ActionListRoutine, ZeroTargetAction):
    home_node = None
    map_ = None

    def build_portal_list(self):
        raise NotImplementedError

    def build_action_list(self):
        portal_list = self.build_portal_list()
        return [Enter(self.actor, portal) for portal in portal_list]


class WalkToEntranceRoutine(DestinationRoutine):
    # def build_portal_list(self):
    #     return self.map_.path_to_entrance(self.home_node)

    def build_portal_list(self):
        try:
            return self.actor.location.path_to_entrance()
        except AttributeError:
            print(f"Warning: no path from {self.actor.location}")
            return []


class LeaveDungeonRoutine(Routine, ZeroTargetAction):
    def get_local_action(self):
        act = self.start_routine(WalkToEntranceRoutine(self.actor))
        if act:
            return act
        if self.actor.location.has_trait("wide"):
            debug("ACTOR FLED TO WILDERNESS")
            return WildernessFlee(self.actor)
        game_exits = self.actor.location.things_with_name("exit")
        if game_exits:
            exit = next(iter(game_exits))
            return Enter(self.actor, exit)
        self.complete = True
        return None


class WalkToLocationRoutine(DestinationRoutine):
    def __init__(self, destination=None, *args, **kwargs):
        self.destination = destination
        super().__init__(*args, **kwargs)

    # def build_portal_list(self):
    #     return self.map_.path_to_location(self.actor.location, self.destination)

    def build_portal_list(self):
        return self.actor.location.path_to_location(self.destination)


class WalkToRandomRoutine(DestinationRoutine):
    # def build_portal_list(self):
    #     return self.map_.path_to_random(self.home_node)

    def build_portal_list(self):
        return self.actor.location.wander_destination()


class DirectionMoveRoutine(SingleActionRoutine, ZeroTargetAction):
    synonyms = ["move", "go", "walk"]

    class VerbClass(Verb):
        match_strings = ["VERB DIRECTION", "DIRECTION"]

    def __init__(self, *args, **kwargs):
        self.direction = kwargs.pop("direction")
        super().__init__(*args, **kwargs)

    def get_single_action(self):
        if self.actor.coordinates and self.direction.vector is not None:
            return VectorTravel(self.actor, vector=self.direction.vector)

        found_portal = None
        for portal in self.actor.get_valid_targets():
            if (
                    portal.has_trait("portal") and
                    portal.get_relative_direction(self.actor) == self.direction
            ):
                found_portal = portal
                break
        if found_portal:
            return Enter(self.actor, found_portal)
        else:
            return None

    def reason_for_empty(self):
        return "There is no exit facing {}.".format(self.direction.name)


class LandmarkTravelRoutine(Routine, ZeroTargetAction):
    priority = 15
    synonyms = ["travel", "walk", "go"]

    class VerbClass(Verb):
        match_strings = ["VERB to? LANDMARK"]

    def __init__(self, *args, landmark, **kwargs):
        self.landmark = landmark
        super().__init__(*args, **kwargs)
        self.displacement = landmark.vector_from_thing(self.actor)
        if self.displacement:
            self.steps_taken = 0
            norm_square = sum(x ** 2 for x in self.displacement)
            if norm_square > 1:
                norm = sqrt(norm_square)
                self.step = tuple(x / norm for x in self.displacement)
                self.steps_needed = floor(norm)
            else:
                self.steps_needed = 0
        else:
            self.complete = True

    def get_local_action(self):
        if self.complete:
            return None

        if self.steps_taken < self.steps_needed:
            self.steps_taken += 1
            vector = self.step
            quiet = True
        else:
            self.complete = True
            vector = self.landmark.vector_from_thing(self.actor)
            quiet = False
        return VectorTravel(self.actor, quiet=quiet, vector=vector)


if __name__ == "__main__":
    import actor
    import game_object

    place = location.Location()
    dude = actor.Hero(location=place)
    key = game_object.Item(location=dude, name="key")
    cage = game_object.Cage(location=place, name="cage", key=key)
    prisoner = actor.Prisoner(location=place)
    cage.add_prisoner(prisoner)
    tar = TakeAllRoutine(dude)
    u = Unlock(dude, cage, key)
    prisoner.hear_announcement(u)
    # print(dude.get_action())
    # print(tar.action_list)
    # tar.attempt()
    # print(dude.get_action())
