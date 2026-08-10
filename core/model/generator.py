"""
generator.py

Defines the Generator model.

A Generator represents a controllable power injection.

Supports:
- Active power injection (P)
- Reactive power injection (Q)
- Voltage setpoint (for PV buses)

Future extensions:
- Reactive limits enforcement
- Slack behavior
- Capability curves
"""

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Generator(ElectricalObject, Injection):
    """
    Generator model.
    """

    def __init__(
        self,
        id: str,
        bus,
        p: float,
        q: float,
        vm_setpoint: float = 1.0,
        q_limits: tuple = (-float("inf"), float("inf")),
        name: str = ""
    ):
        super().__init__(id, name)

        # Connection
        self.terminal = Terminal(bus)

        # Power injection
        self.p = float(p)
        self.q = float(q)

        # Voltage control
        self.vm_setpoint = float(vm_setpoint)

        # Reactive limits
        self.q_min = float(q_limits[0])
        self.q_max = float(q_limits[1])

    # -------------------------
    # Injection interface
    # -------------------------

    def get_power(self):
        """
        Returns injected power.
        """
        return self.p, self.q

    @property
    def bus(self):
        return self.terminal.bus

    # -------------------------
    # Control updates
    # -------------------------

    def set_power(self, p: float, q: float):
        self.p = float(p)
        self.q = float(q)

    def set_voltage_setpoint(self, vm: float):
        self.vm_setpoint = float(vm)

    # -------------------------
    # Limits
    # -------------------------

    def enforce_q_limits(self):
        """
        Clamp Q within limits.
        """
        if self.q < self.q_min:
            self.q = self.q_min
        elif self.q > self.q_max:
            self.q = self.q_max

    # -------------------------
    # Debug
    # -------------------------

    def __repr__(self):
        return (
            f"<Generator id={self.id}, "
            f"bus={self.bus.id}, "
            f"P={self.p:.4f}, "
            f"Q={self.q:.4f}, "
            f"Vset={self.vm_setpoint:.4f}>"
        )
