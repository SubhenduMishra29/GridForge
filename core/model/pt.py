"""
GridForge Potential Transformer Model
=====================================

GridForge Model Layer V2

Defines the canonical Potential Transformer (PT) equipment model.

A PT is a voltage measurement transformer physically connected to the
power-system primary circuit and providing a scaled secondary voltage
for measurement, protection, control, and instrumentation.

Architecture
------------

                    POTENTIAL TRANSFORMER
                             │
               ┌─────────────┴─────────────┐
               │                           │
          PRIMARY SIDE               SECONDARY SIDE
               │                           │
        Electrical circuit          Measurement circuit
               │                           │
        ┌──────┴──────┐             ┌──────┴──────┐
        │             │             │             │
   Primary H1     Primary H2    Secondary X1  Secondary X2
        │             │             │             │
        └──────┬──────┘             └──────┬──────┘
               │                           │
        Power topology              Measurement /
                                    protection

Responsibilities
----------------
This module is responsible for:

- Representing a physical PT.
- Representing its primary electrical terminals.
- Representing its secondary measurement terminals.
- Storing rated primary voltage.
- Storing rated secondary voltage.
- Storing accuracy-class information.
- Storing rated burden.
- Storing polarity.
- Storing service state.
- Providing local state validation.
- Providing diagnostic information.

This module does NOT:

- Build network topology.
- Register terminals with Network.
- Build Y-bus.
- Calculate network voltages.
- Perform relay calculations.
- Perform protection logic.
- Perform measurement simulation.
- Manage GUI objects.

Those responsibilities belong to the appropriate GridForge layers.

GridForge V2 Boundary
---------------------
The PT primary terminals participate in the physical/electrical
power-system graph.

The PT secondary terminals belong to the measurement/protection
domain.

The PT itself does not decide how those interfaces are connected.

GridForge V2 Status
-------------------
Canonical Model Layer V2 equipment.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from enum import Enum
from math import isfinite

from .base import ElectricalObject
from .terminal import Terminal


# =====================================================================
# POLARITY
# =====================================================================

class PTPolarity(Enum):
    """
    Potential-transformer polarity convention.
    """

    H1_H2 = "H1-H2"
    H2_H1 = "H2-H1"


# =====================================================================
# POTENTIAL TRANSFORMER
# =====================================================================

class PotentialTransformer(ElectricalObject):
    """
    GridForge Potential Transformer.

    Parameters
    ----------
    id : str
        Unique GridForge object identifier.

    name : str, optional
        Human-readable PT name.

    rated_primary_voltage : float
        Rated primary voltage in volts.

    rated_secondary_voltage : float
        Rated secondary voltage in volts.

        Typical values may include 100 V or 110 V depending on the
        application and transformer configuration.

    accuracy_class : str, optional
        Measurement/protection accuracy classification.

    rated_burden_va : float, optional
        Rated secondary burden in VA.

    polarity : PTPolarity, optional
        Primary polarity designation.

    in_service : bool, optional
        Equipment service state.

    Notes
    -----
    The PT owns four local terminals:

        primary_h1_terminal
        primary_h2_terminal
        secondary_x1_terminal
        secondary_x2_terminal

    The primary terminals belong to the electrical power-system
    physical graph.

    The secondary terminals belong to the measurement/protection
    domain.
    """

    def __init__(
        self,
        id: str,
        name: str = "",
        rated_primary_voltage: float = 11000.0,
        rated_secondary_voltage: float = 110.0,
        accuracy_class: str = "",
        rated_burden_va: float = 0.0,
        polarity: PTPolarity = PTPolarity.H1_H2,
        in_service: bool = True,
    ):
        super().__init__(
            id=id,
            name=name,
        )

        # -------------------------------------------------------------
        # Validate nameplate data
        # -------------------------------------------------------------

        self._validate_positive(
            rated_primary_voltage,
            "rated_primary_voltage",
        )

        self._validate_positive(
            rated_secondary_voltage,
            "rated_secondary_voltage",
        )

        self._validate_non_negative(
            rated_burden_va,
            "rated_burden_va",
        )

        if not isinstance(accuracy_class, str):
            raise TypeError(
                "accuracy_class must be a string."
            )

        if not isinstance(polarity, PTPolarity):
            raise TypeError(
                "polarity must be a PTPolarity enum value."
            )

        # -------------------------------------------------------------
        # Nameplate
        # -------------------------------------------------------------

        self.rated_primary_voltage = float(
            rated_primary_voltage
        )

        self.rated_secondary_voltage = float(
            rated_secondary_voltage
        )

        self.accuracy_class = accuracy_class

        self.rated_burden_va = float(
            rated_burden_va
        )

        self.polarity = polarity

        # -------------------------------------------------------------
        # Service state
        # -------------------------------------------------------------

        self.in_service = bool(in_service)

        # -------------------------------------------------------------
        # Primary electrical terminals
        # -------------------------------------------------------------

        self.primary_h1_terminal = Terminal(
            owner=self
        )

        self.primary_h2_terminal = Terminal(
            owner=self
        )

        # -------------------------------------------------------------
        # Secondary measurement terminals
        # -------------------------------------------------------------

        self.secondary_x1_terminal = Terminal(
            owner=self
        )

        self.secondary_x2_terminal = Terminal(
            owner=self
        )

        # -------------------------------------------------------------
        # Compatibility aliases
        # -------------------------------------------------------------

        self.primary_a = self.primary_h1_terminal
        self.primary_b = self.primary_h2_terminal

        self.secondary_x1 = self.secondary_x1_terminal
        self.secondary_x2 = self.secondary_x2_terminal

    # =================================================================
    # VALIDATION
    # =================================================================

    @staticmethod
    def _validate_positive(
        value: float,
        field_name: str,
    ) -> None:
        """
        Validate a strictly positive numerical value.
        """

        value = float(value)

        if not isfinite(value) or value <= 0.0:
            raise ValueError(
                f"{field_name} must be finite and greater than zero."
            )

    # -----------------------------------------------------------------

    @staticmethod
    def _validate_non_negative(
        value: float,
        field_name: str,
    ) -> None:
        """
        Validate a non-negative numerical value.
        """

        value = float(value)

        if not isfinite(value) or value < 0.0:
            raise ValueError(
                f"{field_name} must be finite and non-negative."
            )

    # =================================================================
    # RATIO
    # =================================================================

    @property
    def ratio(self) -> float:
        """
        Return the nominal voltage transformation ratio.

        Defined as:

            primary voltage / secondary voltage
        """

        return (
            self.rated_primary_voltage
            / self.rated_secondary_voltage
        )

    # =================================================================
    # TERMINAL ACCESS
    # =================================================================

    @property
    def primary_terminals(self) -> tuple[Terminal, Terminal]:
        """
        Return the two primary electrical terminals.
        """

        return (
            self.primary_h1_terminal,
            self.primary_h2_terminal,
        )

    # -----------------------------------------------------------------

    @property
    def secondary_terminals(self) -> tuple[Terminal, Terminal]:
        """
        Return the two secondary measurement terminals.
        """

        return (
            self.secondary_x1_terminal,
            self.secondary_x2_terminal,
        )

    # =================================================================
    # STATE
    # =================================================================

    def set_in_service(
        self,
        in_service: bool,
    ) -> None:
        """
        Set the PT service state.

        This changes only local equipment state.

        Network topology interpretation belongs to core/network.
        """

        self.in_service = bool(in_service)

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return a compact PT summary.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": "PotentialTransformer",
            "in_service": self.in_service,
            "rated_primary_voltage": (
                self.rated_primary_voltage
            ),
            "rated_secondary_voltage": (
                self.rated_secondary_voltage
            ),
            "ratio": self.ratio,
            "accuracy_class": self.accuracy_class,
            "rated_burden_va": self.rated_burden_va,
            "polarity": self.polarity.value,
            "primary_h1": (
                self.primary_h1_terminal.endpoint_id
            ),
            "primary_h2": (
                self.primary_h2_terminal.endpoint_id
            ),
            "secondary_x1": (
                self.secondary_x1_terminal.endpoint_id
            ),
            "secondary_x2": (
                self.secondary_x2_terminal.endpoint_id
            ),
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<PotentialTransformer "
            f"id={self.id}, "
            f"ratio={self.rated_primary_voltage:.3f}/"
            f"{self.rated_secondary_voltage:.3f}, "
            f"accuracy={self.accuracy_class!r}, "
            f"in_service={self.in_service}>"
        )
