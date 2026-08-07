import numpy as np


class OvercurrentRelay:
    """
    IEC 60255 Inverse Time Overcurrent Relay
    """

    IEC_CURVES = {
        "IEC_STANDARD_INVERSE": (0.14, 0.02),
        "IEC_VERY_INVERSE": (13.5, 1.0),
        "IEC_EXTREMELY_INVERSE": (80.0, 2.0),
    }

    def __init__(self, pickup, TMS=0.1, curve="IEC_STANDARD_INVERSE"):
        self.pickup = pickup
        self.TMS = TMS
        self.k, self.alpha = self.IEC_CURVES[curve]

        # Dynamic state
        self.timer = 0.0
        self.tripped = False

    def reset(self):
        self.timer = 0.0
        self.tripped = False

    def operate_time(self, I):
        """
        IEC curve:
        t = TMS * k / ((I/Ip)^alpha - 1)
        """
        M = I / self.pickup

        if M <= 1:
            return np.inf

        return self.TMS * self.k / (M**self.alpha - 1)

    def step(self, I, dt):
        """
        Time-domain evaluation
        """
        if self.tripped:
            return True

        t_operate = self.operate_time(I)

        if t_operate == np.inf:
            self.timer = 0.0
            return False

        self.timer += dt

        if self.timer >= t_operate:
            self.tripped = True
            return True

        return False
