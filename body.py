from random import betavariate, randint, random
from math import floor, sqrt
try:
    from scipy.stats import norm
except ImportError:
#  on my work computer, scipy cannot be installed. This is a workaround.
    class norm:
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

    def take_ko(self, amt):
        self.ko_time += amt
        if amt > 0:
            self.owner.pass_out()
            if self.stable:
                self.start_updating()

    def die(self, amt, typ):
        self.owner.die(amt, typ)

    def lose_mana(self, amt):
        self.mana -= amt
        assert (self.mana >= 0)

    def take_fatigue(self, amt):
        if amt > 0:
            self.fatigue += amt
            self.short_fatigue += 3 * amt
            if self.stable:
                self.start_updating()

    def get_total_fatigue(self):
        return floor((self.short_fatigue + self.fatigue) / 4)

    def get_health_report(self):
        out = self.get_damage_report()
        out += self.get_stamina_report()
        out += self.get_skill_report()

        if self.max_mana > 0:
            mana = "You have {} mana remaining out of {}."
            out += mana.format(self.mana, self.max_mana)
        return out

    def get_skill_report(self, verbose=False, alpha=0.1):
        template = "Effective combat skill: {}\n"
        out = template.format(int(self.owner.get_attack_roll(weapon=None, min_=True)))
        mean = 80/2-30/2  # mean of parry roll - attack roll.
        sd = sqrt(30**2/12+2*40**2/12)
        margin_of_error = norm.ppf(alpha, loc=mean, scale=sd)
        template = "Most skilled opponent you can safely fight: {}\n"
        out += template.format(int(self.owner.get_parry_roll(min_=True) + margin_of_error))
        return out

    def get_damage_report(self, verbose=False, alpha=0.2):
        template = ("You have {} damage. "
                    "Expect to be knocked out between {} and {}. ({}% CI)\n")
        if self.damage != 0 or verbose:
            out = template.format(self.damage,
                                  self.inv_ko_cdf(alpha / 2),
                                  self.inv_ko_cdf(1 - alpha / 2),
                                  100 * (1 - alpha), )
            bleed_template = "You are bleeding at a rate of {} damage per second.\n"
            if self.bleeding_damage:
                out += bleed_template.format(self.bleeding_damage * 2)
        else:
            out = ""
        return out

    def get_stamina_report(self, verbose=False):
        template = "You have {} fatigue. {} of this is short-term.\n"
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
        needs_awaken = False
        if self.ko_time:
            self.ko_time -= 1
            if self.ko_time <= 0:
                self.ko_time = 0
                if not self.owner.awake:
                    self.owner.wake_up()
        if self.bleeding_damage:
            self.take_damage(self.bleeding_damage, "bleed")
            if random() < 0.13:
                self.bleeding_damage -= 1
            if self.bleeding_damage <= 0:
                self.bleeding_damage = 0
        if self.short_fatigue:
            self.short_fatigue -= 6
            if self.short_fatigue <= 0:
                self.short_fatigue = 0
        if self.ko_time or self.bleeding_damage or self.short_fatigue:
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


class UndeadBody(Body):
    bleeds = False

    def take_fatigue(self, *args, **kwargs):
        pass

    def take_ko(self, *args, **kwargs):
        self.die(0, None)
