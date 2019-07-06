from enum import Enum, auto
import random


class BonusType(Enum):
    attack_onset_multiplier = auto()
    attack_cooldown_multiplier = auto()
    attack_skill_multiplier = auto()
    parry_skill_multiplier = auto()
    attack_fatigue_multiplier = auto()
    parry_fatigue_multiplier = auto()


class Posture:
    pass


class Stance(Posture):
    pass


class Guard(Posture):
    pass


def random_posture():
    pass
