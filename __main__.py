import random
import argparse


random.seed("seed0001")
import world


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--web", action="store_true")
    parser.add_argument("--save")
    w = world.Random()
    w.run_game()
