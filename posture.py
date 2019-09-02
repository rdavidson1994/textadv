from enum import Enum, auto
from typing import Dict, Optional

import namemaker
from name_object import Name
import random


class BonusType(Enum):
    attack_onset_divisor = auto()
    attack_cooldown_divisor = auto()
    attack_skill_multiplier = auto()
    parry_skill_multiplier = auto()
    attack_damage_multiplier = auto()
    attack_fatigue_divisor = auto()
    parry_fatigue_divisor = auto()


bonus_representation = {
    BonusType.attack_onset_divisor:
        "Attack speed {x:.0%}",
    BonusType.attack_cooldown_divisor:
        "Attack recovery speed {x:.0%}",
    BonusType.attack_skill_multiplier:
        "Attack accuracy {x:.0%}",
    BonusType.parry_skill_multiplier:
        "Parry accuracy {x:.0%}",
    BonusType.attack_damage_multiplier:
        "Attack damage {x:.0%}",
    BonusType.attack_fatigue_divisor:
        "Attack stamina efficiency {x:.0%}",
    BonusType.parry_fatigue_divisor:
        "Parry stamina efficiency {x:.0%}",
}


class Posture:
    def __init__(self, multipliers: Dict[BonusType, float], name: Name):
        self.multipliers = dict(multipliers)
        self.name = name
        self.easy_parry_effect = None
        self.easy_parry_duration = 0
        self.near_hit_effect = None
        self.near_hit_duration = 0

    def get_name(self, viewer=None):
        return self.name.get_text(viewer)

    def get_summary_lines(self, viewer=None):
        out_lines = []
        out_lines.extend(
            "    "+bonus_representation[m].format(x=self.multipliers[m])
            for m in self.multipliers
        )
        cases = (
            (
                self.easy_parry_effect,
                self.easy_parry_duration,
                "On easy parries, attacker gets:"
            ),
            (
                self.near_hit_effect,
                self.near_hit_duration,
                "On near hits, defender gets:"
            )
        )
        for effect, duration, description in cases:
            if effect:
                out_lines.append(
                    "    "+description
                )
                out_lines.extend(
                    "    "+line for line in effect.get_summary_lines(viewer)
                )
                out_lines.append(f"        for {duration/1000} seconds")
        return out_lines

    def get_summary(self, viewer=None):
        out = [self.get_name(viewer)+":"]
        out.extend(self.get_summary_lines(viewer))
        return "\n".join(out)

    @classmethod
    def get_default(cls):
        raise NotImplementedError

    def get_multiplier(self, bonus_type: BonusType):
        if not isinstance(bonus_type, BonusType):
            raise TypeError
        if bonus_type in self.multipliers:
            return self.multipliers[bonus_type]
        else:
            return 1.0


class Stance(Posture):
    @classmethod
    def get_default(cls):
        return cls({}, Name("neutral stance"))


class Guard(Posture):
    @classmethod
    def get_default(cls):
        return cls({}, Name("neutral guard"))


def random_debuff(derived_name):
    malus = random.choice(list(BonusType))
    multiplier = random.choice((0.75, 0.5))
    debuff = Posture(
        multipliers={malus: multiplier},
        name=derived_name,
    )
    return debuff


def random_posture(posture_type=None):
    if posture_type is None:
        posture_type = random.choice([Stance, Guard])
    type_name = {Stance: "stance", Guard: "guard"}[posture_type]
    name = namemaker.make_name()+type_name
    bonus, malus = random.sample(list(BonusType), 2)
    multipliers = {bonus: 1.30, malus: 0.75}
    posture = posture_type(
        name=name,
        multipliers=multipliers
    )
    if random.random() < 0.5:
        derived_name = "temporary effect from" + name
        debuff = random_debuff(derived_name)
        duration = random.randint(2, 5)*1000
        if random.random() < 0.5:
            posture.easy_parry_duration = duration
            posture.easy_parry_effect = debuff
        else:
            posture.near_hit_duration = duration
            posture.near_hit_effect = debuff
    return posture


if __name__ == "__main__":
    p = random_posture()
    print(p.get_summary())
