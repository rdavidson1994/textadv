import location
import schedule
import actor
import game_object
import direction as direc
import spells
import phrase



class Test:
    def __init__(self):
        self.schedule = schedule.Schedule()
        self.street = location.Location(name="street",
                                        description="You are outside.")

        self.hero = actor.Hero(self.street, name="john", sched=self.schedule)
        self.parser = self.hero.ai
        self.hero.spells_known = {spells.Shock, spells.Fireball}
        phrase.QuitPhrase(self.parser, ["quit", "exit"])
        phrase.InventoryPhrase(self.parser, ["i", "inventory"])

    def run(self):
        self.schedule.run_game()

class Building(Test):
    def __init__(self):
        super().__init__()
        self.house = location.Location(name="shop", description="You are inside.")
        self.portal = game_object.Door(self.street, self.house)
        # self.portal = thing.PortalEdge(locations=(self.street, self.house),
        #                                directions=(direc.s, direc.n), )
        

class Town(Test):
    def __init__(self):
        super().__init__()
        desc = "You are inside the guardhouse."
        self.guardhouse = location.Location(description=desc)
        self.portal = game_object.Door(self.street, self.guardhouse)
