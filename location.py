from typing import Optional
from game_object import Thing, debug

class Location(Thing):
    def __init__(self, description="", reg=None, *args, **kwargs):
        from region import Node
        Thing.__init__(self, *args, **kwargs)
        self.reg = reg
        self.map_node : Optional[Node] = None
        self.traits.add("location")
        self.description = description

    def is_entrance(self):
        return False

    def path_to_entrance(self):
        if self.map_node is None:
            raise AttributeError

        return self.map_node.region.path_to_entrance(self.map_node)

    def path_to_rally(self):
        if self.map_node is None:
            raise AttributeError

        return self.map_node.region.path_to_rally(self.map_node)

    def rally_point(self):
        if self.map_node is None:
            raise AttributeError

        return self.map_node.region.get_rally_node().location

    def path_to_location(self, other_location):
        if self.map_node is None:
            raise AttributeError  # Not part of a region

        return self.map_node.region.path_to_location(self, other_location)

    def wander_destination(self):
        if self.map_node is None:
            raise AttributeError

        return self.map_node.region.path_to_random(self.map_node)

    def get_text_map(self, viewer=None, full_size=False):
        if self.map_node is None:
            return None
        else:
            return self.map_node.region.get_text_map(
                viewer=viewer, full_size=full_size
            )

    def get_description(self, viewer: Thing):
        return self.description

    def describe(self, viewer, full_text=True):
        """PUBLIC: returns a string description of the location"""
        str_list = []
        text_map = self.get_text_map(viewer)
        if text_map:
            str_list.append(text_map)
        category_list = [("actor", "\nPeople and animals:"),
                         ("item", "\nItems:"),
                         ("interesting", "\nInteresting features:"),
                         ("portal", "\nExits:")]
        if full_text:
            str_list.append(self.get_description(viewer))
        for trait, header in category_list:
            subset = self.things_with_trait(trait)
            if viewer in subset:
                subset.remove(viewer)
            subset = {t for t in subset if self.line_of_sight(viewer, t)}
            debug(subset)
            if subset:
                str_list.append(header)
            for thing in subset:
                str_list.append(thing.get_name(viewer))
        return '\n'.join(str_list)
