import numpy as np

class IDMT_Relay:
    CURVES = {
        "SI": {"K": 0.14, "alpha": 0.02},
        "VI": {"K": 13.5, "alpha": 1},
        "EI": {"K": 80, "alpha": 2}
    }

    def __init__(self, pickup, TMS=0.1, curve="SI"):
        self.I_pickup = pickup
        self.TMS = TMS
        self.K = self.CURVES[curve]["K"]
        self.alpha = self.CURVES[curve]["alpha"]
        self.curve = curve

    def trip_time(self, I):
        if I <= self.I_pickup:
            return np.inf

        ratio = I / self.I_pickup
        return (self.K * self.TMS) / (ratio**self.alpha - 1)
