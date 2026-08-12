"""
GridForge Model Layer V2
========================

File:
    core/model/pt.py

Purpose
-------
Canonical Potential Transformer (PT) equipment model for GridForge V2.

A PT is a physical instrument transformer connected to the power
system primary circuit and providing an isolated, scaled secondary
voltage representation for:

    - measurement
    - protection
    - metering
    - control
    - instrumentation

Architecture
------------

                 POWER SYSTEM
                      |
                      |
               Primary terminals
                  H1       H2
                   |       |
                   +--- PT--+
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

The PT is an equipment model.

It does NOT:

    - generate measurement signals;
    - store measured voltage;
    - create measurement channels;
    - connect itself to relays;
    - implement protection algorithms;
    - calculate network voltage;
    - build network topology;
    - create Bus objects;
    - build Y-bus;
    - perform load flow;
    - perform short-circuit calculations;
    - perform dynamic simulation;
    - operate circuit breakers;
    - manage GUI state.

Those responsibilities belong to the appropriate GridForge layers.

Authoritative ownership
-----------------------
The PT owns:

    - equipment identity;
    - primary/secondary interfaces;
    - rated voltage;
    - accuracy information;
    - burden information;
    - polarity;
    - frequency;
    - service state.

Measurement values derived from the PT belong to the measurement
domain.

Relay inputs belong to the protection/measurement interface layer.

Network topology belongs to core/network.

Dynamic PT behaviour belongs to the appropriate simulation or
measurement plugin.

GridForge V2 Design Principle
-----------------------------
The PT is upstream of measurement and protection:

    Power-system voltage
            |
            v
           PT
            |
            v
    Measurement Channel
            |
            v
       Relay Input
            |
            v
          Relay

The Relay must never obtain its authoritative voltage directly from
a value stored inside the Relay model.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from enum import Enum
from math import isfinite
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


# =====================================================================
# PT POLARITY
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
    Canonical GridForge V2 Potential Transformer.

    Parameters
    ----------
    id:
        Unique GridForge equipment identifier.

    name:
        Human-readable PT name.

    rated_primary_voltage:
        Rated primary voltage in volts.

    rated_secondary_voltage:
        Rated secondary voltage in volts.

    accuracy_class:
        Instrument-transformer accuracy classification.

        Examples:

            "0.2"
            "0.5"
            "3P"
            "6P"

        The model stores the engineering classification.
        Interpretation belongs to the appropriate measurement
        or protection layer.

    rated_burden_va:
        Rated secondary burden in VA.

    polarity:
        PT polarity convention.

    frequency:
        Nominal operating frequency in Hz.

    in_service:
        Equipment service state.

    Notes
    -----
    The PT owns four local interfaces:

        primary_h1_terminal
        primary_h2_terminal

        secondary_x1_terminal
        secondary_x2_terminal

    Primary terminals represent physical electrical interfaces.

    Secondary terminals represent measurement-side interfaces.

    The PT does not determine global topology or measurement
    connectivity.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        id: str,
        name: str = "",
        rated_primary_voltage: float = 11000.0,
        rated_secondary_voltage: float = 110.0,
        accuracy_class: str = "",
        rated_burden_va: float = 0.0,
        polarity: PTPolarity = PTPolarity.H1_H2,
        frequency: float = 50.0,
        in_service: bool = True,
    ) -> None:

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

        self._validate_positive(
            frequency,
            "frequency",
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

        self.accuracy_class = accuracy_class.strip()

        self.rated_burden_va = float(
            rated_burden_va
        )

        self.polarity = polarity

        self.frequency = float(
            frequency
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

    # =================================================================
    # RATIO
    # =================================================================

    @property
    def ratio(self) -> float:
        """
        Return the nominal PT voltage transformation ratio.

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
        Set the PT service state.

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
            "frequency": self.frequency,
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
            f"ratio="
            f"{self.rated_primary_voltage:.3f}/"
            f"{self.rated_secondary_voltage:.3f}, "
            f"accuracy={self.accuracy_class!r}, "
            f"in_service={self.in_service}>"
        )


__all__ = [
    "PTPolarity",
    "PotentialTransformer",
]
