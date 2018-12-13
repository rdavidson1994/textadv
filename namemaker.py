import random
from full_path import full_path

class NameMaker:
    syllable_choices = {1: 2, 2: 8, 3: 3, 4: 1}

    def __init__(self):
        self.word_onset = self.read("word_onset.txt")
        self.onset = self.read("onset.txt")
        self.stressed_nucleus = self.read("stressed_nucleus.txt")
        self.nucleus = self.read("nucleus.txt")
        self.coda = self.read("coda.txt")
        self.word_coda = self.read("word_coda.txt")

    def choose(self, dictionary):
        # Credit S.O. users Ned Batchelder and moooeeeep
        choices = dictionary.items()
        total = sum(w for c, w in choices)
        r = random.uniform(0, total)
        up_to = 0
        for c, w in choices:
            if up_to + w >= r:
                return c
            up_to += w
        assert False, "Shouldn't get here"

    def read(self, file_name):
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
        if syllables is None:
            syllables = self.choose(self.syllable_choices)

        word_pieces = [self.choose(self.word_onset),
                       self.choose(self.stressed_nucleus)]

        for i in range(syllables-1):
            word_pieces.append(self.choose(self.coda))
            word_pieces.append(self.choose(self.onset))
            word_pieces.append(self.choose(self.nucleus))

        word_pieces.append(self.choose(self.word_coda))
        return "".join(word_pieces)


if __name__ == "__main__":
    nm = NameMaker()
    for i in range(15):
        print(nm.create_word())

# for s in range(syllables):
#     for lst in choice_lists:
#         word_pieces.append(weighted_choice(lst))