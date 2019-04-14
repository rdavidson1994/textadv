from action import SingleTargetAction, ZeroTargetAction, Action
from random import randint, choice
from verb import StandardVerb


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

    def is_valid(self):
        try:
            known = (type(self) in self.actor.spells_known)
        except AttributeError:
            known = False
        if not known:
            return False, "You don't know that spell."
        elif self.mana_cost > self.actor.body.mana:
            return False, "You don't have enough mana."
        else:
            return super().is_valid()

    def get_name(self, viewer=None):
        out = "cast" + self.possible_s(viewer) + " " + self.synonyms[0]
        if len(self.target_list) > 0:
            out += " on"
        return out


class InvalidSpell(Spell, ZeroTargetAction):
    synonyms = ["hocus pocus"]

    class VerbClass(StandardVerb):
        match_strings = ["cast NONSENSE"]

        def match_quality(self, i):
            return "bad"


class Heal(Spell, SingleTargetAction):
    synonyms = ["heal"]
    mana_cost = 40
    target_traits = ["person"]

    def affect_game(self):
        self.target.reset_body()


class Shock(Spell, SingleTargetAction):
    synonyms = ["shock"]
    mana_cost = 25

    def affect_game(self):
        self.target.take_damage(randint(75, 125), "lightning")


class Blade(Spell, SingleTargetAction):
    synonyms = ["blade"]
    mana_cost = 30

    def affect_game(self):
        self.target.take_damage(randint(75, 125), "sharp")


class Knock(Spell, SingleTargetAction):
    synonyms = ["knock"]
    mana_cost = 30

    def affect_game(self):
        self.target.take_damage(randint(50, 100), "blunt")


class AOESpell(Spell, ZeroTargetAction):
    affects_caster = False

    def affect_game(self):
        for actor in self.actor.location.things_with_trait("actor"):
            if actor != self.actor or self.affects_caster:
                self.spell_effect(actor)

    def spell_effect(self, other):
        pass


class Sleep(AOESpell):
    synonyms = ["sleep"]
    mana_cost = 35

    def spell_effect(self, other):
        duration = randint(20, 30)
        other.take_ko(duration)


class Fireball(AOESpell):
    synonyms = ["fireball", "fire ball"]
    mana_cost = 40

    def spell_effect(self, other):
        damage = randint(50, 100)
        other.take_damage(damage, "fire")


class ShockWave(AOESpell):
    synonyms = ["shockwave", "shock wave"]
    mana_cost = 30

    def spell_effect(self, other):
        damage = randint(30, 75)
        other.take_damage(damage, "blunt")


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

