import world
import sites
import agent
import argparse

parser = argparse.ArgumentParser()
w = world.PopulationTest(sites.Hive, agent.GiantAntSwarm)
w.population.power = 99
dude = world.make_player(w.overworld, (5, 5))
w.run_game()
