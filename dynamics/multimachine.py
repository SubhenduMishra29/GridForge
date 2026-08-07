import numpy as np

class Generator:
    def __init__(self, bus, H, Pm, E=1.1):
        self.bus = bus
        self.H = H
        self.Pm = Pm
        self.E = E

        self.delta = 0.0
        self.omega = 1.0

    def step(self, Pe, dt):
        M = 2 * self.H

        d2delta = (self.Pm - Pe) / M

        self.omega += d2delta * dt
        self.delta += self.omega * dt
