"""
GridForge Model Layer V2
========================

File:
    core/model/cvt.py

Purpose
-------
Canonical Capacitive Voltage Transformer (CVT) equipment model
for GridForge V2.

A CVT is an instrument transformer used to provide an isolated,
scaled representation of a high-voltage electrical quantity for:

    - measurement
    - protection
    - metering
    - control
    - synchronization
    - instrumentation

Architecture
------------

                 POWER SYSTEM
                      |
                      |
               Primary terminals
                  H1       H2
                   |       |
                   +--- CVT-+
                       |
                Internal CVT
             capacitive divider
             + electromagnetic
                transformer
                       |
                 Secondary side
                  X1       X2
                   |       |
                   +-------+
                       |
             Measurement / protection
                       |
              Measurement Channel
                       |
                 Relay Input
                       |
                    Relay

The CVT is a physical equipment model.

It does NOT:

    - generate measurement signals;
    - store measured voltage;
    - implement relay logic;
    - implement protection functions;
    - create measurement channels;
    - connect itself to relays;
    - modify global network topology;
    - create Bus objects;
    - build Y-bus;
    - perform load flow;
    - perform short-circuit calculations;
    - perform dynamic simulation;
    - operate circuit breakers;
    - manage GUI state.

Those responsibilities belong to the appropriate GridForge layers.

Architectural ownership
-----------------------
The CVT owns:

    - equipment identity;
    - primary interfaces;
    - secondary interfaces;
    - rated primary voltage;
    - rated secondary voltage;
    - nominal frequency;
    - accuracy class;
    - burden;
    - capacitive-divider parameters;
    - intermediate transformer ratio;
    - service state.

Measurement values derived from the CVT belong to the
measurement-domain layer.

Relay inputs belong to the measurement/protection interface layer.

Network topology belongs to core/network.

Dynamic CVT behaviour belongs to the appropriate simulation
or measurement/protection plugin.

GridForge V2 Design Principle
-----------------------------
The CVT is upstream of measurement and protection:

    Power-system voltage
            |
            v
           CVT
            |
            v
    Measurement Channel
            |
            v
       Relay Input
            |
            v
          Relay

The Relay must never obtain its authoritative voltage directly
from a value stored inside the Relay model.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite
from typing import Any, Optional

from .base import ElectricalObject
from .terminal import Terminal


# =====================================================================
# CAPACITIVE VOLTAGE TRANSFORMER
# =====================================================================


class CVT(ElectricalObject):
    """
    Canonical GridForge V2 Capacitive Voltage Transformer.

    Parameters
    ----------
    id:
        Unique GridForge equipment identifier.

    name:
        Human-readable CVT name.

    rated_primary_voltage:
        Rated primary voltage in volts.

    rated_secondary_voltage:
        Rated secondary voltage in volts.

    frequency:
        Nominal operating frequency in Hz.

    accuracy_class:
        Instrument-transformer accuracy classification.

    rated_burden_va:
        Rated secondary burden in VA.

    capacitance_high:
        High-side divider capacitance in farads.

        Optional because the model may be used without detailed
        internal divider data.

    capacitance_low:
        Low-side divider capacitance in farads.

    transformer_ratio:
        Optional ratio of the intermediate electromagnetic
        transformer.

        This represents internal engineering data only.

    in_service:
        Equipment service state.

    Notes
    -----
    The CVT owns four local interfaces:

        primary_h1_terminal
        primary_h2_terminal

        secondary_x1_terminal
        secondary_x2_terminal

    Primary terminals represent physical electrical interfaces.

    Secondary terminals represent measurement-side interfaces.

    The internal capacitive divider and electromagnetic transformer
    are represented as equipment characteristics and do not
    automatically become separate network elements.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        id: str,
        name: str = "",
        rated_primary_voltage: float = 110000.0,
        rated_secondary_voltage: float = 110.0,
        frequency: float = 50.0,
        accuracy_class: str = "",
        rated_burden_va: float = 0.0,
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
        # Validate basic nameplate data
        # -------------------------------------------------------------

        self._validate_positive(
            rated_primary_voltage,
            "rated_primary_voltage",
        )

        self._validate_positive(
            rated_secondary_voltage,
            "rated_secondary_voltage",
        )

        self._validate_positive(
            frequency,
            "frequency",
        )

        self._validate_non_negative(
            rated_burden_va,
            "rated_burden_va",
        )

        self._validate_optional_positive(
            capacitance_high,
            "capacitance_high",
        )

        self._validate_optional_positive(
            capacitance_low,
            "capacitance_low",
        )

        self._validate_optional_positive(
            transformer_ratio,
            "transformer_ratio",
        )

        if not isinstance(accuracy_class, str):
            raise TypeError(
                "accuracy_class must be a string."
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

        self.frequency = float(
            frequency
        )

        self.accuracy_class = accuracy_class.strip()

        self.rated_burden_va = float(
            rated_burden_va
        )

        # -------------------------------------------------------------
        # Internal CVT characteristics
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

        self.transformer_ratio = (
            None
            if transformer_ratio is None
            else float(transformer_ratio)
        )

        # -------------------------------------------------------------
        # Service state
        # -------------------------------------------------------------

        self.in_service = bool(
            in_service
        )

        # -------------------------------------------------------------
        # Primary physical interfaces
        # -------------------------------------------------------------

        self.primary_h1_terminal = Terminal(
            owner=self
        )

        self.primary_h2_terminal = Terminal(
            owner=self
        )

        # -------------------------------------------------------------
        # Secondary measurement interfaces
        # -------------------------------------------------------------

        self.secondary_x1_terminal = Terminal(
            owner=self
        )

        self.secondary_x2_terminal = Terminal(
            owner=self
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    @staticmethod
    def _validate_positive(
        value: float,
        field_name: str,
    ) -> None:
        """
        Validate a strictly positive finite quantity.
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
        Validate a finite non-negative quantity.
        """

        value = float(value)

        if not isfinite(value) or value < 0.0:
            raise ValueError(
                f"{field_name} must be finite and non-negative."
            )

    # -----------------------------------------------------------------

    @staticmethod
    def _validate_optional_positive(
        value: Optional[float],
        field_name: str,
    ) -> None:
        """
        Validate an optional strictly positive quantity.
        """

        if value is None:
            return

        value = float(value)

        if not isfinite(value) or value <= 0.0:
            raise ValueError(
                f"{field_name} must be finite and greater than zero."
            )

    # =================================================================
    # RATIO
    # =================================================================

    @property
    def ratio(self) -> float:
        """
        Return the nominal external CVT voltage ratio.

        Defined as:

            primary voltage / secondary voltage
        """

        return (
            self.rated_primary_voltage
            / self.rated_secondary_voltage
        )

    # =================================================================
    # PRIMARY TERMINALS
    # =================================================================

    @property
    def primary_terminals(
        self,
    ) -> tuple[Terminal, Terminal]:
        """
        Return the two primary electrical terminals.
        """

        return (
            self.primary_h1_terminal,
            self.primary_h2_terminal,
        )

    # -----------------------------------------------------------------

    @property
    def primary_h1(self) -> Terminal:
        """
        Return the H1 primary terminal.
        """

        return self.primary_h1_terminal

    # -----------------------------------------------------------------

    @property
    def primary_h2(self) -> Terminal:
        """
        Return the H2 primary terminal.
        """

        return self.primary_h2_terminal

    # =================================================================
    # SECONDARY TERMINALS
    # =================================================================

    @property
    def secondary_terminals(
        self,
    ) -> tuple[Terminal, Terminal]:
        """
        Return the two secondary measurement terminals.
        """

        return (
            self.secondary_x1_terminal,
            self.secondary_x2_terminal,
        )

    # -----------------------------------------------------------------

    @property
    def secondary_x1(self) -> Terminal:
        """
        Return the X1 secondary terminal.
        """

        return self.secondary_x1_terminal

    # -----------------------------------------------------------------

    @property
    def secondary_x2(self) -> Terminal:
        """
        Return the X2 secondary terminal.
        """

        return self.secondary_x2_terminal

    # =================================================================
    # SERVICE STATE
    # =================================================================

    def set_in_service(
        self,
        in_service: bool,
    ) -> None:
        """
        Set the CVT service state.

        This modifies only local equipment state.

        Network/topology interpretation belongs to core/network.
        """

        self.in_service = bool(
            in_service
        )

    # =================================================================
    # ENGINEERING ACCESSORS
    # =================================================================

    @property
    def primary_voltage_rating(self) -> float:
        """
        Return the rated primary voltage.
        """

        return self.rated_primary_voltage

    # -----------------------------------------------------------------

    @property
    def secondary_voltage_rating(self) -> float:
        """
        Return the rated secondary voltage.
        """

        return self.rated_secondary_voltage

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return a compact engineering summary.

        Measurement values are intentionally absent because
        measurement state belongs to the measurement layer.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": "CVT",
            "in_service": self.in_service,
            "rated_primary_voltage": (
                self.rated_primary_voltage
            ),
            "rated_secondary_voltage": (
                self.rated_secondary_voltage
            ),
            "ratio": self.ratio,
            "frequency": self.frequency,
            "accuracy_class": self.accuracy_class,
            "rated_burden_va": self.rated_burden_va,
            "capacitance_high": self.capacitance_high,
            "capacitance_low": self.capacitance_low,
            "transformer_ratio": self.transformer_ratio,
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
            f"<CVT "
            f"id={self.id}, "
            f"ratio="
            f"{self.rated_primary_voltage:.3f}/"
            f"{self.rated_secondary_voltage:.3f}, "
            f"accuracy={self.accuracy_class!r}, "
            f"in_service={self.in_service}>"
        )


__all__ = [
    "CVT",
]
