```python
"""
GridForge Shunt Model
=====================

File:
    core/model/shunt.py

Defines the GridForge shunt-element model.

A Shunt represents a passive admittance connected to a single bus.

Supported models
----------------
General shunt admittance:

    Y = G + jB

where:

    G = conductance in per-unit
    B = susceptance in per-unit

Typical applications
--------------------
- Capacitor banks
- Reactor banks
- Fixed shunt compensation
- General network shunt admittance

Sign convention
---------------
The electrical admittance is stored directly as:

    Y_shunt = G + jB

Therefore:

    B > 0
        Capacitive shunt

    B < 0
        Inductive/reactive shunt

The Ybus builder is responsible for incorporating this admittance
into the network admittance matrix.

The Shunt model does NOT:
    - Build Ybus.
    - Calculate bus power.
    - Perform load flow.
    - Perform short-circuit calculations.
    - Perform voltage-control calculations.
    - Perform protection calculations.

Those responsibilities belong to the appropriate network,
solver, or analysis layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from .base import ElectricalObject
from .terminal import Terminal


class Shunt(ElectricalObject):
    """
    GridForge passive shunt admittance.

    Parameters
    ----------
    id:
        Unique shunt identifier.

    bus:
        Bus object to which the shunt is connected.

    g:
        Conductance in per-unit.

    b:
        Susceptance in per-unit.

    name:
        Human-readable shunt name.

    Notes
    -----
    At least one of ``g`` or ``b`` must be non-zero.

    The complete shunt admittance is:

        Y = G + jB
    """

    def __init__(
        self,
        id: str,
        bus,
        g: float = 0.0,
        b: float = 0.0,
        name: str = "",
    ):
        """
        Initialize a shunt element.
        """

        super().__init__(
            id=id,
            name=name
        )

        # ---------------------------------------------------------
        # Connectivity
        # ---------------------------------------------------------

        self.terminal = Terminal(bus)

        # ---------------------------------------------------------
        # Electrical parameters
        # ---------------------------------------------------------

        self.g = float(g)
        self.b = float(b)

        # ---------------------------------------------------------
        # Operational state
        # ---------------------------------------------------------

        self.in_service = True

        self._validate_parameters()

    # =============================================================
    # BUS ACCESS
    # =============================================================

    @property
    def bus(self):
        """
        Return the connected Bus.
        """

        return self.terminal.bus

    # =============================================================
    # COMPATIBILITY ALIASES
    # =============================================================

    @property
    def g_pu(self) -> float:
        """
        Conductance in per-unit.

        Compatibility alias for ``g``.
        """

        return self.g

    @property
    def b_pu(self) -> float:
        """
        Susceptance in per-unit.

        Compatibility alias for ``b``.
        """

        return self.b

    # =============================================================
    # DERIVED ELECTRICAL QUANTITIES
    # =============================================================

    @property
    def y_pu(self) -> complex:
        """
        Return the shunt admittance.

        Y = G + jB
        """

        return complex(
            self.g,
            self.b
        )

    @property
    def admittance(self) -> complex:
        """
        Alias for ``y_pu``.
        """

        return self.y_pu

    # =============================================================
    # TYPE IDENTIFICATION
    # =============================================================

    @property
    def is_capacitive(self) -> bool:
        """
        Return True when the shunt has positive susceptance.
        """

        return self.b > 0.0

    @property
    def is_inductive(self) -> bool:
        """
        Return True when the shunt has negative susceptance.
        """

        return self.b < 0.0

    # =============================================================
    # PARAMETER CONTROL
    # =============================================================

    def set_admittance(
        self,
        g: float | None = None,
        b: float | None = None
    ) -> None:
        """
        Update the shunt admittance.

        Only supplied values are changed.

        Parameters
        ----------
        g:
            Conductance in per-unit.

        b:
            Susceptance in per-unit.
        """

        new_g = (
            self.g
            if g is None
            else float(g)
        )

        new_b = (
            self.b
            if b is None
            else float(b)
        )

        if new_g == 0.0 and new_b == 0.0:
            raise ValueError(
                "Shunt must have non-zero admittance"
            )

        self.g = new_g
        self.b = new_b

    # =============================================================
    # STATUS CONTROL
    # =============================================================

    def trip(self) -> None:
        """
        Remove the shunt from service.

        The numerical Ybus builder should ignore the element while
        ``in_service`` is False.
        """

        self.in_service = False

    def close(self) -> None:
        """
        Return the shunt to service.
        """

        self.in_service = True

    # =============================================================
    # VALIDATION
    # =============================================================

    def _validate_parameters(self) -> None:
        """
        Validate shunt electrical parameters.
        """

        if (
            self.g == 0.0
            and self.b == 0.0
        ):
            raise ValueError(
                "Shunt must have non-zero admittance"
            )

    # =============================================================
    # SUMMARY
    # =============================================================

    def summary(self) -> dict:
        """
        Return structured shunt information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": "shunt",
            "bus": self.bus.id,
            "g_pu": self.g,
            "b_pu": self.b,
            "y_pu": self.y_pu,
            "in_service": self.in_service,
        }

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self) -> str:
        return (
            f"<Shunt "
            f"id={self.id}, "
            f"bus={self.bus.id}, "
            f"Y={self.g:.6f}"
            f"+j{self.b:.6f}, "
            f"in_service={self.in_service}>"
        )
```
