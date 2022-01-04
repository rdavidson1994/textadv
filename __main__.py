from save_manager import SaveManager
import random
random.seed("seed0001")

import argparse
from os import environ
import dill as pickle
import world


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--web", action="store_true")
    parser.add_argument("--save")
    args = parser.parse_args()

    save_manager = SaveManager()
    if args.save:
        w = save_manager.load(args.save)
    else:
        w = world.Random(use_web_output=args.web, save_manager=SaveManager())
    w.run_game()
