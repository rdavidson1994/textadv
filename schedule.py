import logging
from errors import ScheduleError
debug = logging.debug
logging.basicConfig(level=logging.WARNING, format='%(message)s')


class Event:
    def __init__(self, schedule, time=0, content=None, instant=False):
        self.content = content
        self.time = time
        self.schedule = schedule
        self.is_instant = instant
        schedule.add_event(self)
        self.actor = None

    def __repr__(self):
        return self.content

    def happen(self):
        # prin("{} happened.".format(self.content))
        pass


class TimerEvent(Event):
    def __init__(self, schedule, actor, time, keyword=None, callback=None):
        self.keyword = keyword
        self.callback = callback
        self.actor = actor
        self.schedule = schedule
        self.time = time + schedule.current_time
        self.is_instant = False
        self.action = None
        self.schedule.add_event(self)
        if self.keyword is None and self.callback is None:
            raise Exception("To set a timer, you need a keyword or a callback. You passed neither.")
        if self.keyword and self.callback:
            raise Exception("You passed both a keyword and a callback. This is not supported.")


    def happen(self):
        if self.keyword:
            self.actor.hear_timer(self.keyword)
        elif self.callback:
            self.callback()
        else:
            raise Exception("Hey! A timer had no callback or keyword.")


class ActionEvent(Event):
    is_cooldown = False

    def __init__(self, action):
        self.is_instant = action.is_instant
        self.schedule = action.actor.schedule
        self.action = action
        self.actor = action.actor
        if self.actor.scheduled_event:
            raise ScheduleError
        else:
            self.actor.scheduled_event = self
        self.time = self.get_time()
        self.schedule.add_event(self)

    def __repr__(self):
        return "Event({})".format(str(self.action))

    def get_time(self):
        return self.action.time_elapsed + self.schedule.current_time

    def happen(self):
        assert self.actor.scheduled_event == self
        self.actor.scheduled_event = None
        self.actor.attempt_action(self.action)
        try:
            if self.action.cooldown_time == 0:
                self.schedule.grant_action(self.actor)
            else:
                new_event = CooldownEvent(self.action)
        except ScheduleError:
            pass


class CooldownEvent(ActionEvent):
    is_cooldown = True

    def __repr__(self):
        return "Cooldown({})".format(str(self.action))

    def get_time(self):
        return self.action.cooldown_time + self.schedule.current_time

    def happen(self):
        assert self.actor.scheduled_event == self
        self.actor.scheduled_event = None
        self.schedule.grant_action(self.actor)


class Schedule:
    def __init__(self):
        self.current_time = 0
        self.event_list = list()
        self.actors = list()
        self.stopped_actors = list()
        self.new_stopped_actors = list()
        self.end_game = False

    def set_timer(self, actor, time, keyword=None, callback=None):
        return TimerEvent(self, actor, time, keyword, callback)

    def add_event(self, new_event):
        if new_event.is_instant:
            self.event_list.append(new_event)
        else:
            i = 0
            try:
                while self.event_list[i].time > new_event.time:
                    i += 1
                # if self.event_list[i].time == new_event.time:
                # new_event.time += 1
                self.event_list.insert(i, new_event)
            except IndexError:
                self.event_list.append(new_event)

    def add_actor(self, actor):
        self.actors.append(actor)
        if actor not in self.stopped_actors:
            self.stopped_actors.append(actor)

    def remove_actor(self, actor):
        self.actors.remove(actor)
        self.event_list = [e for e in self.event_list if e.actor != actor]
        actor.scheduled_event = None

    def cancel_event(self, event):
        try:
            self.event_list.remove(event)
        except IndexError:
            pass

    def cancel_actions(self, actor):
        e = actor.scheduled_event
        if e is not None and not isinstance(e, CooldownEvent):
            # debug("queue before cancellation {}".format(self.event_list))
            self.event_list = [e for e in self.event_list
                               if e.actor != actor
                               or e.action is None]
            # debug("queue after cancellation {}".format(self.event_list))
            actor.scheduled_event = None
            self.grant_action(actor)
            # debug("queue after grant {}".format(self.event_list))
        else:
            pass
            # print_("HEY, CANCELLATION WITH NO SCHEDULED EVENT")

    def stop_game(self):
        self.end_game = True

    def grant_action(self, actor):
        debug("Action granted")
        if actor.scheduled_event:
            raise ScheduleError
        elif self.end_game == False and actor in self.actors:
            action = actor.get_action()
            ActionEvent(action)
        else:
            self.new_stopped_actors.append(actor)

    def run_game(self, duration=None):
        if duration is not None:
            end_time = self.current_time + duration
        else:
            end_time = None
        self.end_game = False

        while (
            not self.end_game
            and (self.event_list or self.stopped_actors)
            and (end_time is None or self.current_time < end_time)
        ):
            if self.stopped_actors:
                for actor in self.stopped_actors:
                    if actor in self.actors:
                        self.grant_action(actor)
                self.stopped_actors = list()
            event = self.event_list.pop()
            if event.actor in self.actors:
                self.current_time = event.time
                event.happen()
            else:
                pass


class DefaultSchedule(Schedule):
    default_schedule = None

    def __new__(cls):
        if cls.default_schedule is None:
            cls.default_schedule = super().__new__(cls)
        return cls.default_schedule


if __name__ == "__main__":
    my_schedule = Schedule()
    e0 = Event(my_schedule, 0, "A")
    e1 = Event(my_schedule, 1000, "B")
    e2 = Event(my_schedule, 0, "Before A", True)
    e3 = Event(my_schedule, 2000, "C")
    e4 = Event(my_schedule, 2000, "D")
    # prin([event.content for event in my_schedule.event_list])
