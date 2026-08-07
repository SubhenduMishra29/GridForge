import numpy as np


class SwingEquation:
    """
    Classical swing equation:
    dδ/dt = ω
    dω/dt = (Pm - Pe) / M
    """

    def __init__(self, M, D=0.0):
        self.M = M
        self.D = D

    def derivatives(self, delta, omega, Pm, Pe):
        ddelta_dt = omega
        domega_dt = (Pm - Pe - self.D * omega) / self.M
        return ddelta_dt, domega_dt
