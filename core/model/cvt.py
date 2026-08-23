# core/model/cvt.py
"""
GridForge V2 Capacitive Voltage Transformer Model
==================================================

Author:
    Subhendu Mishra

A Capacitive Voltage Transformer (CVT) is an instrument
transformer used to provide an isolated, scaled representation
of primary system voltage to measurement, metering, protection,
control, and instrumentation systems.

Architecture
------------

                    POWER SYSTEM
                         |
                  Primary interface
                    H1       H2
                     |       |
                     +--CVT--+
                         |
                  Measurement interface
                    X1       X2
                     |       |
                     +-------+
                         |
              Measurement / Protection
                         |
              MeasurementChannel / RelayInput
                         |
                       Relay

The CVT is an equipment model.

It owns:

    - equipment identity
    - primary interfaces
    - secondary interfaces
    - rated primary voltage
    - rated secondary voltage
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
    - CVT transient-response simulation
    - ferroresonance simulation
    - dynamic simulation
    - Y-bus construction
    - load-flow calculations
    - short-circuit calculations
    - SLD state
    - GUI state

Terminal Architecture
---------------------

The CVT has four physical interfaces:

    Primary:
        H1
        H2

    Secondary:
        X1
        X2

Primary terminals are electrical equipment interfaces.

Secondary terminals are instrument/measurement interfaces.

The CVT does not decide how these interfaces are connected in
the global topology or measurement architecture.

Measurement and protection layers consume the CVT through
appropriate domain services and channels.

Dynamic Behaviour
-----------------

Dynamic CVT behaviour is deliberately outside this static model.

Future simulation may provide:

    - transient response
    - ferroresonance behaviour
    - frequency response
    - secondary voltage distortion
    - transient recovery behaviour

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
# CVT POLARITY
# =====================================================================


class CVTPolarity(Enum):
    """
    Capacitive-voltage-transformer polarity convention.
    """

    H1_H2 = "H1-H2"
    H2_H1 = "H2-H1"


# =====================================================================
# CAPACITIVE VOLTAGE TRANSFORMER
# =====================================================================


class CapacitiveVoltageTransformer(ElectricalObject):
    """
    Static GridForge V2 Capacitive Voltage Transformer model.

    The CVT provides physical primary and secondary interfaces,
    together with static nameplate information.

    It does not calculate measured voltage or protection
    quantities.
    """

    TYPE = "CVT"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        rated_primary_voltage_kv: float = 1.0,
        rated_secondary_voltage_v: float = 100.0,
        accuracy_class: str = "",
        rated_burden_va: float = 0.0,
        polarity: CVTPolarity = CVTPolarity.H1_H2,
        frequency_hz: float = 50.0,
        in_service: bool = True,
    ) -> None:
        """
        Create a Capacitive Voltage Transformer.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        name:
            Human-readable equipment name.

        rated_primary_voltage_kv:
            Rated primary voltage in kV.

        rated_secondary_voltage_v:
            Rated secondary voltage in volts.

        accuracy_class:
            Engineering accuracy designation.

        rated_burden_va:
            Rated secondary burden in VA.

        polarity:
            CVT primary polarity convention.

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

        self.rated_primary_voltage_kv = (
            self._validate_positive(
                rated_primary_voltage_kv,
                "rated_primary_voltage_kv",
            )
        )

        self.rated_secondary_voltage_v = (
            self._validate_positive(
                rated_secondary_voltage_v,
                "rated_secondary_voltage_v",
            )
        )

        if not isinstance(accuracy_class, str):
            raise TypeError(
                "accuracy_class must be a string."
            )

        if not isinstance(polarity, CVTPolarity):
            raise TypeError(
                "polarity must be a CVTPolarity value."
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

        self.primary_h1_terminal = Terminal(
            owner=self,
        )

        self.primary_h2_terminal = Terminal(
            owner=self,
        )

        # =============================================================
        # SECONDARY INSTRUMENT INTERFACES
        # =============================================================

        self.secondary_x1_terminal = Terminal(
            owner=self,
        )

        self.secondary_x2_terminal = Terminal(
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

            H1, H2
        """

        return (
            self.primary_h1_terminal,
            self.primary_h2_terminal,
        )

    @property
    def secondary_terminals(
        self,
    ) -> tuple[Terminal, Terminal]:
        """
        Return the ordered secondary terminals.

        Order:

            X1, X2
        """

        return (
            self.secondary_x1_terminal,
            self.secondary_x2_terminal,
        )

    @property
    def terminals(
        self,
    ) -> tuple[Terminal, ...]:
        """
        Return all CVT interfaces in deterministic order.

        Order:

            H1, H2, X1, X2

        Generic model infrastructure may enumerate the interfaces
        through this property.

        The returned terminals are not assumed to belong to the
        same network domain.
        """

        return (
            self.primary_h1_terminal,
            self.primary_h2_terminal,
            self.secondary_x1_terminal,
            self.secondary_x2_terminal,
        )

    # =================================================================
    # TERMINAL ACCESSORS
    # =================================================================

    @property
    def primary_h1(self) -> Terminal:
        """Return the H1 primary terminal."""

        return self.primary_h1_terminal

    @property
    def primary_h2(self) -> Terminal:
        """Return the H2 primary terminal."""

        return self.primary_h2_terminal

    @property
    def secondary_x1(self) -> Terminal:
        """Return the X1 secondary terminal."""

        return self.secondary_x1_terminal

    @property
    def secondary_x2(self) -> Terminal:
        """Return the X2 secondary terminal."""

        return self.secondary_x2_terminal

    # =================================================================
    # CONNECTIVITY
    # =================================================================

    @property
    def primary_connected(self) -> bool:
        """
        Return whether both primary interfaces have endpoints.
        """

        return (
            self.primary_h1_terminal.is_connected
            and self.primary_h2_terminal.is_connected
        )

    @property
    def secondary_connected(self) -> bool:
        """
        Return whether both secondary interfaces have endpoints.
        """

        return (
            self.secondary_x1_terminal.is_connected
            and self.secondary_x2_terminal.is_connected
        )

    # =================================================================
    # TRANSFORMATION RATIO
    # =================================================================

    @property
    def ratio(self) -> float:
        """
        Return the nominal voltage transformation ratio.

        Defined as:

            primary voltage / secondary voltage

        Units are converted consistently:

            kV -> V

        Example:

            132 kV / 110 V

            = 132000 / 110

            = 1200
        """

        return (
            self.rated_primary_voltage_kv * 1000.0
            / self.rated_secondary_voltage_v
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
        Set the local CVT service state.

        This does not modify network topology or measurement
        channel state.
        """

        self.in_service = bool(in_service)

    def connect(self) -> None:
        """Place the CVT in service."""

        self.in_service = True

    def disconnect(self) -> None:
        """Take the CVT out of service."""

        self.in_service = False

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate CVT-local engineering parameters.

        This does not validate:

            - network topology
            - measurement channels
            - relay configuration
            - protection settings
            - simulation state
        """

        self.rated_primary_voltage_kv = (
            self._validate_positive(
                self.rated_primary_voltage_kv,
                "rated_primary_voltage_kv",
            )
        )

        self.rated_secondary_voltage_v = (
            self._validate_positive(
                self.rated_secondary_voltage_v,
                "rated_secondary_voltage_v",
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
            CVTPolarity,
        ):
            raise TypeError(
                "polarity must be a CVTPolarity value."
            )

        return True

    def validate(self) -> bool:
        """
        Public CVT validation entry point.
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

            "rated_primary_voltage_kv":
                self.rated_primary_voltage_kv,

            "rated_secondary_voltage_v":
                self.rated_secondary_voltage_v,

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

            "primary_h1_endpoint":
                self._endpoint_id(
                    self.primary_h1_terminal
                ),

            "primary_h2_endpoint":
                self._endpoint_id(
                    self.primary_h2_terminal
                ),

            "secondary_x1_endpoint":
                self._endpoint_id(
                    self.secondary_x1_terminal
                ),

            "secondary_x2_endpoint":
                self._endpoint_id(
                    self.secondary_x2_terminal
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
            f"<CapacitiveVoltageTransformer "
            f"id={self.id}, "
            f"ratio="
            f"{self.rated_primary_voltage_kv:.3f}kV/"
            f"{self.rated_secondary_voltage_v:.3f}V, "
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

        This avoids imposing a particular endpoint implementation
        on the CVT model.
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

CVT = CapacitiveVoltageTransformer


__all__ = [
    "CVTPolarity",
    "CapacitiveVoltageTransformer",
    "CVT",
]
