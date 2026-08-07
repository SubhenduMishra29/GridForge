# ============================================
# File: gridforge/dynamics/multimachine.py
# Description: Multi-machine transient stability
# ============================================

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


def electrical_power_all(generators, Ybus):
    n = len(generators)
    Pe = np.zeros(n)

    for i in range(n):
        for j in range(n):
            Ei = generators[i].E
            Ej = generators[j].E

            G = Ybus[i, j].real
            B = Ybus[i, j].imag

            delta_i = generators[i].delta
            delta_j = generators[j].delta

            Pe[i] += Ei * Ej * (
                G * np.cos(delta_i - delta_j) +
                B * np.sin(delta_i - delta_j)
            )

    return Pe


class MultiMachineSimulator:
    def __init__(self, generators, Ybus_pre, Ybus_fault, Ybus_post):
        self.generators = generators
        self.Ybus_pre = Ybus_pre
        self.Ybus_fault = Ybus_fault
        self.Ybus_post = Ybus_post

    def simulate(self, t_fault, t_clear, t_end, dt=0.01):
        t = 0
        results = []

        while t < t_end:

            if t < t_fault:
                Ybus = self.Ybus_pre
            elif t < t_clear:
                Ybus = self.Ybus_fault
            else:
                Ybus = self.Ybus_post

            Pe = electrical_power_all(self.generators, Ybus)

            for i, gen in enumerate(self.generators):
                gen.step(Pe[i], dt)

            results.append({
                "time": t,
                "delta": [g.delta for g in self.generators],
                "omega": [g.omega for g in self.generators]
            })

            t += dt

        return results


def check_stability(results, threshold=np.pi):
    for state in results:
        deltas = state["delta"]

        for i in range(len(deltas)):
            for j in range(i+1, len(deltas)):
                if abs(deltas[i] - deltas[j]) > threshold:
                    return False

    return True
