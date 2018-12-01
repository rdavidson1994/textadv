import game_object
import body
import parsing
import ai
import schedule
import errors
from logging import debug
from random import random, randint, triangular
from game_object import Name


class Actor(game_object.Thing):
    def __init__(self, *args, **kwargs):
        game_object.Thing.__init__(self, *args, **kwargs)
        self.traits.update({"actor", "listener"})
        self.scheduled_event = None
        self.ai = None
        self.awake = True
        self.combat_skill = 50
        self.known_landmarks = set()
        self.body = body.Body(self)
        self.actor_strategy_dict = dict()
        # self.action_queue = list()
        self.timer = 0
        if self.schedule is None:
            self.schedule = schedule.DefaultSchedule()

        self.schedule.add_actor(self)
        self.free_action = True
        self.money = 0  # TODO: Abstract this out

    def attempt_action(self, action):
        # Many side effects! action.attempt later causes action.affect game
        assert action.actor == self # Can't attempt another's action
        valid, explanation = action.is_valid()
        if valid:
            action.attempt()
        else:
            self.receive_action_feedback(False, explanation)
            print("Invalid action stopped")

    def final_action_check(self, action):
        if action.is_social:
            return self.ai.final_transaction_check(action)
        else:
            return True, ""

    def announce(self, action):
        if getattr(action, "traverses_portals", False):
            for loc in (action.target.location,
                        action.target.opposite().location):
                if loc:
                    loc.broadcast_announcement(action)
        elif self.location:
            self.location.broadcast_announcement(action)
        else:
            pass

    def vanish(self):
        self.schedule.remove_actor(self)
        super().vanish()

    def cancel_actions(self):
        self.schedule.cancel_actions(self)

    def special_actor_effects(self, action):
        debug("Special actor effects performed")
        return True, ""

    def receive_action_feedback(self, success, string):
        pass

    def perform_action(self, action):
        action_ok, explanation = self.special_actor_effects(action)
        if action_ok:
            # If the action is allowed, lets the action instance do its thing.
            return action.attempt()
        else:
            return False, explanation

    def get_action(self):
        return self.ai.get_action()


class Person(Actor):

    def hear_announcement(self, action):
        self.ai.hear_announcement(action)

    def view_location(self):
        self.ai.display(self.location.describe(self, full_text=True))

    def is_hostile_to(self, other):
        return self.ai.is_hostile_to(other)

    def get_name(self, viewer=None):
        if viewer == self:
            output = "you"
        else:
            output = super().get_name(viewer)
        if not self.awake:
            output += " (unconscious)"
        return output

    def get_look_text(self, viewer=None):
        out = super().get_look_text()
        if self.things:
            out += "\nInventory:\n"
            out += "\n".join([i.get_name(viewer) for i in self.things])
        return out

    def receive_text_message(self, text):
        pass

    def change_location(self, new_location, coordinates=None,
                        keep_arranged=False):
        # This is pretty slow! Probably don't do this
        super().change_location(new_location, coordinates, keep_arranged)
        for item in new_location.things:
            if new_location.line_of_sight(self,item):
                self.ai.see_thing(item)

    def take_damage(self, amt, damage_type):
        self.body.take_damage(amt, damage_type)

    def notice_damage(self, amt, typ):
        self.ai.notice_damage(amt, typ)

    def take_ko(self, amt):
        self.body.take_ko(amt)

    def __repr__(self):
        return "Actor({})".format(self.name)

    def create_corpse(self):
        corpse = game_object.Container(
            location=self.location,
            name=self.name + "'s corpse",
            other_names=[self.name + "s corpse", "corpse", self.name]
        )
        corpse.traits.add("corpse")
        corpse.owner = self
        for item in set(self.things):
            item.change_location(corpse)

    def create_head(self):
        adjectives = [self.name]
        if self.name_object:
            adjectives += self.name_object.nouns+self.name_object.adjectives
        game_object.Item(location=self.location,
                         name=Name(adjectives,
                             "head"))

    def pass_out(self):
        if self.awake:
            self.location.show_text_to_hero(self.name + " falls unconscious.")
            self.awake = False
            self.cancel_actions()

    def wake_up(self):
        self.location.show_text_to_hero(self.name + " wakes up.")
        self.awake = True
        self.cancel_actions()

    def die(self, damage_ammount=0, damage_type=None):
        self.create_corpse()
        if damage_type == "sharp":
            if damage_ammount >= 80 and random() > 0.5:
                text = self.name + " is decapitated."
                self.create_head()
            else:
                text = self.name + " has been chopped to death."
        elif damage_type == "bleed":
            text = self.name + " has bled to death."
        elif damage_type == "blunt":
            text = self.name + " has been beaten to death."
        else:
            text = self.name + " has died."
        self.location.show_text_to_hero(text)
        self.vanish()

    def get_fatigue_multiplier(self, decay_rate=0.008):
        x = self.body.get_total_fatigue()
        a = decay_rate
        return 1 / (1 + a * (x ** 2))

    def get_attack_roll(self, weapon=None, min_=False):
        modifier = self.combat_skill * self.get_fatigue_multiplier(.00005)
        if min_:
            return modifier
        return randint(0, 30) + modifier

    def get_parry_roll(self, min_=False):
        modifier = self.combat_skill * self.get_fatigue_multiplier(.00020)
        if min_:
            return modifier
        return triangular(0, 80) + modifier

    def set_timer(self, time, keyword):
        self.schedule.set_timer(self, time, keyword)

    def set_body_timer(self):
        self.schedule.set_timer(self, 500, "body update")

    def hear_timer(self, keyword):
        if keyword == "body update":
            self.body.update()

    def is_hero(self):
        return False

    def set_routine(self, routine):
        self.ai.set_routine(routine)

    def can_reach(self, target):
        if self.has_thing(target):
            return True
        elif self.location.has_nested_thing(target) or self.has_thing(target):
            return self.location.line_of_sight(self, target)
        else:
            return False

    def be_targeted(self, action):
        if action.is_social:
            if self.awake:
                return self.ai.social_response(action)
            else:        
                return False, "You cannot speak to an unconscious person."

        elif (
                self.awake
                and getattr(action, "is_physical_attack", False)
        ):
            name = action.actor.get_identifier(self)
            parry_roll = self.get_parry_roll()
            if parry_roll >= 2 * action.attack_roll:
                self.ai.display("You easily parry " + name)
                self.body.take_fatigue(3)
                return False, "Your attack is easily parried."
            elif parry_roll >= 1.3 * action.attack_roll:
                self.body.take_fatigue(6)
                self.ai.display("You parry " + name)
                return False, "Your attack is parried."
            elif parry_roll >= action.attack_roll:
                self.body.take_fatigue(9)
                self.ai.display("You barely parry " + name)
                return False, "Your attack is barely parried."
            else:
                self.body.take_fatigue(9)
                self.ai.display("You fail to parry " + name)
        return super().be_targeted(action)

    def find_portal_facing_direction(self, direction):
        for portal in self.location.things_with_trait("portal"):
            if portal.get_relative_direction(self) == direction:
                return portal
        else:
            raise errors.PortalNotFound

    def get_targets_from_name(self, name, kind="TARGET"):
        if kind == "TARGET":
            candidates = self.get_valid_targets()
        elif kind == "LANDMARK":
            candidates = self.known_landmarks
        else:
            raise Exception # Need to specify a valid kind
        if name in ("self","myself","yourself"):
            return [x for x in candidates if x == self]
        else:
            return [x for x in candidates if x.has_name(name)]

    def get_targets_from_trait(self, trait):
        return [x for x in self.get_valid_targets() if x.has_trait(trait)]

    def get_valid_targets(self):
        return self.things | self.location.get_interactables(self)

    def spend_time(self, time_spent):
        pass

    def agrees_to(self, own_action):
        assert own_action.actor == self
        return self.ai.agrees_to(own_action)

    def offer_price(self, other, item):
        return self.ai.offer_price(other, item)

    def get_suggested_verbs(self):
        return "attack", "examine"


class WaitingActor(Person):
    def __init__(self, *args, **kwargs):
        Person.__init__(self, *args, **kwargs)
        self.ai = ai.AI(self)


class Prisoner(Person):
    def __init__(self, *args, **kwargs):
        Person.__init__(self, *args, **kwargs)
        self.ai = ai.PrisonerAI(self)


class KoboldActor(Person):
    def __init__(self, *args, **kwargs):
        Person.__init__(self, *args, **kwargs)
        self.ai = ai.KoboldAI(self)
        self.traits.add("kobold")


class Hero(Person):
    def __init__(self, *args, **kwargs):
        Person.__init__(self, *args, **kwargs)
        self.traits.add("hero")
        self.ai = parsing.Parser(self)
        self.visited_locations = set()
        self.combat_skill = 100

    def get_article(self, viewer=None, definite=False):
        return " "

    def get_identifier(self, viewer=None):
        return self.get_name(viewer)

    def die(self, amt=0, typ=None):
        self.schedule.stop_game()
        super().die(amt, typ)

    def receive_text_message(self, text):
        self.ai.display(text)

    def receive_action_feedback(self, success, string):
        self.ai.display(string)

    def change_location(self, new_location, coordinates=None,
                        keep_arranged=False):
        super().change_location(new_location, coordinates)

    def is_hero(self):
        """check if the actor is commanded by the player.
        If this returns true, you are expected to be of the Hero class,
        and expected to have a self.ai != None.
        """
        return True
