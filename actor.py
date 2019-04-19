import game_object
import body
import parsing
import ai
import schedule
import errors
from logging import debug
from random import random, randint, triangular
from name_object import Name


class Actor(game_object.Thing):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.physical = False
        self.awake = True
        self.alive = True
        self.traits.update({"actor", "listener"})
        self.scheduled_event = None
        self.ai = None
        self.actor_strategy_dict = dict()
        # self.action_queue = list()
        self.timer = 0

        assert self.schedule is not None or self.location is None
        # upon creation, actors in the world should have a schedule
        if self.schedule:
            self.schedule.add_actor(self)
        self.free_action = True

    def attempt_action(self, action):
        # Many side effects! action.attempt later causes action.affect game
        assert action.actor == self  # Can't attempt another's action
        valid, explanation = action.is_valid()
        if valid:
            action.attempt()
        else:
            self.receive_action_feedback(False, explanation)

    def final_action_check(self, action):
        if action.is_social:
            return self.ai.final_transaction_check(action)
        else:
            return True, ""

    def change_location(
        self, new_location, coordinates=None, keep_arranged=False
    ):
        # This is pretty slow! Probably don't do this
        assert self.schedule is not None
        super().change_location(new_location, coordinates, keep_arranged)
        for item in new_location.things:
            if new_location.line_of_sight(self, item):
                self.ai.see_thing(item)

    def change_coordinates(self, new_coordinates, keep_arranged=False):
        self.change_location(self.location, new_coordinates, keep_arranged)

    def move_to(self, other):
        assert self.location == other.location
        self.change_coordinates(other.coordinates)

    def vanish(self):
        self.schedule.remove_actor(self)
        super().vanish()

    def materialize(self, location, coordinates=None):
        self.schedule = location.schedule
        self.schedule.add_actor(self)
        super().materialize(location, coordinates)

    def cancel_actions(self):
        self.schedule.cancel_actions(self)

    def set_routine(self, routine):
        self.ai.set_routine(routine)

    def special_actor_effects(self, action):
        debug("Special actor effects performed")
        return True, ""

    def receive_action_feedback(self, success, string):
        pass

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

    def get_action(self):
        return self.ai.get_action()

    def receive_text_message(self, text):
        pass

    def set_timer(self, time, keyword):
        self.schedule.set_timer(self, time, keyword)

    def set_callback_timer(self, time, callback):
        self.schedule.set_timer(self, time, callback=callback)

    def hear_timer(self, keyword):
        pass

    def is_hostile_to(self, other):
        return self.ai.is_hostile_to(other)


class Person(Actor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.physical = True
        self.combat_skill = 50
        self.known_landmarks = set()
        self.body = body.Body(self)
        self.spells_known = set()
        self.traits.add("person")
        self.get_health_report = self.body.get_health_report
        self.money = 0

    def hear_announcement(self, action):
        self.ai.hear_announcement(action)

    def view_location(self):
        self.ai.display(self.location.describe(self, full_text=True))

    def get_look_text(self, viewer=None):
        out = super().get_look_text()+":\n"
        out += self.get_health_report(viewer=viewer)+"\n"
        if self.things:
            out += "Inventory:\n"
            out += "\n".join([i.get_name(viewer) for i in self.things])
        return out

    def increase_max_mana(self, amt):
        self.body.max_mana += amt
        self.set_body_timer()

    def take_damage(self, amt, damage_type):
        self.body.take_damage(amt, damage_type)

    def notice_damage(self, amt, typ):
        self.ai.notice_damage(amt, typ)

    def take_ko(self, amt):
        self.body.take_ko(amt)

    def __repr__(self):
        return "Person({})".format(self.name)

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
        game_object.Item(
            location=self.location,
            name=self.name_object+Name("head")
        )

    def pass_out(self, show_message=True):
        if self.awake:
            if show_message:
                message = self.name + " falls unconscious."
                self.location.show_text_to_hero(message)
            self.awake = False
            self.cancel_actions()

    def hear_timer(self, keyword):
        if keyword == "body update":
            self.body.update()
        else:
            super().hear_timer(keyword)

    def learn_spell(self, spell):
        self.spells_known.add(spell)
        self.receive_text_message(
            f"You learn the \"{spell.synonyms[0]}\" spell"
        )

    def wake_up(self):
        self.location.show_text_to_hero(self.name + " wakes up.")
        self.awake = True
        self.cancel_actions()

    def die(self, damage_amount=0, damage_type=None):
        self.pass_out(show_message=False)
        self.create_corpse()
        if damage_type == "sharp":
            if damage_amount >= 80 and random() > 0.5:
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
        self.alive = False
        self.vanish()

    def reset_body(self):
        self.body.reset()

    def full_rest(self):
        self.body.full_rest()

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

    def set_body_timer(self):
        self.schedule.set_timer(self, 500, "body update")

    def is_hero(self):
        return False

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
            self.awake and getattr(action, "is_physical_attack", False)
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
            raise Exception  # Need to specify a valid kind
        if name in ("self", "myself", "yourself"):
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

    def get_name(self, viewer=None):
        if viewer == self:
            output = "you"
        else:
            output = super().get_name(viewer)
        if not self.awake:
            output += " (unconscious)"
        return output


class WaitingActor(Person):
    def __init__(self, *args, **kwargs):
        Person.__init__(self, *args, **kwargs)
        self.ai = ai.AI(self)


class Prisoner(Person):
    def __init__(self, *args, **kwargs):
        Person.__init__(self, *args, **kwargs)
        self.ai = ai.PrisonerAI(self)


class SquadActor(Person):
    def __init__(self, *args, **kwargs):
        Person.__init__(self, *args, **kwargs)
        self.ai = ai.SquadAI(self)


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
