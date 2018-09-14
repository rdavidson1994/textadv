import lock

class Interactable():
    def __init__(self, location, name, short_name=None):
        self.items = []
        self.traits = []
        self.location = location
        self.name = name
        self.target_strategy_dict = {}
        if short_name == None:
            self.short_name = name
        else:
            self.short_name = short_name

    def has_trait(self, trait):
        if trait in self.traits:
            return True
        else:
            return False

    def return_false_strategy(*args):
        return False

    def has_name(self, name):
        if self.name == name or self.short_name == name:
            return True
        else:
            return False

    def has_item(self, target):
        if target in self.items:
            return True
        else:
            return False

    def __repr__(self):
        return "Interactable({})".format(self.name)

    def has_location(self, location):
        if location == self.location:
            return True
        else:
            return False

    def be_targetted(self, action, actor, *target_list):
        """
        This method implements any special behavior or checks that the
        interactable performs when an action is done to it. It is allowed to have side
        effects.

        At the end, implementation should return 
        super().be_targeted(self, action, actor, *target_list), so that special
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
        return True, ""

    def get_name(self, viewer):
        '''PUBLIC: Return a name appropriate to the viewer
        arg viewer: The actor who is looking at this object.
        return: A name for this object appropriate to the viewer'''
        return self.name

class Location(Interactable):

    def __init__(self, description = "A field of grass."):
        self.name = "" #Players are not supposed to directly interact with locaitons.
        self.items = []
        self.actors = []
        self.portals = []
        self.description = description

    def has_interactable(self, interactable):
        if interactable in self.get_interactables():
            return True
        else:
            return False

    def has_portal(self, portal):
        if portal in self.portals:
            return True

    def has_location(self, location):
        #locations are not nested. No location resides in another location.
        return False

    def describe(self, viewer):
        '''PUBLIC: returns a string description of the location'''
        str_list = []
        if viewer.parser.verbose or self not in viewer.visited_locations:
            str_list.append(self.description)
        if self.actors != []:
            str_list.append("\nPeople and animals:")
            for actor in self.actors:
                str_list.append(actor.get_name(viewer))
        if self.items != []:
            str_list.append("\nObjects of interest:")
            for item in self.items:
                str_list.append(item.get_name(viewer))
        if self.portals != []:
            str_list.append("\nExits:")
            for portal in self.portals:
                str_list.append(portal.get_name(viewer))
        return '\n'.join(str_list)

    def get_interactables(self):
        '''PUBLIC: returns a list with all interactables at the location.'''
        output = self.items+self.actors+self.portals
        for possible_container in self.items:
            try:
                if possible_container.is_open or possible_container.contents_visible_when_closed:
                    output += possible_container.items
            except AttributeError:
                pass
        return output

class InvItem(Interactable):                  
    def __init__(self, location, name, short_name=None):
        super().__init__(location, name, short_name)
        self.location.items.append(self)

    def __repr__(self):
        return "Item({})".format(self.name)

    def is_item(self):
        return True

    def vanish(self):
        self.location.items.remove(self)
        self.location = None
                   
    def change_location(self, new_location):
        self.location.items.remove(self)
        self.location = new_location
        self.location.items.append(self)
                   
    def be_taken(self, actor):
        self.change_location(actor)
        return True, 'You take the {}.'.format(self.name)
                   
    def be_dropped(self, actor):
        self.change_location(actor.location)
        return True, 'You drop the {}.'.format(self.name)

class FoodItem(InvItem):
    def __init__(self, *args):
        super().__init__(*args)
        self.traits.append("food")
        self.nutrition = 0
        

class Portal(Interactable):

    def __init__(self, source, target, sourceDirection, targetDirection, name = ""):
        super().__init__(source, name)
        self.source = source
        self.target = target
        source.portals.append(self)
        target.portals.append(self)
        self.direction = (sourceDirection, targetDirection) #eg ("n", "s"), if the source is on the north side

    def __repr__(self):
        return "Portal("+str(self.direction)+self.name+")"

    def has_location(self, location):
        if location == self.source or location == self.target:
            return True
        else:
            return False

    def get_relative_direction(self, viewer):
        '''Returns which way the exit points, relative to a given location
        arg viewerLocation: Which location you are looking at the exit from.
        return: A string ('n','s','e','w','u','d') represnting which direction the exit faces.
        '''
        if viewer.location == self.source:
            return self.direction[1]
        if viewer.location == self.target:
            return self.direction[0]
        else:
            raise MisplacedViewerError
        
    def get_name(self, viewer):
        '''Returns a name appropriate to the viewing actor.
        '''
        direction = self.get_relative_direction(viewer)
        return "a door facing "+direction+"."

    def be_entered(self, actor):
        print("Portal entered")
        if actor.location == self.source:
            actor.change_location(self.target)
        elif actor.location == self.target:
            actor.change_location(self.source)
        else:
            raise Exception
        return True, "SILENCE"

class LockedPortal(Portal):
    
    def __init__(self, source, target, sourceDirection, targetDirection, key = None, locked=True, name = "door"):
        super().__init__(source, target, sourceDirection, targetDirection, name = "door")
        self.lock = lock.Lock(key, locked, self.name)
    
    def be_targetted(self, action, actor, *target_list):
        try:
            if action.traverses_portals() and self.lock.locked:
                return False, "The door is locked."
        except AttributeError:
            pass

        return super().be_targetted(action, actor, *target_list)

class MisplacedViewerError(Exception):
    pass
