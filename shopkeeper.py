from location import Location
import ai
import actor
import action
import game_object
import agent
import population
import environment
import typing
import building
import trait
from typing import Optional


class ShopkeeperAI(ai.PeacefulAI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.customers_seen_today = set()
        self.held_merchandise = {}

    def actor_enters_location(self, act):
        if act.actor in self.customers_seen_today:
            greeting_text = "Welcome back!"
        else:
            greeting_text = "Welcome!"
            self.customers_seen_today.add(act.actor)
        if isinstance(self.get_current_action(), action.Wait):
            self.say(greeting_text, now=True)
        else:
            self.say(greeting_text, now=False)
        super().actor_enters_location(act)

    def actor_leaves_location(self, act):
        if act.actor in self.held_merchandise.values():
            self.enemies.add(act.actor)

    def social_response(self, act):
        if act.actor in self.enemies:
            template = "The {} will not speak to you."
            out_string = template.format(self.actor.get_name(act.actor))
            return False, out_string
        elif isinstance(act, action.Sell):
            item = act.tool
            if item.price is None:  # TODO: or item isn't sold by merchant
                return False, "That item has no monetary value."
            elif item.has_location(act.actor):
                return False, "You must put down the item to sell it."
            else:
                offer_price = item.price * 0.5
                if offer_price > self.actor.money:
                    offer_price = self.actor.money
                act.set_price(offer_price)
                return True, ""
        else:
            return super().social_response(act)

    def say(self, text, now=False):
        own_action = action.Speak(self.actor, text=text)
        self.set_action(own_action, now)

    def remove_merchandise(self, item):
        try:
            return self.held_merchandise.pop(item)
        except KeyError:
            return None

    def hear_announcement(self, act):
        if act.actor not in self.enemies:
            if isinstance(act, action.Take) and act.target.owner == self.actor:
                template = "A fine choice. And only {} gold!"
                self.say(template.format(act.target.price), now=True)
                self.held_merchandise[act.target] = act.actor
            if isinstance(act, action.Drop) and act.target.owner == self.actor:
                self.remove_merchandise(act.target)
                self.say("Acknowledged", now=True)
            if isinstance(act, action.Buy) and act.target == self.actor:
                self.remove_merchandise(act.tool)
                self.say("Thank you for your purchase!", now=True)
        super().hear_announcement(act)
            

class Person(actor.Person):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai = ShopkeeperAI(self)
        self.traits.add(trait.merchant())
        self.shop : Optional[Location] = None


if __name__ == "__main__":
    test = environment.Test()
    shop = building.WeaponShop(source_location=test.street,
                               sched=test.schedule)

    test.hero.money = 200
    test.run()
