import re

from verb import group_from_list as gfl


class Name:
    @staticmethod
    def wrap_if_str(possible_str):
        if isinstance(possible_str, str):
            return [possible_str]
        else:
            return list(possible_str)

    @staticmethod
    def sequence_regex(*seq):
        group_seq = [gfl(i) for i in seq]
        group_str = " ".join(group_seq)
        strict_str = "^" + group_str + "$"
        return re.compile(strict_str)

    @classmethod
    def accept_string(cls, string_or_name):
        if isinstance(string_or_name, cls):
            return string_or_name
        elif isinstance(string_or_name, str):
            return cls(n=string_or_name)

    def __init__(self,
                 a=(),
                 n=(),
                 has_article=False,
                 display_name=None):
        self.nouns = self.wrap_if_str(n)
        self.adjectives = self.wrap_if_str(a)
        self.has_article = has_article
        self.display_name = display_name
        noun_regex = self.sequence_regex(self.nouns)
        if a:
            adjective_regex = self.sequence_regex(self.adjectives)
            full_regex = self.sequence_regex(self.adjectives, self.nouns)
            self.regex_list = [noun_regex, adjective_regex, full_regex]
        else:
            self.regex_list = [noun_regex]

    def get_text(self, viewer=None, use_article=False):
        if self.display_name:
            return self.display_name
        elif self.adjectives:
            return self.adjectives[0] + " " + self.nouns[0]
        else:
            return self.nouns[0]

    def matches(self, text):
        for regex in self.regex_list:
            if regex.match(text):
                return True
            else:
                continue
        else:
            return False