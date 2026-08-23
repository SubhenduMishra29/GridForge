# core/model/pt.py
"""
GridForge V2 Potential Transformer (PT) Model
=============================================

Author:
    Subhendu Mishra

A PT is an electrical measurement instrument transformer.

The PT model owns:

    - identity
    - ratio / rated voltages
    - accuracy data
    - burden
    - phase displacement
    - four physical terminals
    - service state

The PT does NOT own:

    - network topology
    - graph state
    - network containers
    - relay logic
    - protection decisions
    - SLD geometry
    - GUI state

Terminal architecture:

    primary_a  ─────┐
    primary_b  ─────┤ PT
    secondary_a ────┤
    secondary_b ────┘

Connectivity is owned by the Network layer.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class PT(ElectricalObject):
    """
    Potential Transformer / Voltage Transformer model.

    The PT is a measurement device and therefore does not implement
    the Injection contract.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    name:
        Human-readable name.

    primary_voltage_kv:
        Rated primary voltage in kV.

    secondary_voltage_v:
        Rated secondary voltage in volts.

    accuracy_class:
        Instrument-transformer accuracy class.

    burden_va:
        Rated secondary burden in VA.

    phase_displacement_deg:
        Rated phase displacement in degrees.

    in_service:
        Equipment service state.

    primary_a, primary_b:
        Primary-side terminal endpoints.

    secondary_a, secondary_b:
        Secondary-side terminal endpoints.
    """

    TYPE = "PT"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        primary_voltage_kv: float = 11.0,
        secondary_voltage_v: float = 110.0,
        accuracy_class: str = "0.5",
        burden_va: float = 100.0,
        phase_displacement_deg: float = 0.0,
        in_service: bool = True,
        primary_a: Any = None,
        primary_b: Any = None,
        secondary_a: Any = None,
        secondary_b: Any = None,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # =============================================================
        # NAMEPLATE / MEASUREMENT PARAMETERS
        # =============================================================

        self.primary_voltage_kv = (
            self._validate_positive(
                primary_voltage_kv,
                "primary_voltage_kv",
            )
        )

        self.secondary_voltage_v = (
            self._validate_positive(
                secondary_voltage_v,
                "secondary_voltage_v",
            )
        )

        if not isinstance(
            accuracy_class,
            str,
        ):
            raise TypeError(
                "accuracy_class must be a string."
            )

        self.accuracy_class = accuracy_class.strip()

        if not self.accuracy_class:
            raise ValueError(
                "accuracy_class cannot be empty."
            )

        self.burden_va = (
            self._validate_non_negative(
                burden_va,
                "burden_va",
            )
        )

        self.phase_displacement_deg = (
            self._validate_finite(
                phase_displacement_deg,
                "phase_displacement_deg",
            )
        )

        # =============================================================
        # SERVICE STATE
        # =============================================================

        if not isinstance(
            in_service,
            bool,
        ):
            raise TypeError(
                "in_service must be boolean."
            )

        self.in_service = in_service

        # =============================================================
        # AUTHORITATIVE TERMINALS
        # =============================================================

        self.primary_a = Terminal(
            endpoint=primary_a,
            owner=self,
        )

        self.primary_b = Terminal(
            endpoint=primary_b,
            owner=self,
        )

        self.secondary_a = Terminal(
            endpoint=secondary_a,
            owner=self,
        )

        self.secondary_b = Terminal(
            endpoint=secondary_b,
            owner=self,
        )

        # =============================================================
        # COMMON MODEL VALIDATION
        # =============================================================

        self.validate()

    # =================================================================
    # IDENTITY
    # =================================================================

    @property
    def element_type(self) -> str:
        """Return the canonical PT element type."""

        return self.TYPE

    # =================================================================
    # TERMINALS
    # =================================================================

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """
        Return all PT terminals in deterministic order.

        Order:

            primary_a
            primary_b
            secondary_a
            secondary_b
        """

        return (
            self.primary_a,
            self.primary_b,
            self.secondary_a,
            self.secondary_b,
        )

    @property
    def primary_terminals(self) -> tuple[Terminal, Terminal]:
        """Return the two primary terminals."""

        return (
            self.primary_a,
            self.primary_b,
        )

    @property
    def secondary_terminals(self) -> tuple[Terminal, Terminal]:
        """Return the two secondary terminals."""

        return (
            self.secondary_a,
            self.secondary_b,
        )

    # =================================================================
    # SERVICE STATE
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """Return True when the PT is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return True when the PT is out of service."""

        return not self.in_service

    def put_in_service(self) -> None:
        """Place the PT in service."""

        self.in_service = True

    def take_out_of_service(self) -> None:
        """Take the PT out of service."""

        self.in_service = False

    # Compatibility methods retained for callers using the older API.

    def set_in_service(
        self,
        value: bool,
    ) -> None:
        """
        Set PT service state.

        Unlike the previous implementation, arbitrary values are not
        silently coerced to bool.
        """

        if not isinstance(
            value,
            bool,
        ):
            raise TypeError(
                "in_service must be boolean."
            )

        self.in_service = value

    # =================================================================
    # RATIO
    # =================================================================

    @property
    def voltage_ratio(self) -> float:
        """
        Return primary-to-secondary voltage ratio.

        Primary voltage is stored in kV and secondary voltage in V.
        """

        return (
            self.primary_voltage_kv * 1000.0
            / self.secondary_voltage_v
        )

    @property
    def ratio(self) -> float:
        """Compatibility alias for voltage_ratio."""

        return self.voltage_ratio

    # =================================================================
    # CONNECTIVITY
    # =================================================================

    @property
    def is_primary_connected(self) -> bool:
        """Return True when both primary terminals are connected."""

        return (
            self.primary_a.is_connected
            and self.primary_b.is_connected
        )

    @property
    def is_secondary_connected(self) -> bool:
        """Return True when both secondary terminals are connected."""

        return (
            self.secondary_a.is_connected
            and self.secondary_b.is_connected
        )

    @property
    def is_connected(self) -> bool:
        """
        Return True when all PT terminals are connected.
        """

        return all(
            terminal.is_connected
            for terminal in self.terminals
        )

    # =================================================================
    # TERMINAL CONNECTION HELPERS
    # =================================================================

    def connect_primary_a(
        self,
        endpoint: Any,
    ) -> None:
        """Connect primary terminal A."""

        if endpoint is None:
            raise ValueError(
                f"PT '{self.id}' primary_a endpoint cannot be None."
            )

        self.primary_a.connect(endpoint)

    def connect_primary_b(
        self,
        endpoint: Any,
    ) -> None:
        """Connect primary terminal B."""

        if endpoint is None:
            raise ValueError(
                f"PT '{self.id}' primary_b endpoint cannot be None."
            )

        self.primary_b.connect(endpoint)

    def connect_secondary_a(
        self,
        endpoint: Any,
    ) -> None:
        """Connect secondary terminal A."""

        if endpoint is None:
            raise ValueError(
                f"PT '{self.id}' secondary_a endpoint cannot be None."
            )

        self.secondary_a.connect(endpoint)

    def connect_secondary_b(
        self,
        endpoint: Any,
    ) -> None:
        """Connect secondary terminal B."""

        if endpoint is None:
            raise ValueError(
                f"PT '{self.id}' secondary_b endpoint cannot be None."
            )

        self.secondary_b.connect(endpoint)

    def disconnect_all(self) -> None:
        """Disconnect all PT terminals."""

        for terminal in self.terminals:
            terminal.disconnect()

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate PT-local engineering parameters.

        Network topology is deliberately outside this method.
        """

        self.primary_voltage_kv = (
            self._validate_positive(
                self.primary_voltage_kv,
                "primary_voltage_kv",
            )
        )

        self.secondary_voltage_v = (
            self._validate_positive(
                self.secondary_voltage_v,
                "secondary_voltage_v",
            )
        )

        if not isinstance(
            self.accuracy_class,
            str,
        ):
            raise TypeError(
                "accuracy_class must be a string."
            )

        self.accuracy_class = (
            self.accuracy_class.strip()
        )

        if not self.accuracy_class:
            raise ValueError(
                "accuracy_class cannot be empty."
            )

        self.burden_va = (
            self._validate_non_negative(
                self.burden_va,
                "burden_va",
            )
        )

        self.phase_displacement_deg = (
            self._validate_finite(
                self.phase_displacement_deg,
                "phase_displacement_deg",
            )
        )

        if not isinstance(
            self.in_service,
            bool,
        ):
            raise TypeError(
                "in_service must be boolean."
            )

        for terminal in self.terminals:
            if terminal.owner is not self:
                raise ValueError(
                    f"PT '{self.id}' terminal ownership is invalid."
                )

        return True

    def validate(self) -> bool:
        """
        Validate the complete PT through the common model contract.
        """

        return super().validate()

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """Return structured PT diagnostic information."""

        def endpoint_id(
            terminal: Terminal,
        ) -> Any:
            endpoint = terminal.endpoint

            if endpoint is None:
                return None

            return getattr(
                endpoint,
                "id",
                endpoint,
            )

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "primary_voltage_kv":
                self.primary_voltage_kv,

            "secondary_voltage_v":
                self.secondary_voltage_v,

            "ratio":
                self.voltage_ratio,

            "accuracy_class":
                self.accuracy_class,

            "burden_va":
                self.burden_va,

            "phase_displacement_deg":
                self.phase_displacement_deg,

            "in_service":
                self.in_service,

            "primary_a":
                endpoint_id(self.primary_a),

            "primary_b":
                endpoint_id(self.primary_b),

            "secondary_a":
                endpoint_id(self.secondary_a),

            "secondary_b":
                endpoint_id(self.secondary_b),

            "is_primary_connected":
                self.is_primary_connected,

            "is_secondary_connected":
                self.is_secondary_connected,

            "is_connected":
                self.is_connected,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        return (
            f"<PT "
            f"id={self.id}, "
            f"ratio={self.voltage_ratio:.6f}, "
            f"accuracy={self.accuracy_class}, "
            f"in_service={self.in_service}>"
        )

    # =================================================================
    # VALIDATION HELPERS
    # =================================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """Convert to float and require a finite value."""

        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc

        if not math.isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        return value

    @classmethod
    def _validate_positive(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Convert to float and require value > 0."""

        value = cls._validate_finite(
            value,
            name,
        )

        if value <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

        return value

    @classmethod
    def _validate_non_negative(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Convert to float and require value >= 0."""

        value = cls._validate_finite(
            value,
            name,
        )

        if value < 0.0:
            raise ValueError(
                f"{name} cannot be negative."
            )

        return value


__all__ = [
    "PT",
]
