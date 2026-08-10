"""
bus.py

Unified Bus Model (STATIC ONLY)

Represents an electrical node in the network.

This class ONLY contains:
- Identity
- Voltage level
- Bus classification

It does NOT contain:
- Solver state (V, theta)
- Power injections
- Connected equipment lists

Those are handled by:
- state.py
- injection models
- topology module
"""

from enum import Enum
from .base import ElectricalObject


class BusType(Enum):
    """
    Bus classification for power flow analysis
    """

    SLACK = 0   # V, θ fixed
    PV = 1      # P, V fixed
    PQ = 2      # P, Q fixed


class Bus(ElectricalObject):
    """
    Static representation of a network bus.
    """

    def __init__(
        self,
        id: str,
        bus_type: BusType,
        base_kv: float,
        name: str = ""
    ):
        super().__init__(id, name)

        # -------------------------
        # Type
        # -------------------------
        if not isinstance(bus_type, BusType):
            raise ValueError("bus_type must be BusType enum")

        self.type = bus_type

        # -------------------------
        # Electrical base
        # -------------------------
        self.base_kv = float(base_kv)

        # -------------------------
        # Shunt (static)
        # -------------------------
        self.g_shunt = 0.0
        self.b_shunt = 0.0

    # -------------------------
    # Type helpers
    # -------------------------

    def is_slack(self):
        return self.type == BusType.SLACK

    def is_pv(self):
        return self.type == BusType.PV

    def is_pq(self):
        return self.type == BusType.PQ

    # -------------------------
    # Debug
    # -------------------------

    def __repr__(self):
        return (
            f"<Bus id={self.id}, "
            f"type={self.type.name}, "
            f"base_kv={self.base_kv}>"
        )
