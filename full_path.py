import os
import sys


def full_path(name):
    return os.path.join(sys.path[0], name)