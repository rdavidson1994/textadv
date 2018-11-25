import logging
from errors import ScheduleError
debug = logging.debug
logging.basicConfig(level=logging.WARNING, format='%(message)s')

class Subscriber:
    def __init__(self, schedule):
        self.schedule = schedule
        self.schedule.add_subscriber(self)
        self.scheduled_event = None
    
    def terminate(self):
        self.schedule.remove_subscriber(self)

    def set_timer(self, callback, time, keyword=""):
        self.schedule.set_timer(callback, time, keyword)

    def cancel_actions(self):
        self.schedule.cancel_actions(self)
    
    def stop_game(self):
        self.schedule.stop_game()
    
    def act(self):
        raise NotImplementedError


class ActorSubscriber(Subscriber):
    def __init__(self, actor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actor = actor

    def act(self):
        action = self.actor.get_action()
        new_event = ActionEvent(action, self.schedule, self)



class Event:
    def __init__(self, schedule, time=0, content=None, instant=False):
        self.content = content
        self.time = time
        self.schedule = schedule
        self.is_instant = instant
        schedule.add_event(self)
        self.subscriber = None

    def __repr__(self):
        return self.content

    def happen(self):
        print("{} happened.".format(self.content))


class TimerEvent(Event):
    def __init__(self, schedule, subscriber, time, callback):
        self.subscriber = subscriber
        self.schedule = schedule
        self.time = time + schedule.current_time
        self.is_instant = False
        self.action = None
        self.schedule.add_event(self)
        self.callback = callback
    
    def happen(self):
        self.callback()

    # def happen(self):
    #     self.subscriber.hear_timer(self.keyword)


class ActionEvent(Event):
    is_cooldown = False

    def __init__(self, action, schedule, subscriber):
        self.is_instant = action.is_instant
        self.schedule = schedule
        self.action = action
        self.subscriber = subscriber
        self.actor = action.actor
        if self.subscriber.scheduled_event:
            print(self.subscriber.scheduled_event)
            raise ScheduleError
        else:
            self.subscriber.scheduled_event = self
        self.time = self.get_time()
        self.schedule.add_event(self)

    def __repr__(self):
        return "Event({})".format(str(self.action))

    def get_time(self):
        return self.action.time_elapsed + self.schedule.current_time

    def happen(self):
        assert self.subscriber.scheduled_event == self
        self.subscriber.scheduled_event = None
        self.actor.attempt_action(self.action)
        try:
            if self.action.cooldown_time == 0:
                self.schedule.grant_action(self.subscriber)
            else:
                CooldownEvent(self.action, self.schedule, self.subscriber)
        except ScheduleError:
            pass


class CooldownEvent(ActionEvent):
    is_cooldown = True

    def __repr__(self):
        return "Cooldown({})".format(str(self.action))

    def get_time(self):
        return self.action.cooldown_time + self.schedule.current_time

    def happen(self):
        assert self.subscriber.scheduled_event == self
        self.subscriber.scheduled_event = None
        self.schedule.grant_action(self.subscriber)


class Schedule:
    def __init__(self):
        self.current_time = 0
        self.event_list = list()
        self.subscribers = list()
        self.stopped_subscribers = list()
        self.new_stopped_subscribers = list()
        self.end_game = False

    def set_timer(self, callback, time, keyword=""):
        TimerEvent(self, callback, time, keyword)

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

    def add_subscriber(self, subscriber):
        self.subscribers.append(subscriber)
        self.stopped_subscribers.append(subscriber)

    def remove_subscriber(self, subscriber):
        self.subscribers.remove(subscriber)

    def cancel_actions(self, subscriber):
        e = subscriber.scheduled_event
        if e is not None and not isinstance(e, CooldownEvent):
            # debug("queue before cancellation {}".format(self.event_list))
            self.event_list = [e for e in self.event_list
                               if e.subscriber != subscriber
                               or e.action is None]
            # debug("queue after cancellation {}".format(self.event_list))
            subscriber.scheduled_event = None
            self.grant_action(subscriber)
            # debug("queue after grant {}".format(self.event_list))
        else:
            pass
            # print("HEY, CANCELLATION WITH NO SCHEDULED EVENT")

    def stop_game(self):
        self.end_game = True

    def grant_action(self, subscriber):
        debug("Action granted")
        if subscriber.scheduled_event:
            raise ScheduleError
        elif self.end_game is False and subscriber in self.subscribers:
            subscriber.act()
        else:
            self.new_stopped_subscribers.append(subscriber)

    def run_game(self):
        self.end_game = False
        for subscriber in self.stopped_subscribers:
            debug("action granted to stopped subscriber")
            self.grant_action(subscriber)
        self.stopped_subscribers = []
        while self.end_game == False and self.event_list:
            # print(f"{self}.end_game is False")
            # debug("{}".format(self.event_list))
            event = self.event_list.pop()
            # debug("{}".format(event))
            if event.subscriber in self.subscribers:
                self.current_time = event.time
                event.happen()
            else:
                pass
                # raise ScheduleError
        print("game over")


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
    print([event.content for event in my_schedule.event_list])
