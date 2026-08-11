```python
# core/model/branch.py

"""
GridForge Branch Model
======================

GridForge Model Layer V2

Defines the common two-terminal electrical Branch model.

A Branch represents a generic two-terminal electrical network element.

Typical implementations include:

- Transmission lines
- Transformers
- Series compensation elements
- FACTS-related branch elements
- Future two-terminal electrical equipment

Responsibilities
----------------
The Branch model provides:

- Two-terminal electrical connectivity.
- Common branch electrical parameters.
- Series impedance representation.
- Series admittance representation.
- Total shunt admittance representation.
- Transformer-compatible tap representation.
- Phase-shift representation.
- Equipment rating storage.
- In-service operational state.
- Basic parameter validation.
- Diagnostic information.

The Branch model does NOT:

- Build Y-bus matrices.
- Perform load-flow calculations.
- Perform Newton-Raphson iterations.
- Calculate short-circuit currents.
- Perform contingency studies.
- Perform protection calculations.
- Perform dynamic simulation.
- Manage GUI geometry.
- Own global network topology.

Numerical interpretation of branch parameters belongs to the
appropriate network/solver/analysis layers.

Connectivity Model
------------------
A Branch contains two Terminal objects:

    from_terminal
    to_terminal

Each Terminal references a Bus.

The Branch therefore provides a common physical connection model:

    Bus
      ▲
      │
    Terminal
      │
    Branch
      │
    Terminal
      │
      ▼
    Bus

The network/container layer remains responsible for registration,
global topology, connectivity validation, and network-wide rules.

Electrical Parameters
---------------------
All electrical parameters are represented in the GridForge model
layer using the established system conventions.

    r
        Series resistance in per-unit.

    x
        Series reactance in per-unit.

    b
        Total shunt susceptance in per-unit.

    tap
        Transformer-compatible magnitude tap ratio.

        A normal transmission line uses 1.0.

    shift
        Phase-shifting angle in radians.

        A normal transmission line uses 0.0.

The exact Y-bus stamping convention, including transformer tap-side
and phase-shift sign convention, belongs to the network/solver
contract and must not be independently implemented here.

Operational State
-----------------
``in_service`` represents whether the branch is currently available
to the network study.

``trip()`` and ``close()`` change only the local operational state.
They do not directly rebuild Y-bus matrices or execute network
studies.

GridForge V2 Status
-------------------
This module is part of the frozen GridForge Model Layer V2 baseline.

Changes require evidence of a genuinely fundamental model requirement
that cannot be satisfied by a specialized branch model or a higher
network/solver layer.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from .base import ElectricalObject
from .terminal import Terminal


# =====================================================================
# BRANCH MODEL
# =====================================================================

class Branch(ElectricalObject):
    """
    Generic two-terminal electrical branch.

    Parameters
    ----------
    id : str
        Unique GridForge object identifier.

    bus_from :
        From-side GridForge Bus.

    bus_to :
        To-side GridForge Bus.

    r : float
        Series resistance in per-unit.

    x : float
        Series reactance in per-unit.

    b : float, optional
        Total shunt susceptance in per-unit.

    name : str, optional
        Human-readable branch name.

    rate_mva : float, optional
        Continuous/nominal thermal rating in MVA.

    tap : float, optional
        Transformer-compatible magnitude tap ratio.

        Normal transmission-line value: 1.0.

    shift : float, optional
        Phase-shifting angle in radians.

        Normal transmission-line value: 0.0.

    Notes
    -----
    ``Branch`` is intentionally generic.

    It stores the common electrical representation required by
    multiple two-terminal network elements. Specialized equipment
    classes such as ``Line`` and ``Transformer`` may add equipment-
    specific parameters without changing the common branch contract.
    """

    def __init__(
        self,
        id: str,
        bus_from,
        bus_to,
        r: float,
        x: float,
        b: float = 0.0,
        name: str = "",
        rate_mva: float = 100.0,
        tap: float = 1.0,
        shift: float = 0.0,
    ):
        super().__init__(
            id=id,
            name=name,
        )

        # =============================================================
        # CONNECTIVITY
        # =============================================================

        if bus_from is None:
            raise ValueError(
                "Branch from-bus cannot be None."
            )

        if bus_to is None:
            raise ValueError(
                "Branch to-bus cannot be None."
            )

        if bus_from is bus_to:
            raise ValueError(
                "Branch cannot connect a bus to itself."
            )

        self.from_terminal = Terminal(bus_from)
        self.to_terminal = Terminal(bus_to)

        # =============================================================
        # ELECTRICAL PARAMETERS
        # =============================================================

        self.r = float(r)
        self.x = float(x)
        self.b = float(b)

        # =============================================================
        # TRANSFORMER-COMPATIBLE PARAMETERS
        # =============================================================

        self.tap = float(tap)
        self.shift = float(shift)

        # =============================================================
        # EQUIPMENT DATA
        # =============================================================

        self.rate_mva = float(rate_mva)

        # =============================================================
        # OPERATIONAL STATE
        # =============================================================

        self.in_service = True

        # =============================================================
        # VALIDATION
        # =============================================================

        self._validate_parameters()

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate_parameters(self) -> None:
        """
        Validate local branch parameters.

        This method performs local parameter validation only.

        System-level rules, such as network connectivity, equipment
        compatibility, and study-specific limits, belong to higher
        layers.
        """

        # A zero series impedance would make the common series
        # admittance representation singular.
        if self.r == 0.0 and self.x == 0.0:
            raise ValueError(
                f"Branch '{self.id}' cannot have zero series impedance."
            )

        # A zero tap ratio is physically and mathematically invalid.
        if self.tap == 0.0:
            raise ValueError(
                f"Branch '{self.id}' tap ratio cannot be zero."
            )

        # Negative thermal ratings are invalid.
        if self.rate_mva < 0.0:
            raise ValueError(
                f"Branch '{self.id}' rate_mva cannot be negative."
            )

    # =================================================================
    # CONNECTIVITY
    # =================================================================

    @property
    def from_bus(self):
        """
        Return the from-side Bus.
        """

        return self.from_terminal.bus

    @property
    def to_bus(self):
        """
        Return the to-side Bus.
        """

        return self.to_terminal.bus

    def buses(self):
        """
        Return the branch endpoint buses.

        Returns
        -------
        tuple
            ``(from_bus, to_bus)``
        """

        return (
            self.from_bus,
            self.to_bus,
        )

    # =================================================================
    # ELECTRICAL PROPERTIES
    # =================================================================

    @property
    def impedance(self) -> complex:
        """
        Return the series impedance.

        Z = R + jX
        """

        return complex(
            self.r,
            self.x,
        )

    @property
    def admittance(self) -> complex:
        """
        Return the series admittance.

        Y = 1 / Z

        Notes
        -----
        This property exposes the mathematical series admittance.

        It does not perform Y-bus assembly or network stamping.
        """

        z = self.impedance

        if z == 0:
            raise ZeroDivisionError(
                f"Branch '{self.id}' has zero impedance."
            )

        return 1.0 / z

    @property
    def shunt_admittance(self) -> complex:
        """
        Return the total branch shunt admittance.

        Y_shunt = jB
        """

        return complex(
            0.0,
            self.b,
        )

    # =================================================================
    # OPERATIONAL STATE
    # =================================================================

    def trip(self) -> None:
        """
        Remove the branch from service.

        This changes only the local operational state.
        """

        self.in_service = False

    def close(self) -> None:
        """
        Return the branch to service.

        This changes only the local operational state.
        """

        self.in_service = True

    # =================================================================
    # STATUS
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """
        Return True when the branch is operational.
        """

        return self.in_service

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

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
            "shift": self.shift,
            "rate_mva": self.rate_mva,
            "in_service": self.in_service,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<Branch "
            f"id={self.id}, "
            f"{self.from_bus.id} -> {self.to_bus.id}, "
            f"r={self.r:.6f}, "
            f"x={self.x:.6f}, "
            f"b={self.b:.6f}, "
            f"in_service={self.in_service}>"
        )
```
