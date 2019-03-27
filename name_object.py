import re

from verb import group_from_list as gfl
from copy import copy

try:
    from nltk.corpus import wordnet as wn
    using_nltk = True
except ImportError:
    wn = None
    using_nltk = True

def recursive_hypernyms(synset):
    next_hypernyms = synset.hypernyms()
    out = set(x for x in synset.lemma_names() if "_" not in x)
    for hypernym in next_hypernyms:
        out |= recursive_hypernyms(hypernym)
    return out


def best_synset(word):
    dots = word.count(".")
    if dots == 0:
        # "sword"
        try:
            return wn.synsets(word)[0]
        except IndexError:
            return None
    elif dots == 1:
        # "sword.n"
        return wn.synset(word+".01")
    elif dots == 2:
        # "sword.n.01"
        return wn.synset(word)
    else:
        raise AttributeError


def subset_names(name_string):
    pieces = name_string.split(" ")
    out = set(p for p in pieces if "." not in pieces)
    for piece in pieces:
        synset = best_synset(piece)
        if synset:
            hypernyms = recursive_hypernyms(synset)
            out |= hypernyms
        else:
            out.add(piece)
    return out


class Name:
    @classmethod
    def accept_string(cls, possible_str):
        if isinstance(possible_str, cls):
            return copy(possible_str)
        else:
            return cls(possible_str)

    def __init__(self, display_string, definition_string=None, proper=False):
        self.proper = proper
        if definition_string is None:
            definition_string = display_string
        else:
            definition_string = definition_string

        if self.proper:
            self.display_string = display_string.capitalize()
        else:
            self.display_string = display_string

        if using_nltk:
            self.lemma_set = subset_names(definition_string)
        else:
            self.lemma_set = set(definition_string.split(" "))

    def get_text(self):
        return self.display_string

    def matches(self, string):
        pieces = string.split(" ")
        return all(piece in self.lemma_set for piece in pieces)

    def add(self, other, template):
        new_name = self.accept_string(other)
        new_name.lemma_set |= self.lemma_set
        new_name.display_string = template.format(
            self.display_string,
            new_name.display_string,
        )
        return new_name

    def __add__(self, other):
        return self.add(other, template="{} {}")
