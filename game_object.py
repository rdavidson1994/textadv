import errors

from name_object import Name
import logging
import direction
from menu_wrap import menu_wrap

debug = logging.debug


# logging.basicConfig(level=logging.WARNING,format='%(message)s')


class Landmark:
    def __init__(self, name, location=None, coordinates=None, basis=None):
        self.name = Name.accept_string(name)
        if basis:
            self.location = basis.location
            self.coordinates = basis.coordinates
        else:
            self.location = location
            self.coordinates = coordinates
            assert coordinates and location

    def vector_from_thing(self, thing):
        if thing.has_location(self.location):
            return self.location.displacement(thing, self.coordinates)

    def get_name(self, viewer=None):
        return self.name.get_text(viewer=viewer)

    def has_name(self, text):
        return self.name.matches(text)


class Thing:
    def __init__(
            self, location=None, name="", coordinates=None, other_names=(),
            sched=None, traits=(), names=(), *args, **kwargs
    ):
        self.physical = True
        self.trapping_item = None
        self.coordinates = coordinates
        self.things = set()
        self.traits = set(traits)
        self.location = location
        self.original_location = location
        self.arranged = True
        self.schedule = sched

        if self.location is not None:
            self.location.things.add(self)
            if self.schedule is None and self.location.schedule is not None:
                self.schedule = self.location.schedule

        if isinstance(name, Name):
            self.name_object = name
        elif names:
            self.name_object = Name(
                display_string=names[0],
                definition_string=" ".join(names),
            )
        else:
            self.name_object = Name(name)
        self.name = self.name_object.get_text()
        self.nearest_portal = None
        self.owner = None
        self.price = None

    def get_identifier(self, viewer=None):
        return "the "+self.get_name(viewer)

    def line_of_sight(self, first, second):
        return second.physical

    def hear_announcement(self, action):
        try:
            self_is_target = (action.target == self)
        except AttributeError:
            self_is_target = False
        if self_is_target:
            return self.action_targets_self(action)

    def action_targets_self(self, action):
        pass

    def broadcast_announcement(self, action):
        # This function gets hit pretty hard - should be more optimized
        target_set = set(action.target_list)
        subscribers = self.things_with_trait("listener") | target_set
        broadcast_source = action.actor
        if (
            getattr(action, "traverses_portals", False)
            and not action.actor.has_location(self)
        ):
            # Departing actor: Announce from portal, not actor
            broadcast_source = action.target
        for sub in subscribers:
            if (
                sub in target_set
                or self.line_of_sight(sub, broadcast_source)
            ):
                # the order of those conditions matters:
                # line_of_sight will throw errors on targets outside location
                sub.hear_announcement(action)

    def take_damage(self, amt, damage_type):
        pass

    def get_coordinates(self, viewing_location):
        assert viewing_location == self.location
        assert self.coordinates is not None
        return self.coordinates

    def vanish(self):
        if self.location is not None:
            self.location.things.remove(self)
        self.location = None

    def materialize(self, location, coordinates=None):
        if self.location is not None:
            raise AttributeError
        self.change_location(location, coordinates)

    def add_thing(self, thing, coordinates=None):
        self.things.add(thing)

    def change_location(
        self, new_location, coordinates=None, keep_arranged=False
    ):
        if self.location is not None:
            self.location.things.remove(self)
        self.location = new_location
        new_location.add_thing(self)
        if not keep_arranged:
            self.arranged = False
        else:
            self.original_location = new_location
        self.coordinates = coordinates

    def has_trait(self, trait):
        if trait in self.traits:
            return True
        else:
            return False

    def has_name(self, name):
        if self.name_object:
            return self.name_object.matches(name)
        else:
            return False

    def things_with_trait(self, trait):
        return {thing for thing in self.things if thing.has_trait(trait)}

    def things_with_name(self, name):
        return {thing for thing in self.things if thing.has_name(name)}

    def has_location(self, location):
        if location == self.location:
            return True
        else:
            return False

    def has_thing(self, thing):
        if thing in self.things:
            return True
        else:
            return False

    def get_interactables(self, viewer=None):
        '''PUBLIC: returns a list with all interactables at the location.'''
        output = set(self.things)
        if viewer:
            output = {t for t in output if self.line_of_sight(viewer, t)}
        nested = set()
        for thing in output:
            nested |= thing.get_interactables()
        output |= nested
        return output

    def has_nested_thing(self, thing):
        if self.has_thing(thing):
            return True
        else:
            for container in self.things_with_trait("container"):
                if container.has_nested_thing(thing):
                    return True
            return False

    def has_furnishing(self, name):
        for thing in self.things_with_name(name):
            if thing.original_location == self and thing.arranged:
                return True
        return False

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.name)

    def be_targeted(self, action):
        """
        This method implements any special behavior or checks that the
        interactable performs when an action is done to it. Allowed to have side
        effects.

        At the end, implementation should return 
        super().be_targeted(self, action), so that special
        behaviors of the parent class can be inheritted properly.

        Note that this sometimes results in multiple special behaviors being
        executed at the same time.

        Returns (Bool, String)
        Bool = True if the action is successful and the affect_game
        method should be called, and success_string returned to the player
        false if the action is unsuccessful and the affect_game method
        should not be called, and the failure string provided by this method
        should be returned.

        String = A description of the actor's success or failure. If
        string == "", then the actions default failure or success string
        should be displayed.
        """
        debug("Special target effects called")
        return True, ""

    def get_name(self, viewer=None):
        '''PUBLIC: Return a name appropriate to the viewer
        arg viewer: The actor who is looking at this object.
        return: A name for this object appropriate to the viewer'''
        if viewer is None:
            web = False
        else:
            try:
                web = viewer.ai.web_output
            except AttributeError:
                web = False
        out = self.name
        if web:
            return self.menu_wrap(out)
        else:
            return out

    @staticmethod
    def get_suggested_verbs():
        return "take", "examine"

    def menu_wrap(self, text):
        return menu_wrap(text, self.get_suggested_verbs())

    def get_look_text(self, viewer=None):
        return self.get_name(viewer)

    def show_text_to_hero(self, text):
        for i in self.things_with_trait("hero"):
            i.receive_text_message(text)


class Item(Thing):
    def __init__(self, *args, **kwargs):
        Thing.__init__(self, *args, **kwargs)
        self.traits.add("item")

    def __repr__(self):
        return "Item({})".format(self.name)


class FoodItem(Item):
    def __init__(self, nutrition=0, *args, **kwargs):
        Item.__init__(self, *args, **kwargs)
        self.traits.add("food")
        self.nutrition = nutrition

    def get_suggested_verbs(self):
        base = super().get_suggested_verbs()
        return ("eat",)+base


class Lock:
    def __init__(self, key, locked):
        self.key = key
        self.locked = locked

    def locking_attempt(self, action):
        debug("Action detected as locking things.")
        if self.locked == action.desired_state:
            return False, "It is is already {}.".format(action.desired_string)
        elif action.tool != self.key:
            name = action.tool.get_name(action.actor)
            return False, "The {} doesn't fit.".format(name)
        else:
            return True, ""


class Container(Item):
    def __init__(self, is_open=True, *args, **kwargs):
        Item.__init__(self, *args, **kwargs)
        self.is_open = is_open
        self.traits.add("container")

    def get_look_text(self, viewer=None):
        base = super().get_look_text(viewer)
        header = "Contents:"
        out_list = [base, header]
        item_looks = [item.get_name(viewer) for item in self.things]
        out_list.extend(item_looks)
        return "\n".join(out_list)


class Cage(Thing):
    def __init__(self, key=None, *args, **kwargs):
        Thing.__init__(self, *args, **kwargs)
        self.traits.add("lockable")
        self.lock = Lock(locked=True, key=key)
        self.prisoners = set()

    def be_targeted(self, action):
        if getattr(action, "locks_things", False):
            return self.lock.locking_attempt(action)
        else:
            return super().be_targeted(action)

    def is_locked(self):
        return self.lock.locked

    def add_prisoner(self, prisoner):
        prisoner.trapping_item = self
        self.prisoners.add(prisoner)

    def remove_prisoner(self, prisoner):
        prisoner.trapping_item = None
        self.prisoners.remove(prisoner)

    def free_prisoners(self):
        for prisoner in self.prisoners:
            prisoner.trapping_item = None
        self.prisoners = []


class PortalVertex(Thing):
    def __init__(self, direction, edge, *args, **kwargs):
        Thing.__init__(self, *args, **kwargs)
        self.direction = direction
        self.traits.add("portal")
        self.edge = edge
        self.landmark = None

    def set_site(self, site):
        self.edge.set_site(site, site_exit=self)

    def be_entered(self, actor):
        self.edge.be_entered(actor, self)

    def get_relative_direction(self, viewer):
        return self.edge.get_relative_direction(viewer)

    def get_coordinates(self, viewing_location):
        return self.coordinates

    def get_name(self, viewer=None):
        """Returns a name appropriate to the viewing actor.
        """
        if viewer:
            if (
                viewer.has_location(self.location)
                and self.coordinates is not None
                and viewer.coordinates is not None
            ):
                distance = self.location.distance(self, viewer)
                bearing = self.location.compass_direction(viewer, self).upper()
                return f"{self.name}, {distance:.1f} units {bearing}"
            else:
                direction = self.get_relative_direction(viewer)
                return self.name + " facing " + str(direction)
        else:
            return self.name

    def be_targeted(self, action):
        debug("Portal target effects called")
        if getattr(action, "traverses_portals", False):
            # if action.traverses_portals == True or AttributeError
            if self.edge.lock and self.edge.lock.locked:
                return False, "The door is locked."
            else:
                return super().be_targeted(action)
        elif getattr(action, "locks_things", False):
            debug("Action detected as locking things.")
            if self.edge.lock is not None:
                return self.lock.locking_attempt(action)
            else:
                return super().be_targeted(action)
        else:
            return super().be_targeted(action)

    def get_relative_destination(self, viewer):
        assert viewer.location == self.location
        return self.edge.other_vertex(self)

    def opposite(self):
        return self.edge.other_vertex(self)

    def create_landmark(self, name):
        self.landmark = Landmark(name=name,
                                 basis=self,)
        return self.landmark


class PortalEdge:
    def __init__(
        self,
        locations=(None, None),
        directions=(None, None),
        key=None,
        locked=False,
        coordinate_pairs=(None, None),
        name_pair=("", ""),
        name="",
        *args,
        **kwargs
    ):
        self.site = None
        self.site_exit = None  # used to specify which vertex is the exit
        self.source_loc, self.target_loc = locations
        self.source_coords, self.target_coords = coordinate_pairs
        self.source_direction, self.target_direction = directions

        if name != "":
            name_pair = (name, name)

        self.vertices = [
            PortalVertex(
                edge=self,
                direction=direct,
                location=loc,
                coordinates=pair,
                name=nm,
                *args, **kwargs
            )
            for loc, pair, direct, nm
            in zip(
                locations,
                coordinate_pairs,
                directions,
                name_pair
            )
        ]
        self.source, self.target = self.vertices
        if locked or key is not None:
            self.lock = Lock(key, locked)
            for vertex in self.vertices:
                vertex.traits.add("lockable")
                vertex.lock = self.lock
        else:
            self.lock = None
        self.direction = tuple(directions)  # eg ("n", "s"), if source is north

    @classmethod
    def free_portal(cls, location, direction, coordinates=None, **kwargs):
        # Creates a portal with a specified location, and no partner
        locations = (location, None)
        directions = (direction.opposite, direction)
        coordinate_pairs = (coordinates, None)
        output_portal = cls(locations,
                            directions,
                            coordinate_pairs=coordinate_pairs,
                            **kwargs)
        return output_portal

    def be_entered(self, actor, vertex):
        if self.site and actor.has_trait("hero"):
            if vertex == self.site_exit:
                # if the hero is leaving the site.
                self.site.offload()
            else:
                # if the hero is entering the site.
                self.site.update_region()
        if actor.location == self.source.location:
            actor.change_location(self.target.location,
                                  self.target.coordinates)
            actor.nearest_portal = self.target
        elif actor.location == self.target.location:
            actor.change_location(self.source.location,
                                  self.source.coordinates)
            actor.nearest_portal = self.source
        else:
            raise Exception
        return True, "SILENCE"

    def other_vertex(self, given_vertex):
        for v in self.vertices:
            if v != given_vertex:
                return v
        else:
            raise Exception

    def get_relative_direction(self, viewer):
        """Returns which way the exit points, relative to a given location
        arg viewerLocation: Which location you are looking at the exit from.
        return: A string ('n','s','e','w','u','d') represnting which
         direction the exit faces.
        """
        if viewer.location == self.source.location:
            return self.target_direction
        if viewer.location == self.target.location:
            return self.source_direction
        else:
            raise errors.MisplacedViewer

    def set_site(self, site, site_exit):
        self.site = site
        self.site_exit = site_exit

    def set_vertex_location(self, index, new_location, new_coords=None):
        self.vertices[index].change_location(new_location, new_coords)

    def set_target_location(self, new_location, new_coords=None):
        self.set_vertex_location(1, new_location, new_coords)

    def set_source_location(self, new_location, new_coords=None):
        self.set_vertex_location(0, new_location, new_coords)


class Door(PortalEdge):
    def __init__(self, start, end, direct="random"):
        locations = (start, end)
        if direct == "random":
            direct = direction.random()
        directions = (direct.opposite, direct)
        name_pair = [
            Name("door to")+place.name
            for place in (end, start)
        ]
        super().__init__(
            locations=locations,
            directions=directions,
            name_pair=name_pair
        )


"""
class GameEndPortal(Portal):
    prisoner_freed = False

    def be_entered(self, actor):
        if actor.has_trait("hero"):
            actor.schedule.end_game = True
            print("Congrats! You made it out of there alive.")
            if actor.has_thing_with_name("chest"):
                print("You even have some treasure to show for it!")
            if self.prisoner_freed:
                print("And you freed the prisoner too!")
        elif actor.has_name("prisoner"):
            self.prisoner_freed = True
        actor.vanish()
"""
