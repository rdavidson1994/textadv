import argparse
import dill as pickle
from os import path
import json


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

        return index