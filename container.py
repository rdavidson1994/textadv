import game_object
import lock
class Container(interactable.InvItem):
    def __init__(self, location, name, is_open = False, short_name=None):
        super().__init__(location, name, short_name)
        self.items = []
        self.is_open = is_open
        self.contents_visible_when_closed = False
    def be_opened(self, actor):
        if self.is_open:
            return False, "The {} is already open.".format(self.name)
        else:
            self.is_open = True
            return True, "You open the {}.".format(self.name)
    def be_closed(self, actor):
        if self.is_open:
            self.is_open = False
            return True, "You close the {}.".format(self.name)                      
        else:
            return False, "The {} is already closed.".format(self.name)

class LockedContainer(Container):
    def __init__(self, location, name, key=None, is_open = False, locked = True, short_name = None):
        super().__init__(location, name, is_open, short_name)
        self.lock = lock.Lock(key, locked, self.name)
        assert not(self.is_open and self.lock.locked)
    def be_locked(self, actor, key):
        if self.is_open:
            return False, "You must first close the {}.".format(self.name)
        else:
            return self.lock.be_locked(actor, key)
    def be_unlocked(self, actor, key):
        return self.lock.be_unlocked(actor, key)

    
