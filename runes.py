import game_object, action, spells


class Rune(game_object.Thing):
    def __init__(self, *args, spell=None, mana_bonus=10, **kwargs):
        if spell is None:
            spell = spells.get_random_spell()
        self.spell = spell
        self.mana_bonus = 5
        self.actors_affected = set()
        super().__init__(*args, **kwargs)

    def be_targeted(self, act):
        if isinstance(act, action.Examine):
            if act.actor not in self.actors_affected:
                act.actor.learn_spell(self.spell)
                act.actor.increase_max_mana(self.mana_bonus)

        return super().be_targeted(act)