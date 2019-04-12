from random import betavariate, randint, random
from math import floor, sqrt
try:
    from scipy.stats import norm
except ImportError:
#  on my work computer, scipy cannot be installed. This is a workaround.
    class norm:
        @staticmethod
        def ppf(alpha, loc, scale):
            return -15     


class Body:
    bleeds = True

    def __init__(self, owner):
        self.owner = owner
        self.short_fatigue = 0
        self.fatigue = 0
        self.max_mana = 0
        self.mana = 0
        self.damage = 0
        self.bleeding_damage = 0
        self.ko_time = 0
        self.stable = True  # if false, needs updates
        self.mana_regen_rate = 1

    def take_ko(self, amt):
        self.ko_time += amt
        if amt > 0:
            self.owner.pass_out()
            if self.stable:
                self.start_updating()

    def die(self, amt, typ):
        self.owner.die(amt, typ)

    def lose_mana(self, amt):
        # This one throws an error, because you got stuff for free
        self.mana -= amt
        assert (self.mana >= 0)

    def gain_mana(self, amt):
        # This one doesn't, because you just got less mana than possible
        prospective_mana = self.mana+amt
        if prospective_mana <= self.max_mana:
            self.mana = prospective_mana
        else:
            self.mana = self.max_mana

    def take_fatigue(self, amt):
        if amt > 0:
            self.fatigue += amt
            self.short_fatigue += 3 * amt
            if self.stable:
                self.start_updating()

    def get_total_fatigue(self):
        return floor((self.short_fatigue + self.fatigue) / 4)

    def get_health_report(self, viewer=None):
        out = self.get_damage_report(viewer=viewer)
        out += self.get_stamina_report(viewer=viewer)
        out += self.get_skill_report(viewer=viewer)

        if self.max_mana > 0:
            mana = "{}/{} mana remaining."
            out += mana.format(self.mana, self.max_mana)
        return out

    def get_skill_report(self, verbose=False, alpha=0.1, viewer=None):
        template = "Effective combat skill: {}\n"
        out = template.format(int(self.owner.get_attack_roll(weapon=None, min_=True)))
        mean = 80/2-30/2  # mean of parry roll - attack roll.
        sd = sqrt(30**2/12+2*40**2/12)
        margin_of_error = norm.ppf(alpha, loc=mean, scale=sd)
        template = "Most skilled opponent you can safely fight: {}\n"
        out += template.format(int(self.owner.get_parry_roll(min_=True) + margin_of_error))
        return out

    def get_damage_report(self, verbose=False, alpha=0.2, viewer=None):
        you = self.owner.get_identifier(viewer)
        out = ""
        if self.damage > 0 or verbose:
            if viewer == self.owner:
                have = "have"
                are = "are"
            else:
                have = "has"
                are = "is"

            left_bound = self.inv_ko_cdf(alpha / 2)
            right_bound = self.inv_ko_cdf(1 - alpha / 2)
            confidence = 100 * (1 - alpha)
            out += (
                f"{you} {have} {self.damage} damage. "
                "Expect to be knocked out between "
                f"{left_bound} and {right_bound}. ({confidence}% CI)\n"
            )
        if self.bleeding_damage:
            out += (
                f"{you} {are} bleeding at a rate of "
                f"{self.bleeding_damage} damage per second.\n"
            )
        return out

    def get_stamina_report(self, verbose=False, viewer=None):

        template = "Fatigue: {}. {} of this is short-term.\n"
        if self.get_total_fatigue() or verbose:
            out = template.format(self.get_total_fatigue(),
                                  floor(self.short_fatigue / 4))
        else:
            out = ""
        return out

    def take_damage(self, amt, typ):
        acute_damage = self.damage + amt * 3
        if amt >= 10 and typ == "sharp" and self.bleeds:
            self.bleeding_damage += floor(amt / 10)
            if self.stable:
                self.start_updating()
        if acute_damage >= 300:
            self.die(amt, typ)
        elif acute_damage > self.get_ko_cutoff():
            duration = randint(10, 15)
            self.take_ko(duration)
        self.damage += amt
        self.owner.notice_damage(amt, typ)

    def start_updating(self):
        self.stable = False
        self.owner.set_body_timer()

    def update(self):
        needs_update = False
        if self.ko_time:
            needs_update = True
            self.ko_time -= 1
            if self.ko_time <= 0:
                self.ko_time = 0
                if not self.owner.awake:
                    self.owner.wake_up()
        if self.bleeding_damage:
            needs_update = True
            self.take_damage(self.bleeding_damage, "bleed")
            if random() < 0.13:
                self.bleeding_damage -= 1
            if self.bleeding_damage <= 0:
                self.bleeding_damage = 0
        if self.short_fatigue:
            needs_update = True
            self.short_fatigue -= 6
            if self.short_fatigue <= 0:
                self.short_fatigue = 0
        if self.mana < self.max_mana:
            needs_update = True
            self.gain_mana(self.mana_regen_rate)
        if needs_update:
            self.owner.set_body_timer()
        else:
            self.stable = True

    def get_ko_cutoff(self):
        y = -1
        while y <= self.damage:
            y = floor(310 * betavariate(7, 4))
        return y

    def inv_ko_cdf(self, alpha):
        # Very, very, inefficient empirical approach
        sample_size = 20000
        sample = [self.get_ko_cutoff() for _ in range(sample_size)]
        sample.sort()
        rank = int(sample_size * alpha)
        percentile = sample[rank]
        if percentile > 300:
            return 300
        else:
            return percentile

    def reset(self):
        self.damage = 0
        self.fatigue = 0
        self.short_fatigue = 0
        self.bleeding_damage = 0


class UndeadBody(Body):
    bleeds = False

    def take_fatigue(self, *args, **kwargs):
        pass

    def take_ko(self, *args, **kwargs):
        self.die(0, None)
