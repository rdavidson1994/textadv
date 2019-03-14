import argparse
import pickle
from world import Static
from os import path
import json

k = {
    "type": "button",
    "text": "tall kobold",
    "options": [
        {"hit": "hit tall kobold"},
        {"examine": "examine tall kobold"},
        {"spells": ""}
    ]
}


class SaveManager:
    def __init__(self, save_directory):
        self.save_directory = save_directory

    def load(self, save_number):
        save_name = path.join(self.save_directory, f"save{save_number}.pkl")
        with open(save_name, 'rb') as file:
            return pickle.load(file)

    def save(self, world):
        index = 0
        base_save_name = path.join(self.save_directory, "save")
        save_name = None
        while not save_name or path.exists(save_name):
            index += 1
            save_name = base_save_name + str(index) + ".pkl"
            if index > 9999:
                Exception("File names save0 - save9999 exist. What gives?")

        with open(save_name, 'wb') as file:
            pickle.dump(world, file)

        if args.web:
            outObject = {
                "type": "save",
                "status": "success",
                "saveId": index,
            }
            print(json.dumps(outObject))
            return "SILENCE"
        else:
            return f"Save created at save{str(index)}.pkl"


if __name__ == "__main__":
    save_directory = path.join(path.dirname(path.abspath(__file__)), "saves")
    parser = argparse.ArgumentParser()
    parser.add_argument("-web", help="Enable html output.",
                        action="store_true")
    parser.add_argument("--save", help="Specify save game.")
    args = parser.parse_args()

    save_manager = SaveManager(save_directory)

    if args.save:
        world = save_manager.load(args.save)
    else:
        world = Static(args.web, save_manager)

    world.run_game()
    save_manager = SaveManager(save_directory)
    saved_game = save_manager.save(world)
    if args.web:
        json_out = {
            "type": "output complete",
            "gameOver": True,
        }
        print(json.dumps(json_out))
