import random
import name_object

from math import sqrt

from full_path import full_path

class NameMaker:
    syllable_choices = {1: 2, 2: 8, 3: 3}

    def __init__(self):
        self.word_onset = self.read("word_onset.txt")
        self.stressed_nucleus = self.read("stressed_nucleus.txt")
        self.nucleus = self.read("nucleus.txt")
        self.word_coda = self.read("word_coda.txt")
        self.inner = self.read("inner.txt")
        # self.onset_or_coda = self.dict_sum(self.onset, self.coda)

    @staticmethod
    def choose(dictionary):
        # Credit S.O. users Ned Batchelder and moooeeeep
        choices = dictionary.items()
        total = sum(w for c, w in choices)
        r = random.uniform(0, total)
        up_to = 0
        for c, w in choices:
            if up_to + w >= r:
                return c, w
            up_to += w
        assert False, "Shouldn't get here"

    @staticmethod
    def read(file_name):
        out_dict = {}
        comment = False
        with open(full_path(file_name)) as f:
            for line in f:
                line = line.partition("#")[0]
                line = line.rstrip()
                if line == "/*":
                    comment = True
                elif line == "*/":
                    comment = False
                elif not comment:
                    lst = line.split(",")
                    out_dict[lst[0]] = float(lst[1].strip())
        return out_dict

    def create_word(self, syllables=None):
        accepted = False
        pieces = []
        while not accepted:
            if syllables is None:
                syllables, _ = self.choose(self.syllable_choices)
            pieces_and_weights = [self.choose(self.word_onset)]
            if random.random() < 1.5:
                stress_index = 0
            else:
                stress_index = random.choice(list(range(0, syllables)))

            for i in range(0, syllables):
                if i > 0:
                    pieces_and_weights.append(self.choose(self.inner))
                if i == stress_index:
                    pieces_and_weights.append(self.choose(self.stressed_nucleus))
                else:
                    pieces_and_weights.append(self.choose(self.nucleus))

            pieces_and_weights.append(self.choose(self.word_coda))
            pieces, weights = zip(*pieces_and_weights)
            price = sum(1/w for w in weights)
            cutoff = 0.25+1/syllables
            if price < cutoff:
                accepted = True
        return "".join(pieces)


def make_string(syllables=None, name_maker=NameMaker(), raw_output=True):
    string = name_maker.create_word(syllables)
    if raw_output:
        return string
    else:
        return name_object.Name(string, proper=True)


def make_name(syllables=None, name_maker=NameMaker()):
    return make_string(syllables, name_maker, False)


if __name__ == "__main__":
    nm = NameMaker()
    for i in range(15):
        print(f"{nm.create_word()}")