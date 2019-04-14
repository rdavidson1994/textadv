import game_object, action, spells


class Rune(game_object.Thing):
    def __init__(self, *args, spell=None, mana_bonus=5, **kwargs):
        super().__init__(*args, **kwargs)
        if spell is None:
            spell = spells.get_random_spell()
        self.spell = spell
        self.mana_bonus = mana_bonus
        self.actors_affected = set()
        self.traits.add("interesting")

    def be_targeted(self, act):
        outcome, text = super().be_targeted(act)
        if outcome and isinstance(act, action.Examine):
            if act.actor not in self.actors_affected:
                act.actor.learn_spell(self.spell)
                act.actor.increase_max_mana(self.mana_bonus)
                self.actors_affected.add(act.actor)
        return outcome, text
