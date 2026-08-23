# core/model/grid.py
"""
GridForge V2 Grid Model
=======================

Author:
    Subhendu Mishra

Grid is an electrical source element representing an external
utility/grid connection.

Grid is NOT:

    - a network container
    - a collection of buses
    - a collection of loads
    - a collection of generators
    - a topology manager
    - a graph
    - a Y-bus builder
    - a solver
    - an SLD container
    - a GUI object

Authoritative physical connection:

    Grid
      |
    Terminal
      |
    Terminal.endpoint
      |
    Network / Topology
      |
     Bus

Grid implements the common Injection contract.

Power convention:

    Positive P/Q = injection into the electrical network.

The Network layer owns topology.
The Grid model owns only Grid-local electrical/source state.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Grid(ElectricalObject, Injection):
    """
    External utility/grid source electrical model.

    A Grid may exist while disconnected from the network.

    Connectivity is established through its Terminal.
    Network topology is never modified directly by this model.
    """

    TYPE = "GRID"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        endpoint: Any = None,
        nominal_voltage_kv: float = 0.0,
        frequency_hz: float = 50.0,
        voltage_pu: float = 1.0,
        angle_deg: float = 0.0,
        p_mw: float = 0.0,
        q_mvar: float = 0.0,
        short_circuit_mva: float | None = None,
        x_over_r: float | None = None,
        z1_pu: complex | None = None,
        z2_pu: complex | None = None,
        z0_pu: complex | None = None,
        in_service: bool = True,
        grounded: bool = True,
        bus: Any = None,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # =============================================================
        # COMPATIBILITY
        # =============================================================

        if (
            endpoint is not None
            and bus is not None
            and endpoint is not bus
        ):
            raise ValueError(
                f"Grid '{self.id}' received both endpoint and bus "
                "with different values."
            )

        if endpoint is None:
            endpoint = bus

        # =============================================================
        # ELECTRICAL SOURCE PARAMETERS
        # =============================================================

        self.nominal_voltage_kv = (
            self._validate_non_negative(
                nominal_voltage_kv,
                "nominal_voltage_kv",
            )
        )

        self.frequency_hz = (
            self._validate_positive(
                frequency_hz,
                "frequency_hz",
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

        self.p_mw = (
            self._validate_finite(
                p_mw,
                "p_mw",
            )
        )

        self.q_mvar = (
            self._validate_finite(
                q_mvar,
                "q_mvar",
            )
        )

        # =============================================================
        # SHORT-CIRCUIT / SOURCE IMPEDANCE DATA
        # =============================================================

        self.short_circuit_mva = (
            self._validate_optional_positive(
                short_circuit_mva,
                "short_circuit_mva",
            )
        )

        self.x_over_r = (
            self._validate_optional_positive(
                x_over_r,
                "x_over_r",
            )
        )

        self.z1_pu = (
            self._validate_optional_impedance(
                z1_pu,
                "z1_pu",
            )
        )

        self.z2_pu = (
            self._validate_optional_impedance(
                z2_pu,
                "z2_pu",
            )
        )

        self.z0_pu = (
            self._validate_optional_impedance(
                z0_pu,
                "z0_pu",
            )
        )

        # =============================================================
        # OPERATING STATE
        # =============================================================

        if not isinstance(
            in_service,
            bool,
        ):
            raise TypeError(
                "in_service must be boolean."
            )

        if not isinstance(
            grounded,
            bool,
        ):
            raise TypeError(
                "grounded must be boolean."
            )

        self.in_service = in_service
        self.grounded = grounded

        # =============================================================
        # AUTHORITATIVE PHYSICAL TERMINAL
        # =============================================================

        self.terminal = Terminal(
            endpoint=endpoint,
            owner=self,
        )

        # =============================================================
        # OPTIONAL ENGINEERING EXTENSIONS
        # =============================================================

        self._extensions: dict[str, Any] = {}

        # =============================================================
        # COMMON MODEL VALIDATION CONTRACT
        # =============================================================

        self.validate()

    # =================================================================
    # IDENTITY
    # =================================================================

    @property
    def element_type(self) -> str:
        """Return the canonical GridForge element type."""

        return self.TYPE

    # =================================================================
    # TERMINALS
    # =================================================================

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """Return the Grid's physical terminal."""

        return (
            self.terminal,
        )

    # =================================================================
    # CONNECTIVITY
    # =================================================================

    @property
    def endpoint(self) -> Any:
        """
        Return the authoritative physical endpoint.

        Terminal.endpoint is authoritative.
        """

        return self.terminal.endpoint

    @property
    def bus(self) -> Any:
        """
        Compatibility accessor.

        Bus state is derived from the Terminal and is not stored
        independently by Grid.
        """

        return self.terminal.bus

    @property
    def is_connected(self) -> bool:
        """Return whether the Grid terminal has an endpoint."""

        return self.terminal.is_connected

    def connect_endpoint(
        self,
        endpoint: Any,
    ) -> None:
        """
        Connect the Grid terminal locally.

        This does not modify global network topology.
        """

        if endpoint is None:
            raise ValueError(
                f"Grid '{self.id}' endpoint cannot be None."
            )

        self.terminal.connect(
            endpoint
        )

    def disconnect_endpoint(self) -> None:
        """
        Disconnect the Grid terminal locally.

        This does not modify global network topology.
        """

        self.terminal.disconnect()

    # =================================================================
    # OPERATING STATE
    # =================================================================

    @property
    def is_in_service(self) -> bool:
        """Return whether the Grid source is in service."""

        return self.in_service

    @property
    def is_out_of_service(self) -> bool:
        """Return whether the Grid source is out of service."""

        return not self.in_service

    @property
    def is_available(self) -> bool:
        """Return whether the source is available for injection."""

        return self.in_service

    def put_in_service(self) -> None:
        """Place the Grid source in service."""

        self.in_service = True

    def take_out_of_service(self) -> None:
        """Take the Grid source out of service."""

        self.in_service = False

    # Compatibility aliases.
    #
    # These names describe service state, not terminal connectivity.
    # New application code should prefer put_in_service() and
    # take_out_of_service().

    def connect(self) -> None:
        """Compatibility alias for put_in_service()."""

        self.put_in_service()

    def disconnect(self) -> None:
        """Compatibility alias for take_out_of_service()."""

        self.take_out_of_service()

    # =================================================================
    # INJECTION CONTRACT
    # =================================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return Grid network injection.

        Positive P/Q represent injection into the network.

        An out-of-service Grid contributes no injection.
        """

        if not self.in_service:
            return (
                0.0,
                0.0,
            )

        return (
            self.p_mw,
            self.q_mvar,
        )

    def set_power(
        self,
        p_mw: float,
        q_mvar: float,
    ) -> None:
        """Set Grid active/reactive power injection."""

        self.p_mw = self._validate_finite(
            p_mw,
            "p_mw",
        )

        self.q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

    @property
    def active_power_mw(self) -> float:
        """Return active power injection."""

        return self.p_mw

    @property
    def reactive_power_mvar(self) -> float:
        """Return reactive power injection."""

        return self.q_mvar

    # =================================================================
    # VOLTAGE
    # =================================================================

    def set_voltage(
        self,
        voltage_pu: float,
        angle_deg: float = 0.0,
    ) -> None:
        """
        Set source voltage magnitude and angle.
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

    # =================================================================
    # SEQUENCE IMPEDANCE
    # =================================================================

    def set_sequence_impedances(
        self,
        *,
        z1_pu: complex | None = None,
        z2_pu: complex | None = None,
        z0_pu: complex | None = None,
    ) -> None:
        """
        Set positive-, negative- and zero-sequence impedances.
        """

        self.z1_pu = (
            self._validate_optional_impedance(
                z1_pu,
                "z1_pu",
            )
        )

        self.z2_pu = (
            self._validate_optional_impedance(
                z2_pu,
                "z2_pu",
            )
        )

        self.z0_pu = (
            self._validate_optional_impedance(
                z0_pu,
                "z0_pu",
            )
        )

    def has_sequence_impedance_data(self) -> bool:
        """Return whether positive-sequence impedance is available."""

        return self.z1_pu is not None

    # =================================================================
    # VALIDATION
    # =================================================================

    def validate_parameters(self) -> bool:
        """
        Validate Grid-local engineering parameters.

        Network topology is deliberately not validated here.
        """

        self.nominal_voltage_kv = (
            self._validate_non_negative(
                self.nominal_voltage_kv,
                "nominal_voltage_kv",
            )
        )

        self.frequency_hz = (
            self._validate_positive(
                self.frequency_hz,
                "frequency_hz",
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

        self.p_mw = (
            self._validate_finite(
                self.p_mw,
                "p_mw",
            )
        )

        self.q_mvar = (
            self._validate_finite(
                self.q_mvar,
                "q_mvar",
            )
        )

        self.short_circuit_mva = (
            self._validate_optional_positive(
                self.short_circuit_mva,
                "short_circuit_mva",
            )
        )

        self.x_over_r = (
            self._validate_optional_positive(
                self.x_over_r,
                "x_over_r",
            )
        )

        self.z1_pu = (
            self._validate_optional_impedance(
                self.z1_pu,
                "z1_pu",
            )
        )

        self.z2_pu = (
            self._validate_optional_impedance(
                self.z2_pu,
                "z2_pu",
            )
        )

        self.z0_pu = (
            self._validate_optional_impedance(
                self.z0_pu,
                "z0_pu",
            )
        )

        if not isinstance(
            self.in_service,
            bool,
        ):
            raise TypeError(
                "in_service must be boolean."
            )

        if not isinstance(
            self.grounded,
            bool,
        ):
            raise TypeError(
                "grounded must be boolean."
            )

        if self.terminal.owner is not self:
            raise ValueError(
                f"Grid '{self.id}' terminal ownership is invalid."
            )

        return True

    def validate(self) -> bool:
        """
        Validate the complete Grid model through the common
        ElectricalObject validation contract.
        """

        return super().validate()

    # =================================================================
    # EXTENSIONS
    # =================================================================

    def register_extension(
        self,
        extension_id: str,
        extension: Any,
    ) -> None:
        """Register an optional engineering extension."""

        if not isinstance(
            extension_id,
            str,
        ):
            raise TypeError(
                "extension_id must be a string."
            )

        extension_id = extension_id.strip()

        if not extension_id:
            raise ValueError(
                "extension_id cannot be empty."
            )

        if extension is None:
            raise ValueError(
                "extension cannot be None."
            )

        if extension_id in self._extensions:
            raise ValueError(
                f"Extension '{extension_id}' is already registered."
            )

        self._extensions[extension_id] = extension

    def get_extension(
        self,
        extension_id: str,
    ) -> Any | None:
        """Return an extension, or None."""

        return self._extensions.get(
            extension_id
        )

    def remove_extension(
        self,
        extension_id: str,
    ) -> Any | None:
        """Remove and return an extension."""

        return self._extensions.pop(
            extension_id,
            None,
        )

    @property
    def extension_ids(self) -> tuple[str, ...]:
        """Return registered extension identifiers."""

        return tuple(
            self._extensions.keys()
        )

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def summary(self) -> dict[str, Any]:
        """Return a structured Grid diagnostic summary."""

        endpoint_id = None

        if self.endpoint is not None:
            endpoint_id = getattr(
                self.endpoint,
                "id",
                self.endpoint,
            )

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "terminal": self.terminal.id,
            "endpoint": endpoint_id,
            "is_connected": self.is_connected,

            "nominal_voltage_kv":
                self.nominal_voltage_kv,

            "frequency_hz":
                self.frequency_hz,

            "voltage_pu":
                self.voltage_pu,

            "angle_deg":
                self.angle_deg,

            "p_mw":
                self.p_mw,

            "q_mvar":
                self.q_mvar,

            "injection":
                self.get_power(),

            "short_circuit_mva":
                self.short_circuit_mva,

            "x_over_r":
                self.x_over_r,

            "z1_pu":
                self.z1_pu,

            "z2_pu":
                self.z2_pu,

            "z0_pu":
                self.z0_pu,

            "in_service":
                self.in_service,

            "grounded":
                self.grounded,

            "extensions":
                self.extension_ids,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        endpoint_id = None

        if self.endpoint is not None:
            endpoint_id = getattr(
                self.endpoint,
                "id",
                self.endpoint,
            )

        return (
            f"<Grid "
            f"id={self.id}, "
            f"endpoint={endpoint_id}, "
            f"P={self.p_mw:.6f} MW, "
            f"Q={self.q_mvar:.6f} MVAr, "
            f"V={self.voltage_pu:.6f} pu, "
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

    @staticmethod
    def _validate_optional_impedance(
        value: complex | None,
        name: str,
    ) -> complex | None:
        """Validate an optional finite complex impedance."""

        if value is None:
            return None

        try:
            value = complex(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{name} must be a valid complex value."
            ) from exc

        if not (
            math.isfinite(value.real)
            and math.isfinite(value.imag)
        ):
            raise ValueError(
                f"{name} must contain finite real and "
                "imaginary parts."
            )

        return value


__all__ = [
    "Grid",
]
