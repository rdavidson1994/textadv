class SpecialPhrase():
    def __init__(self, parser, synonyms):
        self.parser = parser
        self.synonyms = synonyms
        parser.special_phrases.append(self)

    def matches(self, string):
        if string in self.synonyms:
            return True
        else:
            return False

    def perform_action(self):
        pass


class QuitPhrase(SpecialPhrase):
    def perform_action(self):
        self.parser.actor.schedule.end_game = True
        # print(f"quit_phrase set {self.parser.hero.schedule}.end_game to True")
        return "Ending game."


class InventoryPhrase(SpecialPhrase):
    def perform_action(self):
        item_list = self.parser.actor.things_with_trait('item')
        output_string = "\n".join([item.name for item in item_list])
        output_string += "\nmoney={}".format(self.parser.actor.money)
        return output_string
