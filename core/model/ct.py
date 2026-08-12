"""
GridForge Model Layer V2
========================

File:
    core/model/ct.py

Purpose
-------
Canonical Current Transformer (CT) equipment model for GridForge V2.

A CT is a physical instrument transformer installed in a power-system
conductor. It provides an isolated, scaled representation of primary
current to measurement, protection, metering, control, and
instrumentation systems.

Architecture
------------

                POWER SYSTEM
                     |
                     |
              Primary terminals
                 P1       P2
                  |       |
                  +--- CT--+
                       |
                 Secondary side
                  S1       S2
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

The CT is an equipment model.

It does NOT itself:

    - generate measurement signals;
    - calculate relay quantities;
    - perform protection logic;
    - calculate CT saturation;
    - calculate excitation characteristics dynamically;
    - create measurement channels;
    - connect itself to relays;
    - modify Network topology;
    - build Y-bus;
    - perform load flow;
    - perform short-circuit calculations;
    - operate circuit breakers;
    - manage GUI state.

Those responsibilities belong to the appropriate GridForge layers.

Authoritative ownership
-----------------------
The CT owns:

    - equipment identity;
    - primary/secondary interfaces;
    - nameplate ratings;
    - transformation ratio;
    - accuracy information;
    - burden information;
    - polarity;
    - service state.

Measurement quantities produced from the CT belong to the
measurement-domain layer.

Protection quantities and relay decisions belong to core/protection.

Topology belongs to core/network.

Simulation of CT transient behaviour belongs to the appropriate
simulation/protection plugin.

GridForge V2 Design Principle
-----------------------------
The CT is upstream of the relay.

Therefore:

    Relay
       ^
       |
    RelayInput
       ^
       |
    MeasurementChannel
       ^
       |
      CT
       ^
       |
    Power-system current

The Relay must never treat a raw value stored directly inside the
Relay model as the authoritative measurement source.

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
# CT POLARITY
# =====================================================================


class CTPolarity(Enum):
    """
    Current-transformer polarity convention.
    """

    P1_P2 = "P1-P2"
    P2_P1 = "P2-P1"


# =====================================================================
# CURRENT TRANSFORMER
# =====================================================================


class CurrentTransformer(ElectricalObject):
    """
    Canonical GridForge V2 Current Transformer.

    Parameters
    ----------
    id:
        Unique GridForge equipment identifier.

    name:
        Human-readable CT name.

    rated_primary_current:
        Rated primary current in amperes.

    rated_secondary_current:
        Rated secondary current in amperes.

        Typical values are 1 A or 5 A.

    accuracy_class:
        CT accuracy classification.

        Examples:

            "5P20"
            "10P10"
            "0.5"
            "0.2S"

        The model stores this as engineering metadata.
        Interpretation belongs to the appropriate
        measurement/protection layer.

    rated_burden_va:
        Rated secondary burden in VA.

    polarity:
        Primary polarity convention.

    frequency:
        Nominal operating frequency in Hz.

    instrument_ratio:
        Optional explicit transformation ratio.

        Normally this is derived from the rated primary and
        secondary currents and therefore should remain None.

        This field is intentionally not exposed as an independent
        authoritative setting in the normal case.

    in_service:
        Equipment service state.

    Notes
    -----
    The CT owns four local interfaces:

        primary_p1_terminal
        primary_p2_terminal

        secondary_s1_terminal
        secondary_s2_terminal

    Primary terminals represent physical electrical interfaces.

    Secondary terminals represent the CT's measurement-side
    interfaces.

    The CT does not decide how those interfaces participate in
    global topology or measurement connectivity.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        id: str,
        name: str = "",
        rated_primary_current: float = 1.0,
        rated_secondary_current: float = 1.0,
        accuracy_class: str = "",
        rated_burden_va: float = 0.0,
        polarity: CTPolarity = CTPolarity.P1_P2,
        frequency: float = 50.0,
        in_service: bool = True,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # -------------------------------------------------------------
        # Nameplate validation
        # -------------------------------------------------------------

        self._validate_positive(
            rated_primary_current,
            "rated_primary_current",
        )

        self._validate_positive(
            rated_secondary_current,
            "rated_secondary_current",
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

        if not isinstance(polarity, CTPolarity):
            raise TypeError(
                "polarity must be a CTPolarity enum value."
            )

        # -------------------------------------------------------------
        # Nameplate
        # -------------------------------------------------------------

        self.rated_primary_current = float(
            rated_primary_current
        )

        self.rated_secondary_current = float(
            rated_secondary_current
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

        self.primary_p1_terminal = Terminal(
            owner=self
        )

        self.primary_p2_terminal = Terminal(
            owner=self
        )

        # -------------------------------------------------------------
        # Secondary measurement interfaces
        # -------------------------------------------------------------
        #
        # These are local CT interfaces.
        #
        # They are NOT automatically registered as power-system
        # network nodes.
        # -------------------------------------------------------------

        self.secondary_s1_terminal = Terminal(
            owner=self
        )

        self.secondary_s2_terminal = Terminal(
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
        Return the nominal CT transformation ratio.

        Defined as:

            primary current / secondary current

        Example
        -------
        A 400/5 A CT has:

            ratio = 80.0
        """

        return (
            self.rated_primary_current
            / self.rated_secondary_current
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
            self.primary_p1_terminal,
            self.primary_p2_terminal,
        )

    # -----------------------------------------------------------------

    @property
    def primary_p1(self) -> Terminal:
        """
        Compatibility/accessor for the P1 primary terminal.
        """

        return self.primary_p1_terminal

    # -----------------------------------------------------------------

    @property
    def primary_p2(self) -> Terminal:
        """
        Compatibility/accessor for the P2 primary terminal.
        """

        return self.primary_p2_terminal

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
            self.secondary_s1_terminal,
            self.secondary_s2_terminal,
        )

    # -----------------------------------------------------------------

    @property
    def secondary_s1(self) -> Terminal:
        """
        Compatibility/accessor for the S1 secondary terminal.
        """

        return self.secondary_s1_terminal

    # -----------------------------------------------------------------

    @property
    def secondary_s2(self) -> Terminal:
        """
        Compatibility/accessor for the S2 secondary terminal.
        """

        return self.secondary_s2_terminal

    # =================================================================
    # SERVICE STATE
    # =================================================================

    def set_in_service(
        self,
        in_service: bool,
    ) -> None:
        """
        Set the CT service state.

        This changes only local equipment state.

        Network topology interpretation belongs to core/network.
        """

        self.in_service = bool(
            in_service
        )

    # =================================================================
    # ENGINEERING INFORMATION
    # =================================================================

    @property
    def primary_current_rating(self) -> float:
        """
        Return the rated primary current.

        This alias exists for readability in higher-level code.
        """

        return self.rated_primary_current

    # -----------------------------------------------------------------

    @property
    def secondary_current_rating(self) -> float:
        """
        Return the rated secondary current.

        This alias exists for readability in higher-level code.
        """

        return self.rated_secondary_current

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return a compact engineering summary.

        The summary contains model data only.

        It does not expose simulated measurement values because
        measurement state belongs to the measurement layer.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": "CurrentTransformer",
            "in_service": self.in_service,
            "rated_primary_current": (
                self.rated_primary_current
            ),
            "rated_secondary_current": (
                self.rated_secondary_current
            ),
            "ratio": self.ratio,
            "accuracy_class": self.accuracy_class,
            "rated_burden_va": self.rated_burden_va,
            "polarity": self.polarity.value,
            "frequency": self.frequency,
            "primary_p1": (
                self.primary_p1_terminal.endpoint_id
            ),
            "primary_p2": (
                self.primary_p2_terminal.endpoint_id
            ),
            "secondary_s1": (
                self.secondary_s1_terminal.endpoint_id
            ),
            "secondary_s2": (
                self.secondary_s2_terminal.endpoint_id
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
            f"<CurrentTransformer "
            f"id={self.id}, "
            f"ratio="
            f"{self.rated_primary_current:.3f}/"
            f"{self.rated_secondary_current:.3f}, "
            f"accuracy={self.accuracy_class!r}, "
            f"in_service={self.in_service}>"
        )


__all__ = [
    "CTPolarity",
    "CurrentTransformer",
]
