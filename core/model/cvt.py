"""
GridForge CVT Model
===================

GridForge Model Layer V2

Defines the Capacitive Voltage Transformer (CVT) equipment model.

A CVT is an instrument transformer used to reproduce a scaled,
galvanically isolated representation of a high-voltage electrical
quantity for:

- voltage measurement
- protection
- metering
- control
- synchronization
- power-system monitoring

Architectural Boundary
----------------------

The CVT is a physical equipment model.

It stores:

- equipment identity
- service state
- rated primary voltage
- rated secondary voltage
- transformation ratio
- accuracy information
- burden information
- nominal frequency
- capacitive-divider parameters
- local electrical/measurement interface references

The CVT does NOT:

- build global topology
- create Bus objects
- register itself with Network
- modify Network topology
- build Y-bus
- perform load-flow calculations
- perform short-circuit calculations
- implement protection algorithms
- implement relay logic
- implement dynamic integration
- manage measurement channels
- manage GUI objects

Those responsibilities belong to the appropriate GridForge layers.

Physical Interface
------------------

The CVT has two engineering domains:

    Primary
        High-voltage electrical interface.

    Secondary
        Measurement/protection interface.

Conceptually:

        Primary electrical system
                  |
                  |
              [ CVT ]
                  |
                  |
        Secondary measurement
                  |
            Measurement
              Channel
                  |
             Relay / Meter

The CVT model does not determine how these interfaces are connected
to the global network or measurement graph.

Topology ownership belongs to core/network.

Measurement/protection relationships belong to their respective
domain layers.

CVT Electrical Role
-------------------

A CVT is NOT treated as a conventional power-system branch.

Its primary side is physically connected to the electrical system,
but its secondary side is a measurement/protection output.

Therefore the CVT must not automatically become:

    Bus A ---- CVT ---- Bus B

in the electrical study topology.

The topology layer determines the electrical interpretation of the
CVT's physical interfaces.

Model Philosophy
----------------

This class deliberately stores engineering data rather than
implementing simulation mathematics.

Detailed CVT transfer characteristics, transient response,
ferroresonance, frequency response, burden effects, and dynamic
measurement behavior belong to simulation/protection plugins or
appropriate study models.

GridForge V2 Status
-------------------

This module is part of the GridForge Model Layer V2 baseline.

The terminal/interface representation remains intentionally
compatible with the evolving Terminal / TerminalGroup contract.

Future changes require evidence of a genuinely fundamental
architectural requirement.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite, isnan
from typing import Any, Optional

from .base import ElectricalObject


# =====================================================================
# CVT
# =====================================================================

class CVT(ElectricalObject):
    """
    GridForge Capacitive Voltage Transformer.

    Parameters
    ----------
    id : str
        Unique GridForge object identifier.

    name : str, optional
        Human-readable equipment name.

    primary_voltage : float
        Rated primary line-to-line voltage in kV.

    secondary_voltage : float
        Rated secondary voltage in V.

    frequency : float, optional
        Nominal system frequency in Hz.

    accuracy_class : str, optional
        Instrument-transformer accuracy class.

    burden_va : float, optional
        Rated secondary burden in VA.

    capacitance_high : float or None, optional
        High-side divider capacitance in farads.

    capacitance_low : float or None, optional
        Low-side divider capacitance in farads.

    transformer_ratio : float or None, optional
        Ratio of the electromagnetic intermediate transformer.

    in_service : bool, optional
        Equipment service state.

    Notes
    -----
    ``primary_voltage`` and ``secondary_voltage`` describe the rated
    external transformation.

    The CVT's internal capacitive divider and electromagnetic
    transformer are represented by parameters only.

    They do not automatically become separate network elements.
    """

    def __init__(
        self,
        id: str,
        name: str = "",
        primary_voltage: float = 0.0,
        secondary_voltage: float = 0.0,
        frequency: float = 50.0,
        accuracy_class: str = "",
        burden_va: float = 0.0,
        capacitance_high: Optional[float] = None,
        capacitance_low: Optional[float] = None,
        transformer_ratio: Optional[float] = None,
        in_service: bool = True,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # -------------------------------------------------------------
        # Service state
        # -------------------------------------------------------------

        self.in_service = bool(in_service)

        # -------------------------------------------------------------
        # Rated electrical quantities
        # -------------------------------------------------------------

        self.primary_voltage = float(primary_voltage)
        self.secondary_voltage = float(secondary_voltage)
        self.frequency = float(frequency)

        # -------------------------------------------------------------
        # Instrument-transformer characteristics
        # -------------------------------------------------------------

        self.accuracy_class = str(accuracy_class)
        self.burden_va = float(burden_va)

        # -------------------------------------------------------------
        # CVT capacitive-divider parameters
        # -------------------------------------------------------------

        self.capacitance_high = (
            None
            if capacitance_high is None
            else float(capacitance_high)
        )

        self.capacitance_low = (
            None
            if capacitance_low is None
            else float(capacitance_low)
        )

        # -------------------------------------------------------------
        # Intermediate transformer ratio
        # -------------------------------------------------------------

        self.transformer_ratio = (
            None
            if transformer_ratio is None
            else float(transformer_ratio)
        )

        # -------------------------------------------------------------
        # Physical interface references
        #
        # These remain intentionally generic while the final
        # Terminal / TerminalGroup contract is being finalized.
        # -------------------------------------------------------------

        self.primary_terminals: list[Any] = []
        self.secondary_terminals: list[Any] = []

        # -------------------------------------------------------------
        # Local validation
        # -------------------------------------------------------------

        self._validate()

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate(self) -> None:
        """
        Validate local CVT engineering data.

        System-wide engineering validation belongs to
        ``core/validation``.
        """

        # -------------------------------------------------------------
        # Primary voltage
        # -------------------------------------------------------------

        if (
            not isfinite(self.primary_voltage)
            or self.primary_voltage <= 0.0
        ):
            raise ValueError(
                "CVT primary voltage must be finite and greater "
                "than zero."
            )

        # -------------------------------------------------------------
        # Secondary voltage
        # -------------------------------------------------------------

        if (
            not isfinite(self.secondary_voltage)
            or self.secondary_voltage <= 0.0
        ):
            raise ValueError(
                "CVT secondary voltage must be finite and greater "
                "than zero."
            )

        # -------------------------------------------------------------
        # Frequency
        # -------------------------------------------------------------

        if (
            not isfinite(self.frequency)
            or self.frequency <= 0.0
        ):
            raise ValueError(
                "CVT frequency must be finite and greater "
                "than zero."
            )

        # -------------------------------------------------------------
        # Burden
        # -------------------------------------------------------------

        if (
            not isfinite(self.burden_va)
            or self.burden_va < 0.0
        ):
            raise ValueError(
                "CVT burden must be finite and non-negative."
            )

        # -------------------------------------------------------------
        # Capacitance
        # -------------------------------------------------------------

        for value, label in (
            (self.capacitance_high, "high-side capacitance"),
            (self.capacitance_low, "low-side capacitance"),
        ):

            if value is None:
                continue

            if not isfinite(value) or value <= 0.0:
                raise ValueError(
                    f"CVT {label} must be finite and greater "
                    "than zero."
                )

        # -------------------------------------------------------------
        # Intermediate transformer ratio
        # -------------------------------------------------------------

        if self.transformer_ratio is not None:

            if (
                not isfinite(self.transformer_ratio)
                or self.transformer_ratio <= 0.0
            ):
                raise ValueError(
                    "CVT transformer ratio must be finite and "
                    "greater than zero."
                )

    # =================================================================
    # RATIO
    # =================================================================

    @property
    def ratio(self) -> float:
        """
        Return the external rated voltage ratio.

        Returns
        -------
        float
            Primary-to-secondary voltage ratio.
        """

        return (
            self.primary_voltage
            / self.secondary_voltage
        )

    # =================================================================
    # INTERFACE REGISTRATION
    # =================================================================

    def set_primary_terminals(
        self,
        terminals,
    ) -> None:
        """
        Assign the local primary interface terminals.

        This stores local equipment information only.

        It does not connect the terminals to the network.
        """

        if terminals is None:
            raise ValueError(
                "CVT primary terminals cannot be None."
            )

        self.primary_terminals = list(terminals)

    # -----------------------------------------------------------------

    def set_secondary_terminals(
        self,
        terminals,
    ) -> None:
        """
        Assign the local secondary interface terminals.

        This stores local equipment information only.

        It does not create measurement or protection connections.
        """

        if terminals is None:
            raise ValueError(
                "CVT secondary terminals cannot be None."
            )

        self.secondary_terminals = list(terminals)

    # =================================================================
    # SERVICE STATE
    # =================================================================

    def set_in_service(
        self,
        in_service: bool,
    ) -> None:
        """
        Set the CVT service state.

        Topology interpretation of this state belongs to the
        network/topology layer.
        """

        self.in_service = bool(in_service)

    # =================================================================
    # SUMMARY
    # =================================================================

    def summary(self) -> dict:
        """
        Return a compact CVT engineering summary.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": "CVT",
            "in_service": self.in_service,
            "primary_voltage": self.primary_voltage,
            "secondary_voltage": self.secondary_voltage,
            "ratio": self.ratio,
            "frequency": self.frequency,
            "accuracy_class": self.accuracy_class,
            "burden_va": self.burden_va,
            "capacitance_high": self.capacitance_high,
            "capacitance_low": self.capacitance_low,
            "transformer_ratio": self.transformer_ratio,
            "primary_terminal_count": len(
                self.primary_terminals
            ),
            "secondary_terminal_count": len(
                self.secondary_terminals
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
            f"<CVT "
            f"id={self.id}, "
            f"primary={self.primary_voltage:.3f} kV, "
            f"secondary={self.secondary_voltage:.3f} V, "
            f"ratio={self.ratio:.3f}, "
            f"in_service={self.in_service}>"
        )
