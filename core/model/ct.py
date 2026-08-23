# core/model/ct.py
"""
GridForge V2 Current Transformer Model
======================================

Author:
    Subhendu Mishra

A Current Transformer (CT) is an instrument transformer used to
provide an isolated, scaled representation of primary current to
measurement, metering, protection, control, and instrumentation
systems.

Architecture
------------

                    POWER SYSTEM
                         |
                  Primary interface
                    P1       P2
                     |       |
                     +---CT--+
                         |
                  Measurement interface
                    S1       S2
                     |       |
                     +-------+
                         |
              Measurement / Protection
                         |
              MeasurementChannel / RelayInput
                         |
                       Relay

The CT is an equipment model.

It owns:

    - equipment identity
    - primary interfaces
    - secondary interfaces
    - nameplate ratings
    - transformation ratio
    - accuracy information
    - burden
    - polarity
    - frequency
    - service state

It does NOT own:

    - network topology
    - Bus collections
    - measurement channels
    - relay inputs
    - relay logic
    - protection calculations
    - CT saturation simulation
    - excitation-curve simulation
    - transient simulation
    - Y-bus construction
    - load-flow calculations
    - short-circuit calculations
    - breaker operation
    - SLD state
    - GUI state

Terminal Architecture
---------------------

The CT has four physical interfaces:

    Primary:
        P1
        P2

    Secondary:
        S1
        S2

Primary terminals are electrical equipment interfaces.

Secondary terminals are instrument/measurement interfaces.

The CT does not decide how these interfaces are connected in
the global topology or measurement architecture.

Measurement and protection layers consume the CT through
appropriate domain services and channels.

Dynamic Behaviour
-----------------

Dynamic CT behaviour is deliberately outside this static model.

Future simulation may provide:

    - excitation characteristics
    - saturation
    - remanence
    - transient response
    - secondary-current distortion

Those belong to the simulation/protection architecture.

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
    Static GridForge V2 Current Transformer model.

    The CT provides physical primary and secondary interfaces,
    together with static nameplate information.

    It does not calculate measurements or protection quantities.
    """

    TYPE = "CT"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        rated_primary_current: float = 1.0,
        rated_secondary_current: float = 1.0,
        accuracy_class: str = "",
        rated_burden_va: float = 0.0,
        polarity: CTPolarity = CTPolarity.P1_P2,
        frequency_hz: float = 50.0,
        in_service: bool = True,
    ) -> None:
        """
        Create a Current Transformer.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        name:
            Human-readable equipment name.

        rated_primary_current:
            Rated primary current in amperes.

        rated_secondary_current:
            Rated secondary current in amperes.

        accuracy_class:
            Engineering accuracy designation such as
            ``5P20``, ``10P10``, ``0.5`` or ``0.2S``.

        rated_burden_va:
            Rated secondary burden in VA.

        polarity:
            CT primary polarity convention.

        frequency_hz:
            Nominal operating frequency in Hz.

        in_service:
            Equipment service state.
        """

        super().__init__(
            id=id,
            name=name,
        )

        # =============================================================
        # NAMEPLATE PARAMETERS
        # =============================================================

        self.rated_primary_current = (
            self._validate_positive(
                rated_primary_current,
                "rated_primary_current",
            )
        )

        self.rated_secondary_current = (
            self._validate_positive(
                rated_secondary_current,
                "rated_secondary_current",
            )
        )

        if not isinstance(accuracy_class, str):
            raise TypeError(
                "accuracy_class must be a string."
            )

        if not isinstance(polarity, CTPolarity):
            raise TypeError(
                "polarity must be a CTPolarity value."
            )

        self.accuracy_class = accuracy_class.strip()

        self.rated_burden_va = (
            self._validate_non_negative(
                rated_burden_va,
                "rated_burden_va",
            )
        )

        self.polarity = polarity

        self.frequency_hz = (
            self._validate_positive(
                frequency_hz,
                "frequency_hz",
            )
        )

        # =============================================================
        # SERVICE STATE
        # =============================================================

        self.in_service = bool(in_service)

        # =============================================================
        # PRIMARY ELECTRICAL INTERFACES
        # =============================================================

        self.primary_p1_terminal = Terminal(
            owner=self,
        )

        self.primary_p2_terminal = Terminal(
            owner=self,
        )

        # =============================================================
        # SECONDARY INSTRUMENT INTERFACES
        # =============================================================

        self.secondary_s1_terminal = Terminal(
            owner=self,
        )

        self.secondary_s2_terminal = Terminal(
            owner=self,
        )

        self.validate_parameters()

    # =================================================================
    # IDENTITY
    # =================================================================

    @property
    def element_type(self) -> str:
        """
        Return the canonical GridForge element type.
        """

        return self.TYPE

    # =================================================================
    # TERMINALS
    # =================================================================

    @property
    def primary_terminals(
        self,
    ) -> tuple[Terminal, Terminal]:
        """
        Return the ordered primary terminals.

        Order:

            P1, P2
        """

        return (
            self.primary_p1_terminal,
            self.primary_p2_terminal,
        )

    @property
    def secondary_terminals(
        self,
    ) -> tuple[Terminal, Terminal]:
        """
        Return the ordered secondary terminals.

        Order:

            S1, S2
        """

        return (
            self.secondary_s1_terminal,
            self.secondary_s2_terminal,
        )

    @property
    def terminals(
        self,
    ) -> tuple[Terminal, ...]:
        """
        Return all CT interfaces in deterministic order.

        Order:

            P1, P2, S1, S2

        Generic model infrastructure may use this property to
        enumerate CT interfaces.

        It must not assume that all returned terminals belong
        to the same electrical network domain.
        """

        return (
            self.primary_p1_terminal,
            self.primary_p2_terminal,
            self.secondary_s1_terminal,
            self.secondary_s2_terminal,
        )

    # =================================================================
    # TERMINAL ACCESSORS
    # =================================================================

    @property
    def primary_p1(self) -> Terminal:
        """Return the P1 primary terminal."""

        return self.primary_p1_terminal

    @property
    def primary_p2(self) -> Terminal:
        """Return the P2 primary terminal."""

        return self.primary_p2_terminal

    @property
    def secondary_s1(self) -> Terminal:
        """Return the S1 secondary terminal."""

        return self.secondary_s1_terminal

    @property
    def secondary_s2(self) -> Terminal:
        """Return the S2 secondary terminal."""

        return self.secondary_s2_terminal

    # =================================================================
    # CONNECTIVITY
    # =================================================================

    @property
    def primary_connected(self) -> bool:
        """
        Return whether both primary interfaces have endpoints.
        """

        return (
            self.primary_p1_terminal.is_connected
            and self.primary_p2_terminal.is_connected
        )

    @property
    def secondary_connected(self) -> bool:
        """
        Return whether both secondary interfaces have endpoints.
        """

        return (
            self.secondary_s1_terminal.is_connected
            and self.secondary_s2_terminal.is_connected
        )

    # =================================================================
    # RATIO
    # =================================================================

    @property
    def ratio(self) -> float:
        """
        Return the nominal current transformation ratio.

        Defined as:

            primary current / secondary current

        Example:

            400 / 5 = 80
        """

        return (
            self.rated_primary_current
            / self.rated_secondary_current
        )

    @property
    def transformation_ratio(self) -> float:
        """
        Alias for ``ratio``.

        ``ratio`` remains the canonical property.
        """

        return self.ratio

    # =================================================================
    # SERVICE STATE
    # =================================================================

    def set_in_service(
        self,
        in_service: bool,
    ) -> None:
        """
        Set the local CT service state.

        This does not modify network topology or measurement
        channel state.
        """

        self.in_service = bool(in_service)

    def connect(self) -> None:
        """
        Place the CT in service.
        """

        self.in_service = True

    def disconnect(self) -> None:
        """
        Take the CT out of service.
        """

        self.in_service = False

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate CT-local engineering parameters.

        This does not validate:

            - network topology
            - measurement channels
            - relay configuration
            - protection settings
            - simulation state
        """

        self.rated_primary_current = (
            self._validate_positive(
                self.rated_primary_current,
                "rated_primary_current",
            )
        )

        self.rated_secondary_current = (
            self._validate_positive(
                self.rated_secondary_current,
                "rated_secondary_current",
            )
        )

        self.rated_burden_va = (
            self._validate_non_negative(
                self.rated_burden_va,
                "rated_burden_va",
            )
        )

        self.frequency_hz = (
            self._validate_positive(
                self.frequency_hz,
                "frequency_hz",
            )
        )

        if not isinstance(
            self.accuracy_class,
            str,
        ):
            raise TypeError(
                "accuracy_class must be a string."
            )

        if not isinstance(
            self.polarity,
            CTPolarity,
        ):
            raise TypeError(
                "polarity must be a CTPolarity value."
            )

        return True

    def validate(self) -> bool:
        """
        Public CT validation entry point.
        """

        return self.validate_parameters()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """
        Return static engineering information.

        Measurement values are deliberately absent.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,
            "in_service": self.in_service,

            "rated_primary_current":
                self.rated_primary_current,

            "rated_secondary_current":
                self.rated_secondary_current,

            "ratio":
                self.ratio,

            "accuracy_class":
                self.accuracy_class,

            "rated_burden_va":
                self.rated_burden_va,

            "polarity":
                self.polarity.value,

            "frequency_hz":
                self.frequency_hz,

            "primary_connected":
                self.primary_connected,

            "secondary_connected":
                self.secondary_connected,

            "primary_p1_endpoint":
                self._endpoint_id(
                    self.primary_p1_terminal
                ),

            "primary_p2_endpoint":
                self._endpoint_id(
                    self.primary_p2_terminal
                ),

            "secondary_s1_endpoint":
                self._endpoint_id(
                    self.secondary_s1_terminal
                ),

            "secondary_s2_endpoint":
                self._endpoint_id(
                    self.secondary_s2_terminal
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
            f"accuracy="
            f"{self.accuracy_class!r}, "
            f"in_service="
            f"{self.in_service}>"
        )

    # =================================================================
    # INTERNAL HELPERS
    # =================================================================

    @staticmethod
    def _validate_positive(
        value: float,
        field_name: str,
    ) -> float:
        """
        Validate and return a finite positive quantity.
        """

        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{field_name} must be numeric."
            ) from exc

        if not isfinite(value) or value <= 0.0:
            raise ValueError(
                f"{field_name} must be finite and "
                "greater than zero."
            )

        return value

    @staticmethod
    def _validate_non_negative(
        value: float,
        field_name: str,
    ) -> float:
        """
        Validate and return a finite non-negative quantity.
        """

        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{field_name} must be numeric."
            ) from exc

        if not isfinite(value) or value < 0.0:
            raise ValueError(
                f"{field_name} must be finite and "
                "non-negative."
            )

        return value

    @staticmethod
    def _endpoint_id(
        terminal: Terminal,
    ) -> Any:
        """
        Safely return the terminal endpoint identifier.

        This helper avoids imposing a particular endpoint
        implementation on the CT model.
        """

        endpoint = getattr(
            terminal,
            "endpoint",
            None,
        )

        if endpoint is None:
            return None

        return getattr(
            endpoint,
            "id",
            None,
        )


# =====================================================================
# COMPATIBILITY ALIAS
# =====================================================================

CT = CurrentTransformer


__all__ = [
    "CTPolarity",
    "CurrentTransformer",
    "CT",
]
