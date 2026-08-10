```python
"""
branch.py

GridForge Branch Model
======================

File:
    core/model/branch.py

Defines the generic two-terminal Branch model.

A Branch represents a two-terminal electrical network element
such as:

    - Transmission line
    - Transformer-compatible branch
    - Future specialized branch models

The branch model stores electrical parameters and topology only.

Numerical analysis such as:

    - Ybus construction
    - Power-flow calculations
    - Short-circuit calculations
    - Contingency analysis

belongs to the solver/network-analysis layers.

Electrical convention
---------------------

Series impedance:

    Z = R + jX

Series admittance:

    Y = 1 / Z

Total shunt susceptance:

    B

The standard π-model interpretation is:

    jB/2 at the from terminal
    jB/2 at the to terminal

The branch stores the total ``b`` value. Splitting into terminal
shunts is the responsibility of the Ybus builder.

Transformer-compatible parameters are retained:

    tap
    shift

These are not applied inside the Branch model.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from .base import ElectricalObject
from .terminal import Terminal


class Branch(ElectricalObject):
    """
    Generic two-terminal electrical branch.

    Parameters
    ----------
    id:
        Unique branch identifier.

    bus_from:
        Sending/from Bus.

    bus_to:
        Receiving/to Bus.

    r:
        Series resistance in per-unit.

    x:
        Series reactance in per-unit.

    b:
        Total shunt susceptance in per-unit.

    tap:
        Off-nominal transformer tap ratio.

        Default:
            1.0

    shift:
        Transformer phase-shift angle in radians.

        Default:
            0.0

    name:
        Human-readable branch name.

    Notes
    -----
    ``tap`` and ``shift`` are stored here so that the same Branch
    abstraction can support transformer-compatible Ybus assembly.

    The Branch class itself does not apply the transformer
    equations.
    """

    def __init__(
        self,
        id: str,
        bus_from,
        bus_to,
        r: float,
        x: float,
        b: float = 0.0,
        tap: float = 1.0,
        shift: float = 0.0,
        name: str = ""
    ):
        super().__init__(
            id,
            name
        )

        # =========================================================
        # BASIC VALIDATION
        # =========================================================

        if bus_from is None:
            raise ValueError(
                f"Branch '{id}' requires a valid from-bus."
            )

        if bus_to is None:
            raise ValueError(
                f"Branch '{id}' requires a valid to-bus."
            )

        if bus_from is bus_to:
            raise ValueError(
                f"Branch '{id}' cannot connect a bus to itself."
            )

        # ---------------------------------------------------------
        # Electrical parameters
        # ---------------------------------------------------------

        self.r = float(r)
        self.x = float(x)
        self.b = float(b)

        # ---------------------------------------------------------
        # Transformer-compatible parameters
        # ---------------------------------------------------------

        self.tap = float(tap)
        self.shift = float(shift)

        self._validate_parameters()

        # =========================================================
        # TOPOLOGY
        # =========================================================

        self.from_terminal = Terminal(
            bus_from
        )

        self.to_terminal = Terminal(
            bus_to
        )

    # =============================================================
    # VALIDATION
    # =============================================================

    def _validate_parameters(self) -> None:
        """
        Validate branch electrical parameters.
        """

        if not (
            self.r == self.r
            and self.x == self.x
            and self.b == self.b
            and self.tap == self.tap
            and self.shift == self.shift
        ):
            raise ValueError(
                f"Branch '{self.id}' contains NaN parameters."
            )

        if self.tap <= 0.0:
            raise ValueError(
                f"Branch '{self.id}' tap ratio must be greater than zero."
            )

    # =============================================================
    # BUS ACCESS
    # =============================================================

    @property
    def from_bus(self):
        """
        Return the from/sending bus.
        """

        return self.from_terminal.bus

    @property
    def to_bus(self):
        """
        Return the to/receiving bus.
        """

        return self.to_terminal.bus

    def buses(self):
        """
        Return the branch terminal buses.

        Returns
        -------
        tuple
            ``(from_bus, to_bus)``
        """

        return (
            self.from_bus,
            self.to_bus
        )

    # =============================================================
    # ELECTRICAL DERIVED QUANTITIES
    # =============================================================

    @property
    def impedance(self) -> complex:
        """
        Return the series impedance.

        Z = R + jX
        """

        z = complex(
            self.r,
            self.x
        )

        if abs(z) == 0.0:
            raise ZeroDivisionError(
                f"Branch '{self.id}' has zero series impedance."
            )

        return z

    @property
    def admittance(self) -> complex:
        """
        Return the series admittance.

        Y = 1 / Z
        """

        return 1.0 / self.impedance

    @property
    def shunt_admittance(self) -> complex:
        """
        Return the total branch shunt admittance.

        For the standard π-model:

            Y_shunt = jB

        The Ybus builder is responsible for applying B/2 to
        each terminal.
        """

        return complex(
            0.0,
            self.b
        )

    @property
    def half_shunt_admittance(self) -> complex:
        """
        Return the shunt admittance associated with one terminal.

        For a symmetric π-model:

            Y_shunt_terminal = jB / 2
        """

        return complex(
            0.0,
            self.b / 2.0
        )

    # =============================================================
    # PARAMETER UPDATES
    # =============================================================

    def set_parameters(
        self,
        r: float | None = None,
        x: float | None = None,
        b: float | None = None
    ) -> None:
        """
        Update branch electrical parameters.

        Only explicitly supplied parameters are changed.
        """

        if r is not None:
            self.r = float(r)

        if x is not None:
            self.x = float(x)

        if b is not None:
            self.b = float(b)

        self._validate_parameters()

    def set_transformer_parameters(
        self,
        tap: float | None = None,
        shift: float | None = None
    ) -> None:
        """
        Update transformer-compatible parameters.

        These parameters are stored by the model but interpreted
        by the Ybus/network-analysis layer.
        """

        if tap is not None:
            tap = float(tap)

            if tap <= 0.0:
                raise ValueError(
                    "Tap ratio must be greater than zero."
                )

            self.tap = tap

        if shift is not None:
            self.shift = float(
                shift
            )

        self._validate_parameters()

    # =============================================================
    # SUMMARY
    # =============================================================

    def summary(self) -> dict:
        """
        Return structured branch information.
        """

        return {
            "id": self.id,
            "name": self.name,
            "from_bus": self.from_bus.id,
            "to_bus": self.to_bus.id,
            "r": self.r,
            "x": self.x,
            "b": self.b,
            "tap": self.tap,
            "shift": self.shift
        }

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            f"<Branch "
            f"id={self.id}, "
            f"{self.from_bus.id} -> {self.to_bus.id}, "
            f"r={self.r:.6f}, "
            f"x={self.x:.6f}, "
            f"b={self.b:.6f}, "
            f"tap={self.tap:.6f}, "
            f"shift={self.shift:.6f}>"
        )
```
