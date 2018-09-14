class Lock():
    
    def __init__(self, key=None, locked=True, name=None):
        self.key = key
        if key != None:
            key.lock = self
        self.locked = locked
        self.name = name
        
    def be_unlocked(self, actor, key):
        if self.locked == False:
            return False, "The {} is already unlocked.".format(self.name)
        elif key == self.key:
            self.locked = False
            return True, "You unlock the {}.".format(self.name)
        else:
            return False, "The key does not fit."
        
    def be_locked(self, actor, key):
        if self.locked == True:
            return False, "The {} is already locked.".format(self.name)
        elif key == self.key:
            self.locked = True
            return True, "You lock the {}.".format(self.name)
        else:
            return False, "The key does not fit."
        
    def forbidden_if_locked_strategy(self, actor, locked_object):
        if self.locked:
            return False, "The {} is locked.".format(self.locked_object.get_name(actor))
        else:
            return True, ""
