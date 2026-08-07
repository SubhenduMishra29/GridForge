class EventManager:
    def __init__(self):
        self.events = []

    def add_event(self, time, action):
        self.events.append((time, action))

    def process(self, t):
        for event_time, action in self.events:
            if abs(t - event_time) < 1e-6:
                action()
