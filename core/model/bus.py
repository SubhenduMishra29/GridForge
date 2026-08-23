# core/model/bus.py
"""
GridForge V2 Bus Model
======================

Author:
    Subhendu Mishra

A Bus is a first-class electrical network node.

IMPORTANT ARCHITECTURAL RULE
----------------------------

A Bus is NOT a container.

It does not own:

    - loads
    - generators
    - motors
    - transformers
    - lines
    - cables
    - breakers
    - network collections
    - SLD graphics
    - GUI state

Those relationships are managed by the network/topology and
application layers.

The Bus owns only its own electrical state and parameters.

Electrical responsibilities
----------------------------

The Bus may define:

    - bus type
    - voltage magnitude
    - voltage angle
    - nominal voltage
    - active/reactive power specification
    - voltage setpoint
    - reactive power limits

The Bus does NOT:

    - build Y-bus
    - solve load flow
    - solve short circuit
    - calculate network topology
    - perform protection
    - perform dynamic simulation
    - own SLD geometry

Bus type
--------

    PQ
        Load bus.

    PV
        Generator-controlled voltage bus.

    SLACK
        Reference/slack bus.

The exact study-specific interpretation of these values belongs
to the numerical/analysis layers.

Units
-----

    voltage:
        per-unit unless otherwise stated

    angle:
        radians

    P/Q:
        per-unit

    nominal_voltage_kv:
        kV

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import Any

from .base import ElectricalObject


class BusType(str, Enum):
    """
    Standard load-flow bus classifications.
    """

    PQ = "PQ"
    PV = "PV"
    SLACK = "SLACK"


class Bus(ElectricalObject):
    """
    First-class electrical Bus model.

    The Bus represents an electrical node.

    It is intentionally NOT a collection/container for other
    electrical equipment.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    name:
        Human-readable bus name.

    bus_type:
        PQ, PV, or SLACK.

    nominal_voltage_kv:
        Nominal bus voltage in kV.

    voltage_magnitude:
        Per-unit voltage magnitude.

    voltage_angle:
        Voltage angle in radians.

    p:
        Active-power specification in per-unit.

    q:
        Reactive-power specification in per-unit.

    voltage_setpoint:
        Voltage magnitude setpoint in per-unit.

    q_min:
        Minimum reactive-power limit in per-unit.

    q_max:
        Maximum reactive-power limit in per-unit.
    """

    TYPE = "BUS"

    def __init__(
        self,
        id: str,
        *,
        name: str = "",
        bus_type: BusType | str = BusType.PQ,
        nominal_voltage_kv: float | None = None,
        voltage_magnitude: float = 1.0,
        voltage_angle: float = 0.0,
        p: float = 0.0,
        q: float = 0.0,
        voltage_setpoint: float = 1.0,
        q_min: float | None = None,
        q_max: float | None = None,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # ---------------------------------------------------------
        # Electrical classification
        # ---------------------------------------------------------

        self.bus_type = self._normalize_bus_type(
            bus_type
        )

        # ---------------------------------------------------------
        # Electrical parameters
        # ---------------------------------------------------------

        self.nominal_voltage_kv = (
            self._validate_optional_positive(
                nominal_voltage_kv,
                "nominal_voltage_kv",
            )
        )

        self.voltage_magnitude = (
            self._validate_positive(
                voltage_magnitude,
                "voltage_magnitude",
            )
        )

        self.voltage_angle = (
            self._validate_finite(
                voltage_angle,
                "voltage_angle",
            )
        )

        self.p = self._validate_finite(
            p,
            "p",
        )

        self.q = self._validate_finite(
            q,
            "q",
        )

        self.voltage_setpoint = (
            self._validate_positive(
                voltage_setpoint,
                "voltage_setpoint",
            )
        )

        self.q_min = (
            self._validate_optional_finite(
                q_min,
                "q_min",
            )
        )

        self.q_max = (
            self._validate_optional_finite(
                q_max,
                "q_max",
            )
        )

        self.validate_parameters()

    # =============================================================
    # IDENTITY
    # =============================================================

    @property
    def element_type(self) -> str:
        """
        Return canonical GridForge element type.
        """

        return self.TYPE

    # =============================================================
    # BUS TYPE
    # =============================================================

    @staticmethod
    def _normalize_bus_type(
        value: BusType | str,
    ) -> BusType:
        """
        Normalize a bus type to BusType.
        """

        if isinstance(value, BusType):
            return value

        try:
            return BusType(
                str(value).upper()
            )
        except ValueError as exc:
            valid = ", ".join(
                item.value
                for item in BusType
            )

            raise ValueError(
                f"Invalid bus_type '{value}'. "
                f"Expected one of: {valid}."
            ) from exc

    def set_bus_type(
        self,
        bus_type: BusType | str,
    ) -> None:
        """
        Set bus classification.
        """

        self.bus_type = self._normalize_bus_type(
            bus_type
        )

        self.validate_parameters()

    @property
    def is_pq(self) -> bool:
        """Return True for PQ buses."""

        return self.bus_type is BusType.PQ

    @property
    def is_pv(self) -> bool:
        """Return True for PV buses."""

        return self.bus_type is BusType.PV

    @property
    def is_slack(self) -> bool:
        """Return True for the slack/reference bus."""

        return self.bus_type is BusType.SLACK

    # =============================================================
    # VOLTAGE STATE
    # =============================================================

    @property
    def voltage_complex(self) -> complex:
        """
        Return the current complex voltage in per-unit.

            V = |V| ∠ angle
        """

        return (
            self.voltage_magnitude
            * complex(
                math.cos(self.voltage_angle),
                math.sin(self.voltage_angle),
            )
        )

    @property
    def voltage_real(self) -> float:
        """Return real component of bus voltage."""

        return self.voltage_complex.real

    @property
    def voltage_imag(self) -> float:
        """Return imaginary component of bus voltage."""

        return self.voltage_complex.imag

    def set_voltage(
        self,
        magnitude: float,
        angle: float,
    ) -> None:
        """
        Set bus voltage state.

        Values are local electrical state only. No solver is run.
        """

        magnitude = self._validate_positive(
            magnitude,
            "magnitude",
        )

        angle = self._validate_finite(
            angle,
            "angle",
        )

        self.voltage_magnitude = magnitude
        self.voltage_angle = angle

    def set_voltage_magnitude(
        self,
        magnitude: float,
    ) -> None:
        """Set voltage magnitude in per-unit."""

        self.voltage_magnitude = (
            self._validate_positive(
                magnitude,
                "magnitude",
            )
        )

    def set_voltage_angle(
        self,
        angle: float,
    ) -> None:
        """Set voltage angle in radians."""

        self.voltage_angle = (
            self._validate_finite(
                angle,
                "angle",
            )
        )

    # =============================================================
    # POWER SPECIFICATION
    # =============================================================

    def set_power(
        self,
        p: float,
        q: float,
    ) -> None:
        """
        Set active and reactive power specifications.

        Sign convention is study-level data. The Bus does not
        reinterpret the values or execute a power-flow calculation.
        """

        p = self._validate_finite(
            p,
            "p",
        )

        q = self._validate_finite(
            q,
            "q",
        )

        self.p = p
        self.q = q

    def set_active_power(
        self,
        p: float,
    ) -> None:
        """Set active-power specification."""

        self.p = self._validate_finite(
            p,
            "p",
        )

    def set_reactive_power(
        self,
        q: float,
    ) -> None:
        """Set reactive-power specification."""

        self.q = self._validate_finite(
            q,
            "q",
        )

    # =============================================================
    # VOLTAGE SETPOINT
    # =============================================================

    def set_voltage_setpoint(
        self,
        value: float,
    ) -> None:
        """
        Set voltage magnitude setpoint in per-unit.
        """

        self.voltage_setpoint = (
            self._validate_positive(
                value,
                "voltage_setpoint",
            )
        )

    # =============================================================
    # REACTIVE POWER LIMITS
    # =============================================================

    def set_q_limits(
        self,
        q_min: float | None,
        q_max: float | None,
    ) -> None:
        """
        Set reactive-power limits.

        Both limits are optional.

        If both are supplied:

            q_min <= q_max
        """

        q_min = self._validate_optional_finite(
            q_min,
            "q_min",
        )

        q_max = self._validate_optional_finite(
            q_max,
            "q_max",
        )

        if (
            q_min is not None
            and q_max is not None
            and q_min > q_max
        ):
            raise ValueError(
                "q_min cannot be greater than q_max."
            )

        self.q_min = q_min
        self.q_max = q_max

    @property
    def has_q_limits(self) -> bool:
        """Return whether both reactive limits are defined."""

        return (
            self.q_min is not None
            and self.q_max is not None
        )

    def is_q_within_limits(
        self,
        q: float | None = None,
    ) -> bool:
        """
        Check whether a reactive-power value is within the
        configured limits.

        If q is omitted, the Bus's current q value is checked.
        """

        value = (
            self.q
            if q is None
            else self._validate_finite(
                q,
                "q",
            )
        )

        if (
            self.q_min is not None
            and value < self.q_min
        ):
            return False

        if (
            self.q_max is not None
            and value > self.q_max
        ):
            return False

        return True

    # =============================================================
    # VALIDATION
    # =============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Bus-local electrical parameters.

        This does not validate network topology or a particular
        numerical study.
        """

        self.bus_type = self._normalize_bus_type(
            self.bus_type
        )

        self.nominal_voltage_kv = (
            self._validate_optional_positive(
                self.nominal_voltage_kv,
                "nominal_voltage_kv",
            )
        )

        self.voltage_magnitude = (
            self._validate_positive(
                self.voltage_magnitude,
                "voltage_magnitude",
            )
        )

        self.voltage_angle = (
            self._validate_finite(
                self.voltage_angle,
                "voltage_angle",
            )
        )

        self.p = self._validate_finite(
            self.p,
            "p",
        )

        self.q = self._validate_finite(
            self.q,
            "q",
        )

        self.voltage_setpoint = (
            self._validate_positive(
                self.voltage_setpoint,
                "voltage_setpoint",
            )
        )

        self.q_min = (
            self._validate_optional_finite(
                self.q_min,
                "q_min",
            )
        )

        self.q_max = (
            self._validate_optional_finite(
                self.q_max,
                "q_max",
            )
        )

        if (
            self.q_min is not None
            and self.q_max is not None
            and self.q_min > self.q_max
        ):
            raise ValueError(
                "q_min cannot be greater than q_max."
            )

        return True

    def validate(self) -> bool:
        """
        Public local validation entry point.
        """

        return self.validate_parameters()

    # Backward-compatible private validation wrapper.
    def _validate_state(self) -> None:
        """
        Compatibility wrapper for the previous Bus implementation.

        New code should use validate_parameters().
        """

        self.validate_parameters()

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return structured Bus diagnostics.

        No connected equipment is included because the Bus is not
        a container.
        """

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,
            "bus_type": self.bus_type.value,

            "nominal_voltage_kv":
                self.nominal_voltage_kv,

            "voltage_magnitude":
                self.voltage_magnitude,

            "voltage_angle":
                self.voltage_angle,

            "voltage_complex":
                self.voltage_complex,

            "p": self.p,
            "q": self.q,

            "voltage_setpoint":
                self.voltage_setpoint,

            "q_min": self.q_min,
            "q_max": self.q_max,

            "q_within_limits":
                self.is_q_within_limits(),
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self) -> str:
        """
        Return concise developer-facing representation.
        """

        return (
            f"<Bus "
            f"id={self.id}, "
            f"type={self.bus_type.value}, "
            f"V={self.voltage_magnitude:.6f}"
            f"∠{self.voltage_angle:.6f}, "
            f"P={self.p:.6f}, "
            f"Q={self.q:.6f}>"
        )

    # =============================================================
    # VALIDATION HELPERS
    # =============================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """Return a finite floating-point value."""

        value = float(value)

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
        """Return a finite value greater than zero."""

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
    def _validate_optional_positive(
        cls,
        value: float | None,
        name: str,
    ) -> float | None:
        """Validate an optional positive value."""

        if value is None:
            return None

        return cls._validate_positive(
            value,
            name,
        )

    @classmethod
    def _validate_optional_finite(
        cls,
        value: float | None,
        name: str,
    ) -> float | None:
        """Validate an optional finite value."""

        if value is None:
            return None

        return cls._validate_finite(
            value,
            name,
        )
