import location
import game_object


class EncounterPocket(location.Location):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actors = []

    def offload(self):
        for actor in self.actors:
            actor.vanish()

    def add_actor(self, actor):
        self.actors.append(actor)

    def add_actors(self, actors):
        self.actors.extend(actors)


class PocketExit(game_object.PortalEdge):
    def __init__(self, *args, encounter_pocket, **kwargs):
        super().__init__(*args, **kwargs)
        self.target.physical = False
        self.encounter_pocket = encounter_pocket

    def be_entered(self, actor, vertex):
        super().be_entered(actor, vertex)
        if vertex == self.source:
            self.encounter_pocket.offload()
