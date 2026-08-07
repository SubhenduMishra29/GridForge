import numpy as np

class GeneratorDynamics:
    def __init__(self, H, D=0):
        self.H = H      # inertia constant
        self.D = D      # damping
        self.omega = 1  # pu speed
        self.delta = 0  # rotor angle

    def step(self, Pm, Pe, dt):
        M = 2 * self.H

        d2delta = (Pm - Pe - self.D*(self.omega - 1)) / M

        # Integrate (Euler)
        self.omega += d2delta * dt
        self.delta += self.omega * dt

        return self.delta, self.omega
