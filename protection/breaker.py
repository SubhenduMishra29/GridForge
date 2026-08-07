class CircuitBreaker:
    def __init__(self, line):
        self.line = line      # (i, j)
        self.status = "CLOSED"

    def trip(self):
        self.status = "OPEN"

    def close(self):
        self.status = "CLOSED"

    def is_closed(self):
        return self.status == "CLOSED"
