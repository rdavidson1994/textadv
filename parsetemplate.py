import re
import textwrap
from full_path import full_path


class TemplateParser:
    
    def __init__(self, string):
        self.needle = 0
        self.string = string
        self.length = len(string)

    def valid_needle(self):
        return self.needle < self.length

    def char(self):
        return self.string[self.needle]

    def slice(self, start):
        return self.string[start:self.needle]

    def parse_token(self):
        start = self.needle
        while self.valid_needle():
            if self.char() == ":":
                out = self.slice(start)
                self.needle += 1
                return out
            else:
                self.needle += 1
        else:
            raise Exception("EOF while scanning token.")

    def match_word(self, word):
        if self.string[self.needle:self.needle+len(word)]==word:
            self.needle+=len(word)
            return True
        else:
            return False

    def null_parse(self):
        open_curlies = 0
        while self.valid_needle():
            if self.char() == "{":
                open_curlies += 1
            elif self.char() == "}":
                if open_curlies == 0:
                    return ""
                else:
                    open_curlies -= 1
            elif self.char() == "*" and open_curlies == 0:
                self.needle += 1
                if self.match_word("else:"):
                    return self.parse()
                else:
                    raise Exception("Star without recognized command")
            self.needle += 1

    def evaluate_token(self, token):
        if token != "ignore":
            return True
        else:
            return False

    def parse(self):
        out = ""
        start = self.needle
        
        while self.valid_needle():
            if self.char() == "{":
                self.needle += 1  # Move past the curly
                out += self.slice(start)
                token = self.parse_token()
                referent = self.evaluate_token(token)
                if referent:
                    out += self.parse()
                else:
                    out += self.null_parse()
                start = self.needle
            elif self.char() == "}":
                break
            elif self.char() == "*":
                out += self.slice(start)
                self.needle += 1
                if self.match_word("else:"):
                    out += self.null_parse()
                    return out
                else:
                    raise Exception("Star without recognized command")
            self.needle += 1

        out += self.slice(start)
        return out

    def full_parse(self):
        self.needle = 0
        out = self.parse()
        out = re.sub(r"[{}]", "", out)
        out = re.sub(r"\.",". ",out)
        out = re.sub(r",",", ",out)
        out = re.sub(r"(?<=[a-zA-Z])\s+(?=[.,])", "", out)
        out = re.sub(r"\s+", " ", out)
        out = re.sub(r"\.\s*,", ",", out)
        out = "\n".join(textwrap.wrap(out, 70))
        return out


class RoomTemplateParser(TemplateParser):
    # with open(full_path("room_descriptions.txt")) as f:
    #     file_text = f.read()
    # templates = file_text.split("@")
    # templates.remove("")
    # pairs = [template.split(None, 1) for template in templates]
    # # noinspection PyTypeChecker
    # template_dict = dict(pairs)

    def __init__(self, room, string):
        super().__init__(string)
        self.room = room

    def evaluate_token(self, token):
        return self.room.evaluate_token(token)


class ParserManager:
    files_read = {}

    @classmethod
    def get_parser(cls, room, filename, key):
        if filename not in cls.files_read:
            with open(full_path(filename)) as f:
                file_text = f.read()
            templates = file_text.split("@")
            templates.remove("")
            pairs = [template.split(None, 1) for template in templates]
            # noinspection PyTypeChecker
            template_dict = dict(pairs)
            cls.files_read[filename] = template_dict
        return RoomTemplateParser(room, cls.files_read[filename][key])

def test_print(*args, **kwargs):
    # placeholder
    pass

def test():
    """
    class Room:
        def evaluate_token(self, token):
            test_print("Sent token: "+token)
            if token == "use":
                return True
            else:
                return False
    """

    test_string = "Just a string"
    my_parser = TemplateParser(test_string)
    test_print(my_parser.parse())


def else_test():
    string = "Outer text {use: ignored text *else: else text}"
    p = TemplateParser(string)
    test_print(p.full_parse())


def room_test():
    from dungeonrooms import TreasureRoom
    tr = TreasureRoom()
    tr2 = TreasureRoom()
    rtp = ParserManager.get_parser(tr, "room_descriptions.txt", "TreasureRoom")
    test_print(rtp.full_parse())
    tr.decor_dict["chest"].change_location(tr2)
    test_print("Furnish test: "+str(tr.has_furnishing("chest")))
    test_print(rtp.full_parse())


def apothecary_test():
    from dungeonrooms import Apothecary
    Apothecary()
    

if __name__ == "__main__":
    room_test()

