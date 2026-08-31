# ============================================================
# File: core/model/bus.py
# GridForge V2 — Bus Model
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Bus Model
========================

Authoritative electrical Bus model.

Architecture
------------

    ElectricalObject
          |
          v
         Bus
          |
          v
       Terminal
          |
          v
       Endpoint

The Bus owns:

    - identity
    - nominal electrical parameters
    - operating state
    - exactly one authoritative Terminal

The Terminal owns:

    - endpoint connectivity
    - connection state

The Bus does NOT own:

    - global Network topology
    - SLD geometry
    - canvas state
    - solver state
    - UI state

Terminal Contract
-----------------

The canonical Terminal API is:

    Terminal(owner=self, role="bus")

    terminal.attach(endpoint)
    terminal.detach()

    terminal.endpoint
    terminal.is_connected

No duplicate authoritative endpoint state is maintained by Bus.

The ``bus`` object itself is an electrical domain object and
may serve as an endpoint for other electrical model terminals.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal


class Bus(ElectricalObject):
    """
    Authoritative electrical bus.

    A Bus owns one Terminal representing its external electrical
    connection point.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    name:
        Human-readable bus name.

    nominal_voltage_kv:
        Nominal bus voltage in kV.

    voltage_pu:
        Present bus voltage magnitude in per-unit.

    angle_deg:
        Present bus voltage angle in degrees.

    frequency_hz:
        Nominal system frequency in Hz.

    in_service:
        Whether the bus is operationally in service.
    """

    TYPE = "BUS"

    def __init__(
        self,
        id: str,
        *,
        name: str = "",
        nominal_voltage_kv: float = 0.0,
        voltage_pu: float = 1.0,
        angle_deg: float = 0.0,
        frequency_hz: float = 50.0,
        in_service: bool = True,
    ) -> None:
        """
        Construct an authoritative Bus.

        The Bus always creates and owns its own Terminal.
        """

        ElectricalObject.__init__(
            self,
            id=id,
            name=name,
        )

        # ========================================================
        # ELECTRICAL PARAMETERS
        # ========================================================

        self.nominal_voltage_kv = (
            self._validate_non_negative(
                nominal_voltage_kv,
                "nominal_voltage_kv",
            )
        )

        self.voltage_pu = (
            self._validate_positive(
                voltage_pu,
                "voltage_pu",
            )
        )

        self.angle_deg = (
            self._validate_finite(
                angle_deg,
                "angle_deg",
            )
        )

        self.frequency_hz = (
            self._validate_positive(
                frequency_hz,
                "frequency_hz",
            )
        )

        # ========================================================
        # OPERATING STATE
        # ========================================================

        self.in_service = self._validate_bool(
            in_service,
            "in_service",
        )

        # ========================================================
        # AUTHORITATIVE TERMINAL
        # ========================================================

        self._terminal = Terminal(
            owner=self,
            role="bus",
        )

        # ========================================================
        # COMMON VALIDATION
        # ========================================================

        self.validate()

    # ============================================================
    # IDENTITY
    # ============================================================

    @property
    def element_type(self) -> str:
        """Return canonical GridForge element type."""

        return self.TYPE

    # ============================================================
    # TERMINAL
    # ============================================================

    @property
    def terminal(self) -> Terminal:
        """
        Return the Bus's authoritative Terminal.
        """

        return self._terminal

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """
        Return the Bus terminal collection.
        """

        return (
            self._terminal,
        )

    # ============================================================
    # CONNECTIVITY
    # ============================================================

    @property
    def endpoint(self) -> Any | None:
        """
        Return the Terminal endpoint.

        Terminal.endpoint is the sole authoritative connectivity
        state.
        """

        return self._terminal.endpoint

    @property
    def is_connected(self) -> bool:
        """
        Return whether the Bus Terminal has an endpoint.
        """

        return self._terminal.is_connected

    def connect_endpoint(
        self,
        endpoint: Any,
    ) -> None:
        """
        Attach the Bus Terminal to an endpoint.

        Uses the frozen Terminal API.
        """

        if endpoint is None:
            raise ValueError(
                f"Bus '{self.id}' endpoint cannot be None."
            )

        self._terminal.attach(
            endpoint
        )

    def disconnect_endpoint(self) -> None:
        """
        Detach the Bus Terminal.

        Uses the frozen Terminal API.
        """

        self._terminal.detach()

    # ============================================================
    # VOLTAGE
    # ============================================================

    def set_voltage(
        self,
        voltage_pu: float,
        angle_deg: float = 0.0,
    ) -> None:
        """
        Set bus voltage magnitude and phase angle.
        """

        self.voltage_pu = (
            self._validate_positive(
                voltage_pu,
                "voltage_pu",
            )
        )

        self.angle_deg = (
            self._validate_finite(
                angle_deg,
                "angle_deg",
            )
        )

    @property
    def voltage_angle_rad(self) -> float:
        """Return bus voltage angle in radians."""

        return math.radians(
            self.angle_deg
        )

    @property
    def voltage_complex_pu(self) -> complex:
        """
        Return the bus voltage as a complex per-unit quantity.
        """

        angle = math.radians(
            self.angle_deg
        )

        return (
            self.voltage_pu
            * complex(
                math.cos(angle),
                math.sin(angle),
            )
        )

    # ============================================================
    # OPERATING STATE
    # ============================================================

    @property
    def is_in_service(self) -> bool:
        """Return whether the Bus is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return whether the Bus is out of service."""

        return not self.in_service

    def put_in_service(self) -> None:
        """Place the Bus in service."""

        self.in_service = True

    def take_out_of_service(self) -> None:
        """Take the Bus out of service."""

        self.in_service = False

    def set_in_service(
        self,
        value: bool,
    ) -> None:
        """Set Bus operating state."""

        self.in_service = self._validate_bool(
            value,
            "in_service",
        )

    # ============================================================
    # VALIDATION
    # ============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Bus-local electrical parameters.
        """

        self.nominal_voltage_kv = (
            self._validate_non_negative(
                self.nominal_voltage_kv,
                "nominal_voltage_kv",
            )
        )

        self.voltage_pu = (
            self._validate_positive(
                self.voltage_pu,
                "voltage_pu",
            )
        )

        self.angle_deg = (
            self._validate_finite(
                self.angle_deg,
                "angle_deg",
            )
        )

        self.frequency_hz = (
            self._validate_positive(
                self.frequency_hz,
                "frequency_hz",
            )
        )

        self.in_service = (
            self._validate_bool(
                self.in_service,
                "in_service",
            )
        )

        return True

    def validate(self) -> bool:
        """
        Validate the complete Bus model.

        Global topology is intentionally not validated here.
        """

        self.validate_parameters()

        if not isinstance(
            self._terminal,
            Terminal,
        ):
            raise TypeError(
                "Bus terminal must be a Terminal."
            )

        if self._terminal.owner is not self:
            raise ValueError(
                f"Bus '{self.id}' terminal ownership is invalid."
            )

        if self._terminal.role != "bus":
            raise ValueError(
                "Bus terminal role must be 'bus'."
            )

        self._terminal.validate()

        return super().validate()

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def summary(self) -> dict[str, Any]:
        """
        Return a structured Bus diagnostic summary.
        """

        endpoint = self._terminal.endpoint

        endpoint_id = None

        if endpoint is not None:
            endpoint_id = getattr(
                endpoint,
                "id",
                endpoint,
            )

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "terminal": self._terminal,
            "terminal_role": self._terminal.role,

            "endpoint": endpoint_id,
            "is_connected":
                self._terminal.is_connected,

            "nominal_voltage_kv":
                self.nominal_voltage_kv,

            "voltage_pu":
                self.voltage_pu,

            "angle_deg":
                self.angle_deg,

            "frequency_hz":
                self.frequency_hz,

            "voltage_complex_pu":
                self.voltage_complex_pu,

            "in_service":
                self.in_service,
        }

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        return (
            f"<Bus "
            f"id={self.id}, "
            f"V={self.voltage_pu:.6f} pu, "
            f"angle={self.angle_deg:.6f} deg, "
            f"in_service={self.in_service}>"
        )

    # ============================================================
    # VALIDATION HELPERS
    # ============================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """Convert to float and require a finite value."""

        try:
            numeric = float(
                value
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{name} must be numeric."
            ) from exc

        if not math.isfinite(
            numeric
        ):
            raise ValueError(
                f"{name} must be finite."
            )

        return numeric

    @classmethod
    def _validate_positive(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Convert to float and require value > 0."""

        numeric = cls._validate_finite(
            value,
            name,
        )

        if numeric <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

        return numeric

    @classmethod
    def _validate_non_negative(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Convert to float and require value >= 0."""

        numeric = cls._validate_finite(
            value,
            name,
        )

        if numeric < 0.0:
            raise ValueError(
                f"{name} cannot be negative."
            )

        return numeric

    @staticmethod
    def _validate_bool(
        value: bool,
        name: str,
    ) -> bool:
        """Validate a strict boolean."""

        if not isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be boolean."
            )

        return value


__all__ = [
    "Bus",
]
