import numpy as np
from dynamics.swing_equation import SwingEquation


class ClassicalGenerator:
    def __init__(self, bus, M, Pm, E=1.1):
        self.bus = bus
        self.M = M
        self.Pm = Pm
        self.E = E

        self.delta = 0.0
        self.omega = 0.0

        self.swing = SwingEquation(M)

    def electrical_power(self, V):
        """
        Pe = |E||V|/X * sin(delta)
        Simplified model (X assumed = 1)
        """
        return abs(self.E) * abs(V) * np.sin(self.delta)

    def step(self, V, dt):
        Pe = self.electrical_power(V)

        dδ, dω = self.swing.derivatives(
            self.delta,
            self.omega,
            self.Pm,
            Pe
        )

        self.delta += dδ * dt
        self.omega += dω * dt

        return self.delta, self.omega
