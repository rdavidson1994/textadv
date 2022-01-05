import argparse
import dill as pickle
from os import path, environ, makedirs
import json
from uuid import uuid4


class SaveManager:
    def load(self, save_path):
        with open(save_path, 'rb') as file:
            return pickle.load(file)

    def save(self, world):
        index = 0
        
        save_directory = environ.get("TEXTADV_SAVE_DIR", path.abspath("./saves"))
        base_save_name = path.join(save_directory, "save")
        save_path = None
        while not save_path or path.exists(save_path):
            index += 1
            if index < 10:
                save_path = base_save_name + str(index) + ".pkl"
            else:
                save_path = path.join(save_directory, str(uuid4())+".pkl")

        makedirs(save_directory, exist_ok=True)
        with open(save_path, 'wb') as file:
            pickle.dump(world, file)

        return save_path