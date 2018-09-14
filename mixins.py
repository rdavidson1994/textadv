from logging import debug
import errors


class ItemTarget:
    def check_traits(self):
        if self.target.has_trait("item"):
            return super().check_traits()
        else:
            template = "You can only {} reasonably sized inanimate objects."
            return False, template.format(self.get_name(self.actor))


class HeldTarget(ItemTarget):
    def check_geometry(self):
        if self.target.has_location(self.actor):
            return super().check_geometry()
        else:
            template = "You must be holding the {} in order to {} it"
            return False, template.format(self.target.get_name(self.actor),
                                          self.get_name(self.actor))


class TargetInReach:
    def check_geometry(self):
        if self.actor.can_reach(self.target):
            return super().check_geometry()
        else:
            template = "You cannot reach the {}."
            return False, template.format(self.target.get_name(self.actor))


class HeldTool:
    def check_geometry(self):
        if self.tool.has_location(self.actor) or self.tool == self.actor:
            return super().check_geometry()
        else:
            template = "You must be holding the {} in order to use it"
            return False, template.format(self.tool.get_name(self.actor))

class Motion:
    """Defines geometry checking and gameplay effects for actions that
    involve moving through a portal. All that's left for subclasses to do
    is specify the get_portal method.
    """
    not_a_portal_string = "That is not an exit."
    no_portal_string = "There is no exit in that direction."
    traverses_portals = True

    def get_portal(self):
        """Returns an inertactable that the action is trying to use
        as a portal. Maybe its a portal, maybe its not. Maybe it doesn't
        connect right. No guarantees. Might raise a PortalNotFoundError.
        """
        pass

    def affect_game(self):
        debug("motion action affected game")
        cage = self.actor.trapping_item
        if cage:
            cage.remove_prisoner(self.actor)
        portal = self.get_portal()
        portal.be_entered(self.actor)

    def check_geometry(self):
        try:
            portal = self.get_portal()
        except errors.PortalNotFound:
            return False, self.no_portal_string
        if self.actor.location.has_thing(portal):
            return super().check_geometry()
        else:
            return False, self.not_a_portal_string
