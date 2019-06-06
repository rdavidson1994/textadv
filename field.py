class Field:
    def __init__(self, wide_location):
        self.location = wide_location
        wide_location.add_encounter_field(self)

    def probability(self, actor, x, y):
        return 0

    def targets_actor(self, actor):
        return actor.physical

    def affect_actor(self, actor):
        pass

    def destroy(self):
        self.location.remove_encounter_field(self)


class Disk(Field):
    def __init__(self, wide_location, radius, center, height):
        super().__init__(wide_location)
        self.radius = radius
        self.center = center
        self.density = height

    def probability(self, actor, x, y):
        if self.location.distance((x, y), self.center) < self.radius:
            return self.density
        else:
            return 0


class HelloDisk(Disk):
    def affect_actor(self, actor):
        actor.receive_text_message("AN ENCOUNTER HAPPENED!")


class NuisanceEncounters(Disk):
    def __init__(self, agent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent = agent

    def affect_actor(self, actor):
        self.agent.encounter_actor(actor)
