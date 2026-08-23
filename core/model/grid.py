# core/model/grid.py
"""
GridForge V2 Grid Model
=======================

Author:
    Subhendu Mishra

Grid is an electrical source/equipment element representing an
external utility/grid source.

Grid is NOT:
    - a network container
    - a collection of buses
    - a collection of loads
    - a collection of generators
    - a topology manager
    - a Y-bus builder
    - a solver
    - an SLD container
    - a GUI object

The authoritative physical connection is:

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

Positive P/Q represent injection into the electrical network.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Grid(ElectricalObject, Injection):
    """
    External utility/grid source electrical model.

    Grid is an electrical element, not a network model.

    The Grid may exist disconnected from the network. Connectivity is
    established through its Terminal by the application/network layer.
    """

    TYPE = "GRID"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        endpoint=None,
        nominal_voltage_kv: float = 0.0,
        frequency_hz: float = 50.0,
        voltage_pu: float = 1.0,
        angle_deg: float = 0.0,
        p_mw: float = 0.0,
        q_mvar: float = 0.0,
        short_circuit_mva: Optional[float] = None,
        x_over_r: Optional[float] = None,
        z1_pu: Optional[complex] = None,
        z2_pu: Optional[complex] = None,
        z0_pu: Optional[complex] = None,
        in_service: bool = True,
        grounded: bool = True,
        *,
        bus=None,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # ---------------------------------------------------------
        # Compatibility
        # ---------------------------------------------------------

        if endpoint is not None and bus is not None and endpoint is not bus:
            raise ValueError(
                f"Grid '{self.id}' received both endpoint and bus "
                "with different values."
            )

        if endpoint is None:
            endpoint = bus

        # ---------------------------------------------------------
        # Electrical source parameters
        # ---------------------------------------------------------

        self.nominal_voltage_kv = self._validate_non_negative(
            nominal_voltage_kv,
            "nominal_voltage_kv",
        )

        self.frequency_hz = self._validate_positive(
            frequency_hz,
            "frequency_hz",
        )

        self.voltage_pu = self._validate_positive(
            voltage_pu,
            "voltage_pu",
        )

        self.angle_deg = self._validate_finite(
            angle_deg,
            "angle_deg",
        )

        self.p_mw = self._validate_finite(
            p_mw,
            "p_mw",
        )

        self.q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

        # ---------------------------------------------------------
        # Short-circuit/source impedance data
        # ---------------------------------------------------------

        self.short_circuit_mva = self._validate_optional_positive(
            short_circuit_mva,
            "short_circuit_mva",
        )

        self.x_over_r = self._validate_optional_positive(
            x_over_r,
            "x_over_r",
        )

        self.z1_pu = self._validate_optional_impedance(
            z1_pu,
            "z1_pu",
        )

        self.z2_pu = self._validate_optional_impedance(
            z2_pu,
            "z2_pu",
        )

        self.z0_pu = self._validate_optional_impedance(
            z0_pu,
            "z0_pu",
        )

        # ---------------------------------------------------------
        # Operating state
        # ---------------------------------------------------------

        self.in_service = bool(in_service)
        self.grounded = bool(grounded)

        # ---------------------------------------------------------
        # Physical terminal
        #
        # Grid OWNS the terminal.
        # The terminal is the authoritative local connection.
        # ---------------------------------------------------------

        self.terminal = Terminal(
            endpoint=endpoint,
            owner=self,
        )

        # ---------------------------------------------------------
        # Optional engineering extensions
        # ---------------------------------------------------------

        self._extensions: dict[str, Any] = {}

        self.validate_parameters()

    # =============================================================
    # IDENTITY
    # =============================================================

    @property
    def element_type(self) -> str:
        """Return the canonical GridForge element type."""
        return self.TYPE

    # =============================================================
    # CONNECTIVITY
    # =============================================================

    @property
    def endpoint(self):
        """
        Return the authoritative physical endpoint.

        Terminal.endpoint is authoritative.
        """
        return self.terminal.endpoint

    @property
    def bus(self):
        """
        Compatibility accessor.

        This is derived from Terminal and is not authoritative.
        """
        return self.terminal.bus

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """Return the Grid's physical terminal."""
        return (self.terminal,)

    @property
    def is_connected(self) -> bool:
        """Return whether the Grid has a physical endpoint."""
        return self.terminal.is_connected

    def connect_endpoint(self, endpoint) -> None:
        """
        Connect the Grid terminal.

        Global topology is NOT modified here.
        """
        self.terminal.connect(endpoint)

    def disconnect_endpoint(self) -> None:
        """
        Disconnect the Grid terminal locally.

        Global topology is NOT modified here.
        """
        self.terminal.disconnect()

    # =============================================================
    # OPERATING STATE
    # =============================================================

    def connect(self) -> None:
        """Place the Grid source in service."""
        self.in_service = True

    def disconnect(self) -> None:
        """Take the Grid source out of service."""
        self.in_service = False

    @property
    def is_available(self) -> bool:
        """Return whether the source is in service."""
        return self.in_service

    # =============================================================
    # INJECTION CONTRACT
    # =============================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return Grid power injection.

        Positive P/Q mean injection into the electrical network.
        """
        return self.p_mw, self.q_mvar

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

    # =============================================================
    # VOLTAGE
    # =============================================================

    def set_voltage(
        self,
        voltage_pu: float,
        angle_deg: float = 0.0,
    ) -> None:
        """Set source voltage magnitude and angle."""

        self.voltage_pu = self._validate_positive(
            voltage_pu,
            "voltage_pu",
        )

        self.angle_deg = self._validate_finite(
            angle_deg,
            "angle_deg",
        )

    # =============================================================
    # SEQUENCE IMPEDANCE
    # =============================================================

    def set_sequence_impedances(
        self,
        *,
        z1_pu: Optional[complex] = None,
        z2_pu: Optional[complex] = None,
        z0_pu: Optional[complex] = None,
    ) -> None:
        """Set positive, negative and zero sequence impedances."""

        self.z1_pu = self._validate_optional_impedance(
            z1_pu,
            "z1_pu",
        )

        self.z2_pu = self._validate_optional_impedance(
            z2_pu,
            "z2_pu",
        )

        self.z0_pu = self._validate_optional_impedance(
            z0_pu,
            "z0_pu",
        )

    def has_sequence_impedance_data(self) -> bool:
        """Return whether positive-sequence impedance is available."""
        return self.z1_pu is not None

    # =============================================================
    # ENGINEERING VALIDATION
    # =============================================================

    def validate_parameters(self) -> bool:
        """
        Validate only Grid-local engineering parameters.

        Global topology/network validation belongs elsewhere.
        """

        self._validate_non_negative(
            self.nominal_voltage_kv,
            "nominal_voltage_kv",
        )

        self._validate_positive(
            self.frequency_hz,
            "frequency_hz",
        )

        self._validate_positive(
            self.voltage_pu,
            "voltage_pu",
        )

        self._validate_finite(
            self.angle_deg,
            "angle_deg",
        )

        self._validate_finite(
            self.p_mw,
            "p_mw",
        )

        self._validate_finite(
            self.q_mvar,
            "q_mvar",
        )

        return True

    # =============================================================
    # EXTENSIONS
    # =============================================================

    def register_extension(
        self,
        extension_id: str,
        extension: Any,
    ) -> None:
        """Register an optional engineering extension."""

        if not isinstance(extension_id, str):
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
        """Return an extension, or None when not registered."""
        return self._extensions.get(extension_id)

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
        return tuple(self._extensions.keys())

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict[str, Any]:
        """Return a diagnostic summary."""

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,
            "nominal_voltage_kv": self.nominal_voltage_kv,
            "frequency_hz": self.frequency_hz,
            "voltage_pu": self.voltage_pu,
            "angle_deg": self.angle_deg,
            "p_mw": self.p_mw,
            "q_mvar": self.q_mvar,
            "short_circuit_mva": self.short_circuit_mva,
            "x_over_r": self.x_over_r,
            "z1_pu": self.z1_pu,
            "z2_pu": self.z2_pu,
            "z0_pu": self.z0_pu,
            "in_service": self.in_service,
            "grounded": self.grounded,
            "endpoint": self.endpoint,
            "is_connected": self.is_connected,
            "extensions": self.extension_ids,
        }

    # =============================================================
    # VALIDATION HELPERS
    # =============================================================

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        value = float(value)

        if not math.isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        return value

    @staticmethod
    def _validate_positive(
        value: float,
        name: str,
    ) -> float:
        value = float(value)

        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(
                f"{name} must be finite and greater than zero."
            )

        return value

    @staticmethod
    def _validate_non_negative(
        value: float,
        name: str,
    ) -> float:
        value = float(value)

        if not math.isfinite(value) or value < 0.0:
            raise ValueError(
                f"{name} must be finite and non-negative."
            )

        return value

    @staticmethod
    def _validate_optional_positive(
        value: Optional[float],
        name: str,
    ) -> Optional[float]:
        if value is None:
            return None

        return Grid._validate_positive(
            value,
            name,
        )

    @staticmethod
    def _validate_optional_impedance(
        value: Optional[complex],
        name: str,
    ) -> Optional[complex]:
        if value is None:
            return None

        value = complex(value)

        if not (
            math.isfinite(value.real)
            and math.isfinite(value.imag)
        ):
            raise ValueError(
                f"{name} must contain finite real and imaginary parts."
            )

        return value
