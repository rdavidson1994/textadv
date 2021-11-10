import trait

class SpecialPhrase:
    def __init__(self, parser, synonyms, callback=None):
        self.parser = parser
        self.synonyms = synonyms
        self.callback = callback
        parser.special_phrases.append(self)

    def matches(self, string):
        if string in self.synonyms:
            return True
        else:
            return False

    def innate_action(self):
        return "SILENCE"

    def perform_action(self):
        if self.callback:
            out = self.callback()
        else:
            out = self.innate_action()
        return out


class QuitPhrase(SpecialPhrase):
    def innate_action(self):
        self.parser.actor.schedule.end_game = True
        # print(f"quit_phrase set {self.parser.hero.schedule}.end_game to True")
        return "Ending game."


class InventoryPhrase(SpecialPhrase):
    def innate_action(self):
        item_list = self.parser.actor.things_with_trait(trait.item)
        output_string = "\n".join([item.name for item in item_list])
        output_string += "\nmoney={}".format(self.parser.actor.money)
        return output_string
