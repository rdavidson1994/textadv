from random import random, choice, uniform
from string import ascii_uppercase
from math import sqrt

def distance(a, b):
    return sqrt(sum(x**2 + y**2 for x,y in zip(a.coordinates, b.coordinates)))


class Context:
    MIN_X = 0
    MAX_X = 100
    MIN_Y = 0
    MAX_Y = 100

    def __init__(self):
        self.agents = []
        self.places = []

    def add_agent(self, agent):
        assert agent.context == self
        self.agents.append(agent)

    def perform_cycle(self):
        for agent in self.agents:
            agent.take_turn()

    def perform_cycles(self, number_of_cycles):
        for i in range(number_of_cycles):
            self.perform_cycle()

    def random_point(self):
        return uniform(self.MIN_X, self.MAX_X), uniform(self.MIN_Y, self.MAX_Y)

    def add_place(self, place):
        self.places.append(place)


class DemoContext(Context):
    number_of_caves = 20
    number_of_towns = 6

    def __init__(self):
        Context.__init__(self)
        for i in range(self.number_of_caves):
            self.add_place(Cave(self.random_point()))
        for i in range(self.number_of_towns):
            town = Town(self, name=ascii_uppercase[i])
            self.add_agent(town)


class Agent:
    civilized = False

    def __init__(self, context):
        self.context = context
        context.add_agent(self)

    def take_turn(self):
        pass


class Place:
    def __init__(self, coordinates):
        self.coordinates = coordinates

class Mine(Place):
    pass

class Cave(Place):
    pass



class Town(Agent):
    civilized = True

    def __init__(self, *args, name, **kwargs):
        super().__init__(*args, **kwargs)
        self.coordinates = self.context.random_point()
        self.name = name
        self.unrest = 0
        self.destroyed = False

    def take_turn(self):
        if self.destroyed:
            return

        if random() < 1/100:
            print(f"{self.name} built a mine")

        if random() < 1/1000:
            self.unrest += 20
            print(f"{self.name} suffered a plague")

        roll = random()
        if roll < 1/10:
            print(f"{self.name} had a good harvest")
            if self.unrest > 10:
                self.unrest -= 10
            else:
                self.unrest = 0

        elif roll > 9/10:
            self.unrest += 3
            print(f"{self.name} had a bad harvest")

        if random() < (self.unrest/100)**2:
            print(f"{self.name} spawned a bandit group @ unrest {self.unrest}")
            BanditGroup(self, self.context)

        if self.unrest > 40 + random()*40:
            print(f"{self.name} crumbled to ruin amid starvation and rioting.")
            self.destroyed = True
            return


class BanditGroup(Agent):
    def __init__(self, parent_town, context):
        super().__init__(context)
        self.target = parent_town
        self.power = 10
        self.exposure = 0


def basic_demo():
    context = DemoContext()

    context.perform_cycles(1000)

if __name__ == "__main__":
    basic_demo()
