import action


class BeforeHandler:
    def __init__(self, class_triggers=(), attribute_triggers=()):
        self.class_triggers = list(class_triggers)
        self.attribute_triggers = list(attribute_triggers)

    def __call__(self, event_type):
        def decorator(function):
            if isinstance(event_type, action.ActionMeta):
                self.class_triggers.append((event_type, function))
            else:
                self.attribute_triggers.append((event_type, function))
            return function
        return decorator

    def copy(self):
        return BeforeHandler(self.class_triggers, self.attribute_triggers)

    @staticmethod
    def loose_call(sender, function):
        try:
            return function()
        except TypeError:
            return function(self=sender)

    def handle(self, sender, act):
        for trigger, function in self.class_triggers:
            if isinstance(act, trigger):
                return self.loose_call(sender, function)
        for string, function in self.attribute_triggers:
            try:
                test_value = getattr(act, string)()
            except AttributeError:
                test_value = False
            if test_value:
                return self.loose_call(sender, function)


class OnHandler(BeforeHandler):
    pass


class AfterHandler(BeforeHandler):
    pass


def get_handlers():

    return BeforeHandler(), OnHandler(), AfterHandler()


# class ThingMeta(type):
#     def __init__(cls, name, bases, dct):
#         try:
#             cls.before.cls = cls
#         except AttributeError:
#             pass


class Thing:
    # Or should it be: idea, before, on, after
    handlers = before, on, after = get_handlers()

    @classmethod
    def copy_handlers(cls):
        return tuple(h.copy() for h in cls.handlers)

    def handle_before(self, event):
        # Called during action resolution
        try:
            return self.before.handle(self, event)
        except AttributeError:
            pass


class Cage(Thing):
    handlers = before, on, after = Thing.copy_handlers()

    @before("wat_action")
    def f(self, act):
        print("Wat")

    @before("huh_action")
    def f(self, act):
        print("Huh")