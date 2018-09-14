import re
class Verb():
    priority = 100
    def group_from_list(self, lst):
        group = r"|".join(lst)
        group = r"(?:"+group+r")"
        return group
        

class IntransVerb(Verb):
    def __init__(self, verb_strings = []):
        self.verb_strings = verb_strings
        verb_group = self.group_from_list(verb_strings)
        self.regex = re.compile(verb_group)
    def match(self, string):
        m = self.regex.match(string)
        return m
        
class TransVerb(Verb):
    pass

run = IntransVerb([r"\brun\b",r"\bjog\b",r"\bsprint\b"])
