from typing import Tuple
from action import SingleTargetAction, ZeroTargetAction, Action
from random import randint, choice
from verb import StandardVerb
import trait
from game_object import Thing


class Spell(Action):
    class VerbClass(StandardVerb):
        match_strings = [
            "cast? VERB",
            "cast? VERB on? TARGET",
            "cast? VERB on? TARGET with TOOL",
        ]

        def match_quality(self, i):
            if i == 3:
                return "bad"
            else:
                return super().match_quality(i)

    stamina_cost = 5

    def expend_components(self, dry_run : bool):
        return (True, "")

    def is_valid(self):
        try:
            known = (type(self) in self.actor.spells_known)
        except AttributeError:
            known = False
        if not known:
            return False, "You don't know that spell."
        (components_okay, explanation) = self.expend_components(
            dry_run=True
        )
        if not components_okay:
            return False, explanation
        if self.mana_cost > self.actor.body.mana:
            return False, "You don't have enough mana."
        return super().is_valid()

    def get_name(self, viewer=None):
        out = "cast" + self.possible_s(viewer) + " " + self.synonyms[0]
        if len(self.target_list) > 0:
            out += " on"
        return out
    
    def spell_effect(self):
        pass
    
    def affect_game(self):
        self.expend_components(
            dry_run=False
        )
        self.spell_effect()
    

class InvalidSpell(Spell, ZeroTargetAction):
    synonyms = ["hocus pocus"]

    class VerbClass(StandardVerb):
        match_strings = ["cast NONSENSE"]

        def match_quality(self, i):
            return "bad"


class Heal(Spell, SingleTargetAction):
    synonyms = ["heal"]
    mana_cost = 40
    target_traits = [trait.person]

    
    def expend_components(self, dry_run : bool) -> Tuple[bool, str]:
        meat = None
        for item in self.actor.things_with_trait(trait.meat):
            meat = item
            break
        
        if meat is None:
            return False, "You have no meat to use for the spell."

        if not dry_run:
            item.vanish()
        return (True, "")

    def spell_effect(self):
        self.target.reset_body()


class Shock(Spell, SingleTargetAction):
    synonyms = ["shock"]
    mana_cost = 25

    def spell_effect(self):
        self.target.take_damage(randint(75, 125), "lightning", perpetrator=self.actor)


class Blade(Spell, SingleTargetAction):
    synonyms = ["blade"]
    mana_cost = 30

    def spell_effect(self):
        self.target.take_damage(randint(75, 125), "sharp", perpetrator=self.actor)


class Knock(Spell, SingleTargetAction):
    synonyms = ["knock"]
    mana_cost = 30

    def spell_effect(self):
        self.target.take_damage(randint(50, 100), "blunt", perpetrator=self.actor)


class AOESpell(Spell, ZeroTargetAction):
    affects_caster = False

    def spell_effect(self):
        for actor in self.actor.location.things_with_trait(trait.actor):
            if actor != self.actor or self.affects_caster:
                self.affect_object_in_range(actor)

    def affect_object_in_range(self, other):
        pass


class Sleep(AOESpell):
    synonyms = ["sleep"]
    mana_cost = 35

    def affect_object_in_range(self, other):
        duration = randint(20, 30)
        other.take_ko(duration)


class Fireball(AOESpell):
    synonyms = ["fireball", "fire ball"]
    mana_cost = 40

    def affect_object_in_range(self, other):
        damage = randint(50, 100)
        other.take_damage(damage, "fire", perpetrator=self.actor)


class ShockWave(AOESpell):
    synonyms = ["shockwave", "shock wave"]
    mana_cost = 30

    def affect_object_in_range(self, other):
        damage = randint(30, 75)
        other.take_damage(damage, "blunt", perpetrator=self.actor)


def get_random_spell():
    # placeholder, should have procgen later
    return choice([
        Sleep,
        Fireball,
        Shock,
        Blade,
        Knock,
        Heal,
    ])

