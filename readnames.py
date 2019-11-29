import random
from collections import Counter

vowels = "aeiou"


def choose(dictionary):
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


def split_word(word):
    word = word.lower()
    out = [[]]
    last_vowel_status = False
    for char in word:
        vowel_status = char in vowels
        if last_vowel_status == vowel_status:
            out[-1].append(char)
        else:
            last_vowel_status = vowel_status
            out.append([char])
    return ["".join(x) for x in out]


class TransitionCounter:
    def __init__(self):
        self.starts = Counter()
        self.transitions = {}
        self.ends = {}

    def add_pair(self, first, second, is_final=False):
        if is_final:
            d = self.ends
        else:
            d = self.transitions
        if first not in d:
            d[first] = Counter()
        d[first][second] += 1

    def add_start(self, start):
        self.starts[start] += 1

    def random_start(self):
        return choose(self.starts)

    def next_from(self, piece, is_final=False):
        if is_final:
            d = self.ends
        else:
            d = self.transitions
        if piece not in d:
            return None
        else:
            return choose(d[piece])

if __name__ == "__main__":
    tc = TransitionCounter()
    with open("good.txt") as f:
        for line in f:
            pieces = split_word(line.strip())
            tc.add_start(pieces[0])
            for i in range(len(pieces)-2):
                tc.add_pair(pieces[i], pieces[i+1])
            if len(pieces) >= 2:
                tc.add_pair(pieces[-2], pieces[-1], is_final=True)
    for _ in range(10):
        out = [tc.random_start()]
        for i in range(random.randint(2, 5)):
            next = tc.next_from(out[-1])
            out.append(next)
        out.append(tc.next_from(out[-1], is_final=True))

        print(out)
        print("".join(out).capitalize())