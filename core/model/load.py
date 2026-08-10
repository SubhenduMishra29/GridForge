"""
load.py

Defines the Load model.

A Load represents a constant power consumption device
connected to a bus.

This is a PQ-type injection:
- Active power (P) is specified
- Reactive power (Q) is specified

Sign Convention:
----------------
Loads consume power, so:
get_power() returns (-P, -Q)
"""

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Load(ElectricalObject, Injection):
    """
    Constant power load model.
    """

    def __init__(
        self,
        id: str,
        bus,
        p: float,
        q: float,
        name: str = ""
    ):
        """
        Parameters
        ----------
        id : str
            Unique identifier

        bus : Bus
            Bus to which load is connected

        p : float
            Active power demand (positive value, pu)

        q : float
            Reactive power demand (positive value, pu)
        """

        super().__init__(id, name)

        # -------------------------
        # Connection
        # -------------------------
        self.terminal = Terminal(bus)

        # -------------------------
        # Power demand (positive values)
        # -------------------------
        self.p = float(p)
        self.q = float(q)

    # -------------------------
    # Injection interface
    # -------------------------

    def get_power(self):
        """
        Returns negative power (consumption).
        """
        return -self.p, -self.q

    # -------------------------
    # Update methods
    # -------------------------

    def set_power(self, p: float, q: float):
        """
        Update load demand.
        """
        self.p = float(p)
        self.q = float(q)

    # -------------------------
    # Debug
    # -------------------------

    def __repr__(self):
        return (
            f"<Load id={self.id}, "
            f"bus={self.terminal.bus.id}, "
            f"P={self.p:.4f}, "
            f"Q={self.q:.4f}>"
        )
