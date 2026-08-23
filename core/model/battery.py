# core/model/battery.py
"""
GridForge V2 Battery Model
==========================

Author:
    Subhendu Mishra

Battery is a bidirectional electrical energy-storage element.

Architecture
------------

    Battery
      |
      +-- ElectricalObject
      +-- Injection
      +-- Terminal
      |
      +-- static electrical operating data
      +-- energy/SOC data
      +-- charge/discharge limits
      +-- optional dynamic-model binding

Power convention
----------------

    P > 0  -> battery discharging -> injection into network
    P < 0  -> battery charging    -> absorption from network

Battery does NOT own:

    - Network topology
    - Bus collections
    - SLD state
    - Y-bus construction
    - Power-flow solving
    - Dynamic simulation
    - Inverter control execution
    - Protection
    - UI state

Dynamic battery, converter and inverter behavior belongs to the
separate Dynamic Model architecture.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Battery(ElectricalObject, Injection):
    """
    Static bidirectional battery electrical model.

    Positive active power means discharge/injection.
    Negative active power means charge/absorption.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    name:
        Human-readable name.

    endpoint:
        Physical electrical endpoint. May be None.

    p_mw:
        Current active-power operating point.

    q_mvar:
        Current reactive-power operating point.

    p_discharge_max_mw:
        Maximum active power delivered to the network.

    p_charge_max_mw:
        Maximum active power absorbed from the network.

    q_min_mvar:
        Minimum reactive-power capability.

    q_max_mvar:
        Maximum reactive-power capability.

    energy_capacity_mwh:
        Usable battery energy capacity.

    soc:
        State of charge in the range 0.0 to 1.0.

    soc_min:
        Minimum permissible SOC.

    soc_max:
        Maximum permissible SOC.

    nominal_voltage_kv:
        Nominal AC voltage.

    frequency_hz:
        Nominal system frequency.

    voltage_pu:
        Static operating voltage.

    round_trip_efficiency:
        Static charge/discharge efficiency representation.

    in_service:
        Whether the battery is in service.

    bus:
        Backward-compatible endpoint alias.
    """

    TYPE = "BATTERY"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        endpoint=None,
        p_mw: float = 0.0,
        q_mvar: float = 0.0,
        p_discharge_max_mw: float = 0.0,
        p_charge_max_mw: float = 0.0,
        q_min_mvar: float = -float("inf"),
        q_max_mvar: float = float("inf"),
        energy_capacity_mwh: float = 0.0,
        soc: float = 1.0,
        soc_min: float = 0.0,
        soc_max: float = 1.0,
        nominal_voltage_kv: float = 0.0,
        frequency_hz: float = 50.0,
        voltage_pu: float = 1.0,
        round_trip_efficiency: float = 1.0,
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
                f"Battery '{self.id}' received both endpoint and bus "
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

        self.p_discharge_max_mw = self._validate_non_negative(
            p_discharge_max_mw,
            "p_discharge_max_mw",
        )

        self.p_charge_max_mw = self._validate_non_negative(
            p_charge_max_mw,
            "p_charge_max_mw",
        )

        self.q_min_mvar = self._validate_finite(
            q_min_mvar,
            "q_min_mvar",
        )

        self.q_max_mvar = self._validate_finite(
            q_max_mvar,
            "q_max_mvar",
        )

        # ---------------------------------------------------------
        # Energy / SOC parameters
        # ---------------------------------------------------------

        self.energy_capacity_mwh = self._validate_non_negative(
            energy_capacity_mwh,
            "energy_capacity_mwh",
        )

        self.soc_min = self._validate_soc(
            soc_min,
            "soc_min",
        )

        self.soc_max = self._validate_soc(
            soc_max,
            "soc_max",
        )

        if self.soc_min > self.soc_max:
            raise ValueError(
                f"Battery '{self.id}' soc_min cannot exceed soc_max."
            )

        self.soc = self._validate_soc(
            soc,
            "soc",
        )

        if not self.soc_min <= self.soc <= self.soc_max:
            raise ValueError(
                f"Battery '{self.id}' SOC must be between "
                f"soc_min={self.soc_min} and soc_max={self.soc_max}."
            )

        self.round_trip_efficiency = self._validate_efficiency(
            round_trip_efficiency,
            "round_trip_efficiency",
        )

        # ---------------------------------------------------------
        # Electrical operating parameters
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

        self.in_service = bool(in_service)

        # ---------------------------------------------------------
        # Physical terminal
        # ---------------------------------------------------------

        self.terminal = Terminal(
            endpoint=endpoint,
            owner=self,
        )

        # ---------------------------------------------------------
        # Dynamic model binding
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
        """Return canonical GridForge element type."""
        return self.TYPE

    # =============================================================
    # CONNECTIVITY
    # =============================================================

    @property
    def endpoint(self):
        """Return the authoritative physical endpoint."""
        return self.terminal.endpoint

    @property
    def bus(self):
        """
        Compatibility accessor.

        Bus is derived from the terminal and is not authoritative.
        """
        return self.terminal.bus

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """Return the Battery electrical terminal."""
        return (self.terminal,)

    @property
    def is_connected(self) -> bool:
        """Return whether Battery has a physical endpoint."""
        return self.terminal.is_connected

    def connect_endpoint(self, endpoint) -> None:
        """
        Connect Battery to an electrical endpoint.

        Global topology is handled outside this model.
        """
        self.terminal.connect(endpoint)

    def disconnect_endpoint(self) -> None:
        """Disconnect Battery from its electrical endpoint."""
        self.terminal.disconnect()

    # =============================================================
    # OPERATING STATE
    # =============================================================

    def connect(self) -> None:
        """Place Battery in service."""
        self.in_service = True

    def disconnect(self) -> None:
        """Take Battery out of service."""
        self.in_service = False

    @property
    def is_available(self) -> bool:
        """Return whether Battery is in service."""
        return self.in_service

    # =============================================================
    # INJECTION CONTRACT
    # =============================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return network power injection.

        P > 0:
            Battery discharges into the network.

        P < 0:
            Battery absorbs power from the network.
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
        Set Battery active/reactive power.

        Active power is checked against charge/discharge capability.
        """

        p_mw = self._validate_finite(
            p_mw,
            "p_mw",
        )

        q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

        self._validate_active_power(p_mw)
        self._validate_reactive_power(q_mvar)

        self.p_mw = p_mw
        self.q_mvar = q_mvar

    # =============================================================
    # ACTIVE POWER
    # =============================================================

    @property
    def active_power(self) -> float:
        """Return active-power injection."""
        return self.p_mw

    @property
    def reactive_power(self) -> float:
        """Return reactive-power injection."""
        return self.q_mvar

    @property
    def is_discharging(self) -> bool:
        """Return True when Battery is injecting active power."""
        return self.p_mw > 0.0

    @property
    def is_charging(self) -> bool:
        """Return True when Battery is absorbing active power."""
        return self.p_mw < 0.0

    @property
    def is_idle(self) -> bool:
        """Return True when active power is zero."""
        return math.isclose(self.p_mw, 0.0, abs_tol=1e-12)

    def set_active_power(
        self,
        p_mw: float,
    ) -> None:
        """Set active power within charge/discharge capability."""

        p_mw = self._validate_finite(
            p_mw,
            "p_mw",
        )

        self._validate_active_power(p_mw)

        self.p_mw = p_mw

    def set_discharge_limit(
        self,
        p_discharge_max_mw: float,
    ) -> None:
        """Set maximum discharge power."""

        value = self._validate_non_negative(
            p_discharge_max_mw,
            "p_discharge_max_mw",
        )

        if self.p_mw > value:
            raise ValueError(
                f"Battery '{self.id}' current discharge power "
                f"{self.p_mw} MW exceeds the new limit {value} MW."
            )

        self.p_discharge_max_mw = value

    def set_charge_limit(
        self,
        p_charge_max_mw: float,
    ) -> None:
        """Set maximum charging power."""

        value = self._validate_non_negative(
            p_charge_max_mw,
            "p_charge_max_mw",
        )

        if self.p_mw < -value:
            raise ValueError(
                f"Battery '{self.id}' current charge power "
                f"{abs(self.p_mw)} MW exceeds the new limit {value} MW."
            )

        self.p_charge_max_mw = value

    # =============================================================
    # REACTIVE POWER
    # =============================================================

    @property
    def q_limits(self) -> tuple[float, float]:
        """Return reactive-power capability limits."""
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

        self._validate_reactive_power(q_mvar)

        self.q_mvar = q_mvar

    def set_q_limits(
        self,
        q_min_mvar: float,
        q_max_mvar: float,
    ) -> None:
        """Set reactive-power capability."""

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
                f"Battery '{self.id}' Qmin cannot exceed Qmax."
            )

        if not q_min_mvar <= self.q_mvar <= q_max_mvar:
            raise ValueError(
                f"Battery '{self.id}' current Q={self.q_mvar} MVAr "
                "would violate the new Q limits."
            )

        self.q_min_mvar = q_min_mvar
        self.q_max_mvar = q_max_mvar

    # =============================================================
    # ENERGY / SOC
    # =============================================================

    @property
    def available_energy_mwh(self) -> float:
        """Return current stored energy."""
        return self.energy_capacity_mwh * self.soc

    @property
    def minimum_energy_mwh(self) -> float:
        """Return energy corresponding to minimum SOC."""
        return self.energy_capacity_mwh * self.soc_min

    @property
    def maximum_energy_mwh(self) -> float:
        """Return energy corresponding to maximum SOC."""
        return self.energy_capacity_mwh * self.soc_max

    def set_soc(self, soc: float) -> None:
        """Set battery state of charge."""

        soc = self._validate_soc(
            soc,
            "soc",
        )

        if not self.soc_min <= soc <= self.soc_max:
            raise ValueError(
                f"Battery '{self.id}' SOC must be between "
                f"{self.soc_min} and {self.soc_max}."
            )

        self.soc = soc

    def set_soc_limits(
        self,
        soc_min: float,
        soc_max: float,
    ) -> None:
        """Set permissible SOC range."""

        soc_min = self._validate_soc(
            soc_min,
            "soc_min",
        )

        soc_max = self._validate_soc(
            soc_max,
            "soc_max",
        )

        if soc_min > soc_max:
            raise ValueError(
                f"Battery '{self.id}' soc_min cannot exceed soc_max."
            )

        if not soc_min <= self.soc <= soc_max:
            raise ValueError(
                f"Battery '{self.id}' current SOC is outside "
                "the proposed SOC limits."
            )

        self.soc_min = soc_min
        self.soc_max = soc_max

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

        The Battery does not execute this model.
        """
        return self._dynamic_model

    def bind_dynamic_model(
        self,
        model: Any,
    ) -> None:
        """
        Bind a dynamic battery/converter model.

        Dynamic simulation belongs to the simulation/dynamics layer.
        """
        if model is None:
            raise ValueError(
                "Dynamic model cannot be None."
            )

        self._dynamic_model = model

    def unbind_dynamic_model(self) -> Any | None:
        """Remove and return the dynamic model."""
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
        Validate Battery-local engineering invariants.

        This does not validate network topology.
        """

        if self.p_discharge_max_mw < 0.0:
            raise ValueError(
                "Discharge limit cannot be negative."
            )

        if self.p_charge_max_mw < 0.0:
            raise ValueError(
                "Charge limit cannot be negative."
            )

        if self.q_min_mvar > self.q_max_mvar:
            raise ValueError(
                f"Battery '{self.id}' Qmin cannot exceed Qmax."
            )

        if not (
            self.q_min_mvar
            <= self.q_mvar
            <= self.q_max_mvar
        ):
            raise ValueError(
                f"Battery '{self.id}' reactive power is outside "
                "its capability limits."
            )

        self._validate_active_power(
            self.p_mw,
        )

        if not self.soc_min <= self.soc <= self.soc_max:
            raise ValueError(
                f"Battery '{self.id}' SOC is outside its limits."
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
            "p_discharge_max_mw": self.p_discharge_max_mw,
            "p_charge_max_mw": self.p_charge_max_mw,
            "q_min_mvar": self.q_min_mvar,
            "q_max_mvar": self.q_max_mvar,
            "energy_capacity_mwh": self.energy_capacity_mwh,
            "soc": self.soc,
            "soc_min": self.soc_min,
            "soc_max": self.soc_max,
            "available_energy_mwh": self.available_energy_mwh,
            "nominal_voltage_kv": self.nominal_voltage_kv,
            "frequency_hz": self.frequency_hz,
            "voltage_pu": self.voltage_pu,
            "in_service": self.in_service,
            "is_charging": self.is_charging,
            "is_discharging": self.is_discharging,
            "endpoint": self.endpoint,
            "is_connected": self.is_connected,
            "has_dynamic_model": self.has_dynamic_model,
            "extensions": self.extension_ids,
        }

    # =============================================================
    # PRIVATE VALIDATION
    # =============================================================

    def _validate_active_power(
        self,
        p_mw: float,
    ) -> None:
        """
        Validate bidirectional active-power capability.

        Positive:
            discharge

        Negative:
            charge
        """

        if p_mw > self.p_discharge_max_mw:
            raise ValueError(
                f"Battery '{self.id}' active power {p_mw} MW "
                f"exceeds discharge limit "
                f"{self.p_discharge_max_mw} MW."
            )

        if p_mw < -self.p_charge_max_mw:
            raise ValueError(
                f"Battery '{self.id}' charging power "
                f"{abs(p_mw)} MW exceeds charge limit "
                f"{self.p_charge_max_mw} MW."
            )

        # Static SOC guard.
        #
        # Detailed SOC/time/efficiency behavior belongs to the
        # dynamic/storage simulation layer.
        if p_mw > 0.0 and self.soc <= self.soc_min:
            raise ValueError(
                f"Battery '{self.id}' cannot discharge below "
                "minimum SOC."
            )

        if p_mw < 0.0 and self.soc >= self.soc_max:
            raise ValueError(
                f"Battery '{self.id}' cannot charge above "
                "maximum SOC."
            )

    def _validate_reactive_power(
        self,
        q_mvar: float,
    ) -> None:

        if q_mvar < self.q_min_mvar:
            raise ValueError(
                f"Battery '{self.id}' reactive power "
                f"{q_mvar} MVAr is below Qmin "
                f"{self.q_min_mvar} MVAr."
            )

        if q_mvar > self.q_max_mvar:
            raise ValueError(
                f"Battery '{self.id}' reactive power "
                f"{q_mvar} MVAr exceeds Qmax "
                f"{self.q_max_mvar} MVAr."
            )

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
    def _validate_soc(
        value: float,
        name: str,
    ) -> float:
        value = float(value)

        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError(
                f"{name} must be finite and between 0.0 and 1.0."
            )

        return value

    @staticmethod
    def _validate_efficiency(
        value: float,
        name: str,
    ) -> float:
        value = float(value)

        if not math.isfinite(value) or not 0.0 < value <= 1.0:
            raise ValueError(
                f"{name} must be greater than 0.0 and "
                "less than or equal to 1.0."
            )

        return value
