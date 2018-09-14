# #This file contains deprecated Actor methods.
#     def verb_unlock(self, locked_object, key):
#         if locked_object not in self.location.get_interactables():
#             return False, "There is nothing like that here."
#         elif key not in self.items:
#             return False, "You don't have the key you are trying to use."
#         else:
#             try:
#                 return locked_object.be_unlocked(self, key)
#             except AttributeError:
#                 return False, "That object has no lock."
#
#     def verb_lock(self, locked_object, key):
#         if locked_object not in self.location.get_interactables():
#             return False, "There is nothing like that here."
#         elif key not in self.items:
#             return False, "You don't have the key you are trying to use."
#         else:
#             try:
#                 return locked_object.be_locked(self, key)
#             except AttributeError:
#                 return False, "That object has no lock."
#
#
#     def verb_travel(self, direction_string):
#         for portal in self.location.portals:
#             if portal.get_relative_direction(self) == direction_string:
#                 return(self.verb_enter(portal))
#         else:
#             return False, "There is no exit in that direction."
#
#
#     def verb_take(self, target):
#         '''private verb method
#         arg target: an InvItem instance of any kind.
#
#         return (bool, string)
#         bool: True if object was moved into hero's items
#         string: Flavor text to be printed by the parser.
#         '''
#         if target in self.location.get_interactables():
#             try:
#                 return target.be_taken(self)
#             except AttributeError:
#                 return False, "That item can't be taken."
#         else:
#             return False, "That item is not here."
#         #This seems overcomplicated but will expand when more cases get implemented
#
#     def verb_drop(self, target):
#         if target in self.items:
#             try:
#                 return target.be_dropped(self)
#             except AttributeError:
#                 return False, "ERROR: that item can't be dropped!?"
#             return item_response
#         else:
#             return False, "You are not holding that item."
#
#     def verb_enter(self, target):
#         if target in self.location.portals:
#             try:
#                 return target.be_entered(self)
#             except AttributeError:
#                 return False, "That item cannot be entered."
#         else:
#             return False, "That is not a portal."
#
#     def verb_open(self, target):
#         if target in self.location.items:
#             try:
#                 return target.be_opened(self)
#             except AttributeError:
#                 return False, "That item cannot be opened."
#         elif target in self.location.portals:
#             return False, "(You do not need to open and close doors; just make sure they are unlocked and then enter them)"
#         else:
#             return False, "That item cannot be opened."
#
#     def verb_close(self, target):
#         if target in self.location.items:
#             try:
#                 return target.be_closed(self)
#             except AttributeError:
#                 return False, "That item cannot be closed."
#         elif target in self.location.portals:
#             return False, "(You do not need to open and close doors; just make sure they are unlocked and then enter them)"
#         else:
#             return False, "That item cannot be closed."
#
#     def verb_crouch(self):
#         return True, "Yay, you crouched!"
