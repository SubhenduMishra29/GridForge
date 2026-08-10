"""
state.py

Holds all dynamic / solver-updated quantities for the grid.

This module separates numerical state from the static model.

Key design:
-----------
- No topology
- No electrical definitions
- No solver logic
- Pure data containers

Used by:
- Power flow solvers
- State estimation
- Time-domain simulation (future)
"""


class BusState:
    """
    Dynamic state of a bus.

    Contains all solver-updated variables.
    """

    def __init__(
        self,
        vm: float = 1.0,   # voltage magnitude (per-unit)
        va: float = 0.0,   # voltage angle (radians)

        p: float = 0.0,    # net active power injection (pu)
        q: float = 0.0     # net reactive power injection (pu)
    ):
        # -------------------------
        # Voltage state
        # -------------------------
        self.vm = float(vm)
        self.va = float(va)

        # -------------------------
        # Power injection state
        # -------------------------
        self.p = float(p)
        self.q = float(q)

    # -------------------------
    # Convenience updates
    # -------------------------

    def set_voltage(self, vm: float, va: float):
        """
        Update voltage state.
        """
        self.vm = float(vm)
        self.va = float(va)

    def set_power(self, p: float, q: float):
        """
        Update power injection state.
        """
        self.p = float(p)
        self.q = float(q)

    def copy(self):
        """
        Create a deep copy of state (useful for iterations).
        """
        return BusState(
            vm=self.vm,
            va=self.va,
            p=self.p,
            q=self.q
        )

    # -------------------------
    # Debug
    # -------------------------

    def __repr__(self):
        return (
            f"<BusState "
            f"Vm={self.vm:.4f}, "
            f"Va={self.va:.4f}, "
            f"P={self.p:.4f}, "
            f"Q={self.q:.4f}>"
        )
