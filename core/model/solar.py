# core/model/solar.py
"""
GridForge V2 Solar Model
========================

Author:
    Subhendu Mishra

Solar is a static electrical generation/injection element.

Architecture
------------

    Solar
      |
      +-- ElectricalObject
      +-- Injection
      +-- Terminal
      |
      +-- static electrical operating data
      |
      +-- optional dynamic-model binding

Solar does NOT own:

    - Network topology
    - Bus collections
    - SLD state
    - Y-bus construction
    - Power-flow solving
    - Dynamic simulation
    - Protection
    - UI state

Physical connectivity is authoritative through:

    Solar
      |
    Terminal
      |
    Terminal.endpoint

Positive P/Q represent injection into the electrical network.

Dynamic PV/inverter behaviour is intentionally NOT implemented here.
It will be supplied later through the Dynamic Model architecture.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Solar(ElectricalObject, Injection):
    """
    Static solar-generation electrical model.

    A Solar element may be created before it is electrically connected.
    Therefore ``endpoint`` may be ``None``.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    name:
        Human-readable name.

    endpoint:
        Physical electrical endpoint. May be ``None``.

    p_mw:
        Current active-power injection.

    q_mvar:
        Current reactive-power injection.

    p_max_mw:
        Maximum available active power.

    q_min_mvar:
        Minimum reactive-power capability.

    q_max_mvar:
        Maximum reactive-power capability.

    nominal_voltage_kv:
        Nominal AC voltage.

    frequency_hz:
        Nominal system frequency.

    voltage_pu:
        Voltage operating value.

    in_service:
        Whether the Solar source is electrically in service.

    bus:
        Backward-compatible endpoint alias.
    """

    TYPE = "SOLAR"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        endpoint=None,
        p_mw: float = 0.0,
        q_mvar: float = 0.0,
        p_max_mw: float = 0.0,
        q_min_mvar: float = -float("inf"),
        q_max_mvar: float = float("inf"),
        nominal_voltage_kv: float = 0.0,
        frequency_hz: float = 50.0,
        voltage_pu: float = 1.0,
        in_service: bool = True,
        bus=None,
    ) -> None:

        super().__init__(
            id=id,
            name=name,
        )

        # ---------------------------------------------------------
        # Endpoint compatibility
        # ---------------------------------------------------------

        if endpoint is not None and bus is not None and endpoint is not bus:
            raise ValueError(
                f"Solar '{self.id}' received both endpoint and bus "
                "with different values."
            )

        if endpoint is None:
            endpoint = bus

        # ---------------------------------------------------------
        # Static electrical parameters
        # ---------------------------------------------------------

        self.p_mw = self._validate_finite(
            p_mw,
            "p_mw",
        )

        self.q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

        self.p_max_mw = self._validate_non_negative(
            p_max_mw,
            "p_max_mw",
        )

        self.q_min_mvar = self._validate_finite(
            q_min_mvar,
            "q_min_mvar",
        )

        self.q_max_mvar = self._validate_finite(
            q_max_mvar,
            "q_max_mvar",
        )

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

        self.in_service = bool(in_service)

        # ---------------------------------------------------------
        # Physical electrical terminal
        # ---------------------------------------------------------

        self.terminal = Terminal(
            endpoint=endpoint,
            owner=self,
        )

        # ---------------------------------------------------------
        # Dynamic model binding
        #
        # No dynamic behaviour is implemented here.
        # This reference allows future dynamic infrastructure to
        # associate a PV/inverter model without polluting this model.
        # ---------------------------------------------------------

        self._dynamic_model: Any | None = None

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

        Terminal.endpoint is the source of truth.
        """
        return self.terminal.endpoint

    @property
    def bus(self):
        """
        Compatibility accessor.

        The Bus is derived from Terminal and is not authoritative.
        """
        return self.terminal.bus

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """Return the Solar electrical terminal."""
        return (self.terminal,)

    @property
    def is_connected(self) -> bool:
        """Return whether Solar has a physical endpoint."""
        return self.terminal.is_connected

    def connect_endpoint(self, endpoint) -> None:
        """
        Connect Solar to an electrical endpoint.

        Global topology is managed outside this model.
        """
        self.terminal.connect(endpoint)

    def disconnect_endpoint(self) -> None:
        """
        Disconnect Solar from its electrical endpoint.
        """
        self.terminal.disconnect()

    # =============================================================
    # OPERATING STATE
    # =============================================================

    def connect(self) -> None:
        """Place Solar in service."""
        self.in_service = True

    def disconnect(self) -> None:
        """Take Solar out of service."""
        self.in_service = False

    @property
    def is_available(self) -> bool:
        """Return whether Solar is in service."""
        return self.in_service

    # =============================================================
    # INJECTION CONTRACT
    # =============================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return Solar network injection.

        Positive P/Q mean injection into the network.

        When Solar is out of service, zero injection is returned.
        """
        if not self.in_service:
            return 0.0, 0.0

        return self.p_mw, self.q_mvar

    def set_power(
        self,
        p_mw: float,
        q_mvar: float,
    ) -> None:
        """
        Set Solar active/reactive injection.

        The requested values are checked against the local static
        capability limits.
        """

        p_mw = self._validate_finite(
            p_mw,
            "p_mw",
        )

        q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

        if p_mw < 0.0:
            raise ValueError(
                f"Solar '{self.id}' active power cannot be negative."
            )

        if p_mw > self.p_max_mw:
            raise ValueError(
                f"Solar '{self.id}' active power {p_mw} MW exceeds "
                f"Pmax {self.p_max_mw} MW."
            )

        if q_mvar < self.q_min_mvar:
            raise ValueError(
                f"Solar '{self.id}' reactive power {q_mvar} MVAr "
                f"is below Qmin {self.q_min_mvar} MVAr."
            )

        if q_mvar > self.q_max_mvar:
            raise ValueError(
                f"Solar '{self.id}' reactive power {q_mvar} MVAr "
                f"exceeds Qmax {self.q_max_mvar} MVAr."
            )

        self.p_mw = p_mw
        self.q_mvar = q_mvar

    # =============================================================
    # ACTIVE POWER
    # =============================================================

    @property
    def active_power(self) -> float:
        """Return current active-power injection."""
        return self.p_mw

    @property
    def reactive_power(self) -> float:
        """Return current reactive-power injection."""
        return self.q_mvar

    def set_active_power(
        self,
        p_mw: float,
    ) -> None:
        """Set active power within Pmax capability."""

        p_mw = self._validate_finite(
            p_mw,
            "p_mw",
        )

        if p_mw < 0.0:
            raise ValueError(
                f"Solar '{self.id}' active power cannot be negative."
            )

        if p_mw > self.p_max_mw:
            raise ValueError(
                f"Solar '{self.id}' active power {p_mw} MW exceeds "
                f"Pmax {self.p_max_mw} MW."
            )

        self.p_mw = p_mw

    def set_active_power_limit(
        self,
        p_max_mw: float,
    ) -> None:
        """Set maximum available active power."""

        p_max_mw = self._validate_non_negative(
            p_max_mw,
            "p_max_mw",
        )

        if self.p_mw > p_max_mw:
            raise ValueError(
                f"Solar '{self.id}' Pmax cannot be set below "
                f"current active power {self.p_mw} MW."
            )

        self.p_max_mw = p_max_mw

    # =============================================================
    # REACTIVE POWER
    # =============================================================

    @property
    def q_limits(self) -> tuple[float, float]:
        """Return ``(Qmin, Qmax)``."""
        return self.q_min_mvar, self.q_max_mvar

    def set_reactive_power(
        self,
        q_mvar: float,
    ) -> None:
        """Set reactive power within capability limits."""

        q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

        if q_mvar < self.q_min_mvar:
            raise ValueError(
                f"Solar '{self.id}' reactive power is below Qmin."
            )

        if q_mvar > self.q_max_mvar:
            raise ValueError(
                f"Solar '{self.id}' reactive power exceeds Qmax."
            )

        self.q_mvar = q_mvar

    def set_q_limits(
        self,
        q_min_mvar: float,
        q_max_mvar: float,
    ) -> None:
        """Set reactive-power capability limits."""

        q_min_mvar = self._validate_finite(
            q_min_mvar,
            "q_min_mvar",
        )

        q_max_mvar = self._validate_finite(
            q_max_mvar,
            "q_max_mvar",
        )

        if q_min_mvar > q_max_mvar:
            raise ValueError(
                f"Solar '{self.id}' Qmin cannot exceed Qmax."
            )

        if not (
            q_min_mvar <= self.q_mvar <= q_max_mvar
        ):
            raise ValueError(
                f"Solar '{self.id}' existing Q={self.q_mvar} MVAr "
                "would violate the new Q limits."
            )

        self.q_min_mvar = q_min_mvar
        self.q_max_mvar = q_max_mvar

    # =============================================================
    # VOLTAGE
    # =============================================================

    def set_voltage(
        self,
        voltage_pu: float,
    ) -> None:
        """Set static operating voltage."""
        self.voltage_pu = self._validate_positive(
            voltage_pu,
            "voltage_pu",
        )

    # =============================================================
    # DYNAMIC MODEL BINDING
    # =============================================================

    @property
    def dynamic_model(self) -> Any | None:
        """
        Return the associated dynamic model reference.

        This is only a binding/reference. The Solar model does not
        execute the dynamic model.
        """
        return self._dynamic_model

    def bind_dynamic_model(
        self,
        model: Any,
    ) -> None:
        """
        Bind a dynamic model reference.

        Dynamic simulation remains the responsibility of the
        simulation/dynamics layer.
        """
        if model is None:
            raise ValueError(
                "Dynamic model cannot be None."
            )

        self._dynamic_model = model

    def unbind_dynamic_model(self) -> Any | None:
        """Remove and return the dynamic model reference."""
        model = self._dynamic_model
        self._dynamic_model = None
        return model

    @property
    def has_dynamic_model(self) -> bool:
        """Return whether a dynamic model is bound."""
        return self._dynamic_model is not None

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
        """Return an extension, or None."""
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
    # VALIDATION
    # =============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Solar-local engineering invariants.

        This does not validate network topology.
        """

        if self.p_mw < 0.0:
            raise ValueError(
                f"Solar '{self.id}' active power cannot be negative."
            )

        if self.p_mw > self.p_max_mw:
            raise ValueError(
                f"Solar '{self.id}' P exceeds Pmax."
            )

        if self.q_min_mvar > self.q_max_mvar:
            raise ValueError(
                f"Solar '{self.id}' Qmin cannot exceed Qmax."
            )

        if not (
            self.q_min_mvar
            <= self.q_mvar
            <= self.q_max_mvar
        ):
            raise ValueError(
                f"Solar '{self.id}' reactive power is outside "
                "its capability limits."
            )

        return True

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict[str, Any]:
        """Return a diagnostic summary."""

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,
            "p_mw": self.p_mw,
            "q_mvar": self.q_mvar,
            "p_max_mw": self.p_max_mw,
            "q_min_mvar": self.q_min_mvar,
            "q_max_mvar": self.q_max_mvar,
            "nominal_voltage_kv": self.nominal_voltage_kv,
            "frequency_hz": self.frequency_hz,
            "voltage_pu": self.voltage_pu,
            "in_service": self.in_service,
            "endpoint": self.endpoint,
            "is_connected": self.is_connected,
            "has_dynamic_model": self.has_dynamic_model,
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
