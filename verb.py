import re
import direction


def group_from_list(lst, capture=False):
    group = r"|".join(lst)
    if capture:
        capstring = ""
    else:
        capstring = r"?:"
    group = r"(" + capstring + group + r")"
    return group


gfl = group_from_list


def optional(*strings):
    return gfl(strings) + "?"


class Verb:
    verb_list = []
    units = ["second", "minute", "hour"]
    unit_group = gfl(units, capture=True)
    time_string_pattern = "^(.*?) ?" + unit_group + "?(?:s)?$"
    time_regex = re.compile(time_string_pattern)
    match_strings = []

    def __init__(self, action_class):
        self.priority = action_class.priority
        self.verb_list.append(self)
        self.verb_list.sort(key=lambda verb: verb.priority)
        assert action_class.synonyms != []
        self.action_class = action_class
        token_lists = [s.split(" ") for s in self.match_strings]
        self.regex_list = [self.regex_from_tokens(l) for l in token_lists]
        self.signature_list = [self.signature_from_tokens(l)
                               for l in token_lists]

    class MatchTuple:
        # TODO: See if you can do this less stupid
        def __init__(self, parser, verb, groups, sig):
            self.parser = parser
            self.verb = verb
            self.groups = groups
            self.sig = sig
        def build_action(self):
            return self.verb.action_from_groups(self.parser,
                                                self.groups,
                                                self.sig)

    @classmethod
    def match_action_to_string(cls, parser, input_string):
        good_match = None
        backup_match = None
        for verb in cls.verb_list:
            groups, sig, quality = verb.match(parser, input_string)
            if quality is None:
                pass
            else:
                match = cls.MatchTuple(parser, verb, groups, sig)
                if quality == "good":
                    good_match = match
                    break
                elif backup_match is None:
                    backup_match = match
        if good_match:
            return good_match.build_action()
        elif backup_match:
            return backup_match.build_action()
        else:
            return None

    def match_quality(self, i):
        return "good"

    def regex_from_tokens(self, tokens):
        out_strings = []
        for token in tokens:
            if token == "VERB":
                out_strings.append(gfl(self.action_class.synonyms))
            elif token == "NONSENSE":
                out_strings.append(r"(?:.*)")
            elif token in ("TARGET", "TOOL", "DURATION", "LANDMARK"):
                out_strings.append(r"(.*)")
            elif token == "DIRECTION":
                group = gfl(direction.full_dict.keys(), capture=True)
                out_strings.append(group)
            elif token[-1] == "?":
                out_strings.append(optional(token[:-1]))
            else:
                out_strings.append(token)
        pattern = "^"+" ".join(out_strings)+"$"
        corrected_pattern = pattern.replace(")? "," )?")
        return re.compile(corrected_pattern)

    @staticmethod
    def signature_from_tokens(tokens):
        return [t for t in tokens
                if t in ("TARGET", "TOOL", "DURATION", "DIRECTION", "LANDMARK")]

    @staticmethod
    def number_from_word(n_string, numwords={}):
        # Credit to Tom Theisen, stackoverflow user "recursive".
        # https://stackoverflow.com/questions/493174/
        try:
            return int(n_string)
        except ValueError:
            pass

        if not numwords:
            units = [
                "zero", "one", "two", "three", "four", "five", "six",
                "seven", "eight","nine", "ten", "eleven", "twelve",
                "thirteen", "fourteen", "fifteen","sixteen", "seventeen",
                "eighteen", "nineteen",
            ]

            tens = ["", "", "twenty", "thirty", "forty",
                    "fifty", "sixty", "seventy", "eighty", "ninety"
            ]

            scales = ["hundred", "thousand", "million", "billion", "trillion"]

            numwords["and"] = (1, 0)
            for idx, word in enumerate(units):
                numwords[word] = (1, idx)
            for idx, word in enumerate(tens):
                numwords[word] = (1, idx * 10)
            for idx, word in enumerate(scales):
                numwords[word] = (10 ** (idx * 3 or 2), 0)

        current = result = 0
        for word in n_string.split():
            if word not in numwords:
                return None

            scale, increment = numwords[word]
            current = current * scale + increment
            if scale > 100:
                result += current
                current = 0

        return result + current

    def time_string_to_int(self, time_string):
        unit_dict = {None: 1, "second": 1, "minute": 60, "hour": 60*60}

        m = self.time_regex.match(time_string)
        if m is None:
            return None
        else:
            n_string, u_string = m.groups()

        number = self.number_from_word(n_string)
        if number is None:
            return None

        try:
            unit = unit_dict[u_string]
        except KeyError:
            return None

        return unit*number

    def match(self, actor, input_string):
        match = None
        quality = None
        for i, (regex, sig) in enumerate(zip(self.regex_list,
                                             self.signature_list)):
            possible_match = regex.match(input_string)
            if possible_match:
                match = possible_match
                quality = self.match_quality(i)
                if quality == "good":
                    break
        if match:
            return match.groups(), sig, quality
        else:
            return None, None, quality

    def action_from_groups(self, parser, groups, signature):
        # TODO: Think about moving this under MatchTuple?
        from action import FailAction
        target, tool = None, None
        kwargs = {}
        for word, kind in zip(groups, signature):
            if kind == "TARGET":
                target = parser.match_thing_to_name(word)
            elif kind == "TOOL":
                tool = parser.match_thing_to_name(word)
            elif kind == "LANDMARK":
                landmark = parser.match_landmark_to_name(word)
                kwargs["landmark"] = landmark
            elif kind == "DURATION":
                dur = self.time_string_to_int(word)
                if dur is None:
                    template = "{} doesn't make sense as an amount of time."
                    text = template.format(word)
                    return FailAction(parser.actor, failure_string=text)
                else:
                    kwargs["duration"] = dur
            elif kind == "DIRECTION":
                try:
                    direct = direction.full_dict[word]
                except KeyError:
                    template = "{} doesn't make sense as a direction."
                    text = template.format(word)
                    return FailAction(parser.actor, failure_string=text)
                else:
                    kwargs["direction"] = direct

        target_list = [i for i in [target, tool] if i]
        return self.action_class(parser.actor, *target_list, **kwargs)


class StandardVerb(Verb):
    match_strings = ["VERB", "VERB TARGET", "VERB TARGET with TOOL"]

    def match_quality(self, i):
        if i == self.action_class.number_of_targets:
            return "good"
        else:
            return "bad"
