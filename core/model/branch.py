"""
branch.py

Defines the Branch model.

A Branch represents a two-terminal element such as:
- Transmission line
- Transformer (future extension)

Uses the standard π-model.
"""

from .base import ElectricalObject
from .terminal import Terminal


class Branch(ElectricalObject):
    """
    Two-terminal network element.
    """

    def __init__(
        self,
        id: str,
        bus_from,
        bus_to,
        r: float,
        x: float,
        b: float = 0.0,
        name: str = ""
    ):
        """
        Parameters
        ----------
        id : str
            Unique identifier

        bus_from : Bus
        bus_to : Bus

        r : float
            Resistance (pu)

        x : float
            Reactance (pu)

        b : float
            Total line charging susceptance (pu)
        """

        super().__init__(id, name)

        # -------------------------
        # Connectivity
        # -------------------------
        self.from_terminal = Terminal(bus_from)
        self.to_terminal = Terminal(bus_to)

        # -------------------------
        # Electrical parameters
        # -------------------------
        self.r = float(r)
        self.x = float(x)
        self.b = float(b)

    # -------------------------
    # Derived quantities
    # -------------------------

    @property
    def impedance(self):
        """
        Series impedance Z = R + jX
        """
        return complex(self.r, self.x)

    @property
    def admittance(self):
        """
        Series admittance Y = 1 / Z
        """
        z = self.impedance
        if z == 0:
            raise ZeroDivisionError(f"Branch {self.id} has zero impedance.")
        return 1 / z

    @property
    def shunt_admittance(self):
        """
        Total shunt admittance (jB)
        """
        return complex(0.0, self.b)

    # -------------------------
    # Helpers
    # -------------------------

    def buses(self):
        """
        Returns (from_bus, to_bus)
        """
        return (
            self.from_terminal.bus,
            self.to_terminal.bus
        )

    # -------------------------
    # Debug
    # -------------------------

    def __repr__(self):
        fb = self.from_terminal.bus.id
        tb = self.to_terminal.bus.id

        return (
            f"<Branch id={self.id}, "
            f"{fb} -> {tb}, "
            f"r={self.r:.4f}, "
            f"x={self.x:.4f}, "
            f"b={self.b:.4f}>"
        )
