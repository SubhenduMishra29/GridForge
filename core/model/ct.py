"""
GridForge Current Transformer Model
===================================

GridForge Model Layer V2

Defines the canonical Current Transformer (CT) equipment model.

A CT is an electrical measurement device physically inserted into a
power-system conductor. It has:

    Primary circuit
        Two physical electrical terminals participating in the
        physical/electrical network.

    Secondary measurement circuit
        Measurement terminals used by protection, metering, control,
        and instrumentation systems.

The CT model stores the physical/nameplate and transformation
characteristics required by higher GridForge layers.

Architecture
------------

                    CURRENT TRANSFORMER
                           │
             ┌─────────────┴─────────────┐
             │                           │
        PRIMARY SIDE               SECONDARY SIDE
             │                           │
       Electrical path            Measurement path
             │                           │
      ┌──────┴──────┐             ┌──────┴──────┐
      │             │             │             │
   Primary A    Primary B      Secondary S1  Secondary S2
      │             │             │             │
      └──────┬──────┘             └──────┬──────┘
             │                           │
       Power topology              Protection /
                                   measurement

Responsibilities
----------------
This module is responsible for:

- Representing a physical CT.
- Representing its primary electrical terminals.
- Representing its secondary measurement terminals.
- Storing CT ratio.
- Storing rated primary/secondary current.
- Storing accuracy-class information.
- Storing burden information.
- Storing polarity information.
- Storing service state.
- Providing local state validation.
- Providing diagnostic information.

This module does NOT:

- Build network topology.
- Register terminals with Network.
- Determine electrical connectivity.
- Build Y-bus.
- Calculate fault current.
- Calculate relay operating time.
- Implement CT saturation algorithms.
- Implement protection logic.
- Manage relay connections.
- Manage GUI objects.

Those responsibilities belong to the appropriate GridForge layers.

GridForge V2 Boundary
---------------------
The CT primary terminals are physical electrical connection points.

The CT secondary terminals are measurement-side connection points.

The distinction is intentional:

    Primary
        participates in the electrical power-system graph.

    Secondary
        participates in measurement/protection/control graphs.

The model does not decide how those graphs are assembled.

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
    GridForge Current Transformer.

    Parameters
    ----------
    id : str
        Unique GridForge object identifier.

    name : str, optional
        Human-readable CT name.

    rated_primary_current : float
        Rated primary current in amperes.

    rated_secondary_current : float
        Rated secondary current in amperes.

        Common values include 1 A and 5 A.

    accuracy_class : str, optional
        CT accuracy class, for example:

            "5P20"
            "10P10"
            "0.5"
            "0.2S"

        The value is stored as engineering metadata. Accuracy
        interpretation belongs to the appropriate measurement/
        protection layer.

    rated_burden_va : float, optional
        Rated secondary burden in VA.

    polarity : CTPolarity, optional
        Primary polarity designation.

    Notes
    -----
    The CT owns four local physical terminals:

        primary_from_terminal
        primary_to_terminal
        secondary_s1_terminal
        secondary_s2_terminal

    Primary terminals participate in the electrical physical graph.

    Secondary terminals are measurement/protection interfaces and
    must not automatically become electrical network buses.
    """

    def __init__(
        self,
        id: str,
        name: str = "",
        rated_primary_current: float = 1.0,
        rated_secondary_current: float = 1.0,
        accuracy_class: str = "",
        rated_burden_va: float = 0.0,
        polarity: CTPolarity = CTPolarity.P1_P2,
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
        #
        # These belong to the CT and are visible to the physical
        # network assembly.
        # -------------------------------------------------------------

        self.primary_from_terminal = Terminal(
            owner=self
        )

        self.primary_to_terminal = Terminal(
            owner=self
        )

        # -------------------------------------------------------------
        # Secondary measurement terminals
        #
        # These are deliberately still represented by Terminal for
        # local physical identity, but the network layer must treat
        # them as measurement-domain interfaces rather than ordinary
        # power-system nodes.
        # -------------------------------------------------------------

        self.secondary_s1_terminal = Terminal(
            owner=self
        )

        self.secondary_s2_terminal = Terminal(
            owner=self
        )

        # -------------------------------------------------------------
        # Compatibility aliases
        # -------------------------------------------------------------

        self.primary_a = self.primary_from_terminal
        self.primary_b = self.primary_to_terminal

        self.secondary_s1 = self.secondary_s1_terminal
        self.secondary_s2 = self.secondary_s2_terminal

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
        Return the nominal CT transformation ratio.

        Defined as:

            primary current / secondary current
        """

        return (
            self.rated_primary_current
            / self.rated_secondary_current
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
            self.primary_from_terminal,
            self.primary_to_terminal,
        )

    # -----------------------------------------------------------------

    @property
    def secondary_terminals(self) -> tuple[Terminal, Terminal]:
        """
        Return the two secondary measurement terminals.
        """

        return (
            self.secondary_s1_terminal,
            self.secondary_s2_terminal,
        )

    # =================================================================
    # STATE
    # =================================================================

    def set_in_service(
        self,
        in_service: bool,
    ) -> None:
        """
        Set the CT service state.

        This only changes local equipment state.

        Network topology interpretation belongs to core/network.
        """

        self.in_service = bool(in_service)

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict:
        """
        Return a compact CT summary.
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
            "primary_from": (
                self.primary_from_terminal.endpoint_id
            ),
            "primary_to": (
                self.primary_to_terminal.endpoint_id
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
            f"ratio={self.rated_primary_current:.3f}/"
            f"{self.rated_secondary_current:.3f}, "
            f"accuracy={self.accuracy_class!r}, "
            f"in_service={self.in_service}>"
        )
