import errors
import menu_wrap
import phrase
import string
import re
import json
import action
from ai import AI
from logging import debug


class Parser(AI):
    def __init__(self, *args, **kwargs):
        AI.__init__(self, *args, **kwargs)
        self.display_queue = []
        self.special_phrases = []
        self.routine = None
        self.web_output = False
        self.visited_locations = set()
        self.end_game = False
        self.verbose = False
        self.logged_input = None
        self.logged_action = None
        self.last_interrupt_request = None

    def display(self, display_string):
        # self.display_queue.append(display_string)
        if display_string != "SILENCE":
            output = display_string  # .capitalize()
            if self.web_output:
                output = output.replace("\n", "<br />\n")
                output = output.replace(menu_wrap.web_new_line, "\n")
                print(output, end="<br />\n")
            else:
                print(output)

    def close(self):
        self.end_game = True
        return "Ending game."

    def seek_clarification(self, possibility_list, name):
        s = ('There are multiple things called \"{name}\"'
             ' here. Which one do you mean?').format(name=name)
        self.display(s)
        new_name = self.input()
        new_list = self.actor.get_targets_from_name(new_name)
        if new_list:
            return [i for i in possibility_list if i in new_list]
        else:
            # If the input doesn't make sense as a name, try it as a new command
            self.logged_input = new_name
            return []

    def get_local_action(self):
        if self.logged_action is None:
            return self.execute_user_input()
        else:
            out = self.logged_action
            self.logged_action = None
            return out

    def see_thing(self, thing):
        if thing.has_trait("portal") and thing.landmark:
            self.actor.known_landmarks.add(thing.landmark)

    def agrees_to(self, own_action):
        if isinstance(own_action, action.Sell):
            m = own_action.target.get_name(self.actor)
            p = own_action.proposed_price
            self.display("{} offers you {}. Do you accept? (Y/N)".format(m,p))
            inp = self.input()
            if inp in {"y", "yes"}:
                return True
            else:
                return False
        else:
            return super().agrees_to(own_action)

    def ask_for_interrupt(self):
        decision_made = False

        while not decision_made:
            self.display("Interrupt your action? (Y/N)")
            inp = self.input()
            if inp in {"y", "yes"}:
                self.routine = None
                self.cancel_actions()
                decision_made = True
            elif inp in {"n", "no", ""}:
                decision_made = True
            else:
                new_action = self.execute_string(inp)
                if new_action.is_instant:
                    self.actor.attempt_action(new_action)
                    decision_made = False
                else:
                    self.logged_action = new_action
                    self.routine = None
                    self.cancel_actions()
                    decision_made = True

    def hear_announcement(self, action):
        # TODO: Update this to use the taking_hostile_action method
        super().hear_announcement(action)
        if action.actor == self.actor:
            if (
                    action.moves_actor()
                    and not action.quiet
            ):
                new_location = self.actor.location
                if self.verbose or new_location not in self.visited_locations:
                    full_text = True
                else:
                    full_text = False
                out = new_location.describe(self.actor, full_text)
                self.visited_locations.add(new_location)
                self.display(out)

        elif self.actor.awake:
            text = action.get_success_string(viewer=self.actor)
            self.display(text)
            my_action = self.get_current_action()
            conds = (my_action is not None,
                     self.last_interrupt_request != my_action,
                     text != "SILENCE",
                     not self.taking_hostile_action(),)
            if all(conds):
                self_hostile = getattr(my_action, "is_hostile", False)
                # we shouldn't ask to interrupt the player's attacks.
                if not self_hostile and action.actor.is_hostile_to(self.actor):
                    self.last_interrupt_request = my_action
                    self.ask_for_interrupt()

    def input(self):
        if self.web_output:
            prompt = json.dumps({"type": "output complete"})+"\n"
        else:
            prompt = ">"
        output = input(prompt).lower()
        # for ch in string.punctuation:
        #     output = output.replace(ch, "")
        output = output.replace(" the ", " ")
        return output

    def match_things_to_names(self, names):
        return [self.match_thing_to_name(name) for name in names]

    def match_thing_to_name(self, name, kind="TARGET"):
        if kind == "TARGET" or kind == "LANDMARK":
            lst = self.actor.get_targets_from_name(name, kind)
        else:
            raise Exception
        while len(lst) > 1:
            lst = self.seek_clarification(lst, name)
        if len(lst) == 1:
            return lst[0]
        else:
            if not self.logged_input:
                if kind == "TARGET":
                    self.display("There is no {} here".format(name))
                elif kind == "LANDMARK":
                    self.display("You don't know any place called "+name+".")
            raise errors.NoMatchingObject

    def match_landmark_to_name(self, name):
        return self.match_thing_to_name(name, kind="LANDMARK")

    def invalid_action_fallback(self, failed_action):
        from action import NullAction
        failure_string = failed_action.is_valid()[1]
        self.display(failure_string)
        return NullAction(self.actor)

    def execute_user_input(self):
        return self.execute_string(self.input())

    def execute_string(self, input_string):
        for ph in self.special_phrases:
            if ph.matches(input_string):
                self.display(ph.perform_action())
                return action.NullAction(self.actor)
        try:
            action_or_routine = action.match_action_to_string(self, input_string)
        except errors.NoMatchingObject:
            return action.NullAction(self.actor)
        else:
            if action_or_routine is None:
                template = "I don't know what \"{}\" means"
                self.display(template.format(input_string))
                return action.NullAction(self.actor)
            else:
                permission, explanation = action_or_routine.is_valid()
                if not permission:
                    self.display(explanation)
                    return action.NullAction(self.actor)
        if action_or_routine.is_routine():
            my_action = self.start_routine(action_or_routine)
            if my_action is None:
                reason = action_or_routine.reason_for_empty()
                if reason:
                    self.display(reason)
                else:
                    self.display("That doesn't make sense. Do something else.")
                return self.get_action()
            elif not my_action.is_valid()[0]:
                self.routine = None
                return self.invalid_action_fallback(my_action)
            else:
                return my_action
        else:
            return action_or_routine


if __name__ == "__main__":
    import game_object
    import actor

    loc = game_object.Location()
    dude = actor.Hero(loc)
    sword = game_object.Item(location=loc, name="sword", other_names=["iron sword"])
    bsword = game_object.Item(location=loc, name="sword", other_names=["bronze sword"])
    p = Parser(dude)
    print(p.execute_user_input())
