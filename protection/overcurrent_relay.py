import numpy as np

class OvercurrentRelay:
    def __init__(self, pickup, K=0.14, n=0.02):
        self.I_pickup = pickup
        self.K = K
        self.n = n

    def operating_time(self, I):
        if I <= self.I_pickup:
            return np.inf

        ratio = I / self.I_pickup
        return self.K / (ratio**self.n - 1)

    def check_trip(self, I):
        t = self.operating_time(I)

        if t == np.inf:
            return "No Trip"
        return f"Trip in {t:.3f}s"
