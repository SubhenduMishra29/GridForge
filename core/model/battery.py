# core/model/battery.py
"""
GridForge V2 Battery Model
==========================

Author:
    Subhendu Mishra

A Battery is a bidirectional electrical energy-storage element.

The model represents the STATIC electrical equipment state.

Architecture
------------

    Battery
    ├── ElectricalObject
    ├── Injection
    └── Terminal
          │
          └── endpoint
                │
                └── network/topology

Battery owns:

    - electrical operating point
    - active/reactive power capability
    - nominal voltage/frequency
    - energy capacity
    - state of charge
    - SOC limits
    - charge/discharge capability
    - service state
    - optional dynamic-model binding

Battery does NOT own:

    - network topology
    - Bus collections
    - SLD state
    - Y-bus construction
    - power-flow solving
    - short-circuit calculations
    - protection
    - inverter control execution
    - dynamic simulation
    - GUI state

Power convention
----------------

    P > 0
        Battery discharges and injects active power into
        the electrical network.

    P < 0
        Battery charges and absorbs active power from
        the electrical network.

Dynamic simulation
------------------

Dynamic behavior is deliberately separated from this model.

A future dynamic architecture may attach a separate model:

    Battery
       │
       └── DynamicBatteryModel
               ├── SOC dynamics
               ├── converter dynamics
               ├── inverter controls
               ├── current controls
               └── grid-forming/grid-following behavior

The static Battery model must remain valid independently of
that dynamic architecture.

Units
-----

    p_mw / q_mvar:
        MW / MVAr

    energy_capacity_mwh:
        MWh

    nominal_voltage_kv:
        kV

    frequency_hz:
        Hz

    voltage_pu:
        per-unit

    soc:
        0.0 ... 1.0

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .injection import Injection
from .terminal import Terminal


class Battery(ElectricalObject, Injection):
    """
    Static bidirectional battery electrical model.

    Positive active power means discharge/injection.

    Negative active power means charge/absorption.

    Connectivity is represented by the Battery's Terminal.
    """

    TYPE = "BATTERY"

    def __init__(
        self,
        id: str,
        name: str = "",
        *,
        endpoint=None,
        bus=None,
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
        nominal_voltage_kv: float | None = None,
        frequency_hz: float = 50.0,
        voltage_pu: float = 1.0,
        round_trip_efficiency: float = 1.0,
        in_service: bool = True,
    ) -> None:
        """
        Create a static Battery model.

        Parameters
        ----------
        id:
            Stable GridForge object identifier.

        name:
            Human-readable name.

        endpoint:
            Authoritative physical electrical endpoint.

        bus:
            Backward-compatible endpoint alias.

        p_mw:
            Current active-power operating point.

        q_mvar:
            Current reactive-power operating point.

        p_discharge_max_mw:
            Maximum active power the battery can inject.

        p_charge_max_mw:
            Maximum active power the battery can absorb.

        q_min_mvar:
            Minimum reactive-power capability.

        q_max_mvar:
            Maximum reactive-power capability.

        energy_capacity_mwh:
            Usable energy capacity.

        soc:
            Current state of charge.

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
            Static efficiency representation.

        in_service:
            Whether the battery is electrically in service.
        """

        super().__init__(
            id=id,
            name=name,
        )

        # =========================================================
        # ENDPOINT COMPATIBILITY
        # =========================================================

        if (
            endpoint is not None
            and bus is not None
            and endpoint is not bus
        ):
            raise ValueError(
                f"Battery '{self.id}' received both endpoint and "
                "bus with different values."
            )

        if endpoint is None:
            endpoint = bus

        # =========================================================
        # ELECTRICAL OPERATING POINT
        # =========================================================

        self.p_mw = self._validate_finite(
            p_mw,
            "p_mw",
        )

        self.q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

        # =========================================================
        # ACTIVE POWER CAPABILITY
        # =========================================================

        self.p_discharge_max_mw = (
            self._validate_non_negative(
                p_discharge_max_mw,
                "p_discharge_max_mw",
            )
        )

        self.p_charge_max_mw = (
            self._validate_non_negative(
                p_charge_max_mw,
                "p_charge_max_mw",
            )
        )

        # =========================================================
        # REACTIVE POWER CAPABILITY
        # =========================================================

        self.q_min_mvar = self._validate_finite(
            q_min_mvar,
            "q_min_mvar",
        )

        self.q_max_mvar = self._validate_finite(
            q_max_mvar,
            "q_max_mvar",
        )

        # =========================================================
        # ENERGY / SOC
        # =========================================================

        self.energy_capacity_mwh = (
            self._validate_non_negative(
                energy_capacity_mwh,
                "energy_capacity_mwh",
            )
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
                f"Battery '{self.id}' soc_min cannot exceed "
                "soc_max."
            )

        self.soc = self._validate_soc(
            soc,
            "soc",
        )

        if not self.soc_min <= self.soc <= self.soc_max:
            raise ValueError(
                f"Battery '{self.id}' SOC must be between "
                f"soc_min={self.soc_min} and "
                f"soc_max={self.soc_max}."
            )

        self.round_trip_efficiency = (
            self._validate_efficiency(
                round_trip_efficiency,
                "round_trip_efficiency",
            )
        )

        # =========================================================
        # ELECTRICAL RATING / OPERATING STATE
        # =========================================================

        self.nominal_voltage_kv = (
            self._validate_optional_positive(
                nominal_voltage_kv,
                "nominal_voltage_kv",
            )
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

        # =========================================================
        # PHYSICAL ELECTRICAL TERMINAL
        # =========================================================

        self.terminal = Terminal(
            endpoint=endpoint,
            owner=self,
        )

        # =========================================================
        # OPTIONAL DYNAMIC MODEL BINDING
        # =========================================================

        self._dynamic_model: Any | None = None

        # =========================================================
        # EXTENSIONS
        # =========================================================

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
        """
        Return the authoritative physical endpoint.

        The Battery does not own network topology.
        """

        return self.terminal.endpoint

    @property
    def bus(self):
        """
        Compatibility accessor for the connected Bus.

        The Bus is derived from the Terminal and is NOT the
        authoritative connectivity state.
        """

        return self.terminal.bus

    @property
    def terminals(self) -> tuple[Terminal, ...]:
        """Return the Battery electrical terminal."""

        return (self.terminal,)

    @property
    def is_connected(self) -> bool:
        """Return whether the Battery has an endpoint."""

        return self.terminal.is_connected

    def connect_endpoint(self, endpoint) -> None:
        """
        Connect the Battery terminal to an endpoint.

        Network topology remains outside this model.
        """

        self.terminal.connect(endpoint)

    def disconnect_endpoint(self) -> None:
        """Disconnect the Battery terminal."""

        self.terminal.disconnect()

    # =============================================================
    # SERVICE STATE
    # =============================================================

    def connect(self) -> None:
        """Place the Battery in service."""

        self.in_service = True

    def disconnect(self) -> None:
        """Take the Battery out of service."""

        self.in_service = False

    @property
    def is_available(self) -> bool:
        """Return whether the Battery is in service."""

        return self.in_service

    # =============================================================
    # INJECTION CONTRACT
    # =============================================================

    def get_power(self) -> tuple[float, float]:
        """
        Return network power injection.

        Returns
        -------
        tuple[float, float]
            (P, Q) in MW / MVAr.

        Sign convention
        ----------------

        P > 0:
            discharge / network injection

        P < 0:
            charge / network absorption
        """

        if not self.in_service:
            return 0.0, 0.0

        return self.p_mw, self.q_mvar

    # =============================================================
    # POWER CONTROL
    # =============================================================

    def set_power(
        self,
        p_mw: float,
        q_mvar: float,
    ) -> None:
        """Set active and reactive power."""

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

    @property
    def active_power(self) -> float:
        """Return active-power injection."""

        return self.p_mw

    @property
    def reactive_power(self) -> float:
        """Return reactive-power injection."""

        return self.q_mvar

    def set_active_power(
        self,
        p_mw: float,
    ) -> None:
        """Set active power within capability."""

        p_mw = self._validate_finite(
            p_mw,
            "p_mw",
        )

        self._validate_active_power(p_mw)

        self.p_mw = p_mw

    def set_reactive_power(
        self,
        q_mvar: float,
    ) -> None:
        """Set reactive power within capability."""

        q_mvar = self._validate_finite(
            q_mvar,
            "q_mvar",
        )

        self._validate_reactive_power(q_mvar)

        self.q_mvar = q_mvar

    # =============================================================
    # OPERATING MODE
    # =============================================================

    @property
    def is_discharging(self) -> bool:
        """Return True when the Battery is discharging."""

        return self.p_mw > 0.0

    @property
    def is_charging(self) -> bool:
        """Return True when the Battery is charging."""

        return self.p_mw < 0.0

    @property
    def is_idle(self) -> bool:
        """Return True when active power is effectively zero."""

        return math.isclose(
            self.p_mw,
            0.0,
            abs_tol=1e-12,
        )

    # =============================================================
    # ACTIVE POWER LIMITS
    # =============================================================

    def set_discharge_limit(
        self,
        value_mw: float,
    ) -> None:
        """Set maximum discharge power."""

        value_mw = self._validate_non_negative(
            value_mw,
            "p_discharge_max_mw",
        )

        if self.p_mw > value_mw:
            raise ValueError(
                f"Battery '{self.id}' current discharge "
                f"power {self.p_mw} MW exceeds the new "
                f"limit {value_mw} MW."
            )

        self.p_discharge_max_mw = value_mw

    def set_charge_limit(
        self,
        value_mw: float,
    ) -> None:
        """Set maximum charging power."""

        value_mw = self._validate_non_negative(
            value_mw,
            "p_charge_max_mw",
        )

        if self.p_mw < -value_mw:
            raise ValueError(
                f"Battery '{self.id}' current charging "
                f"power {abs(self.p_mw)} MW exceeds the "
                f"new limit {value_mw} MW."
            )

        self.p_charge_max_mw = value_mw

    # =============================================================
    # REACTIVE POWER LIMITS
    # =============================================================

    @property
    def q_limits(self) -> tuple[float, float]:
        """Return reactive-power capability limits."""

        return (
            self.q_min_mvar,
            self.q_max_mvar,
        )

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
                f"Battery '{self.id}' Qmin cannot exceed Qmax."
            )

        if not q_min_mvar <= self.q_mvar <= q_max_mvar:
            raise ValueError(
                f"Battery '{self.id}' current Q={self.q_mvar} "
                "MVAr would violate the new Q limits."
            )

        self.q_min_mvar = q_min_mvar
        self.q_max_mvar = q_max_mvar

    # =============================================================
    # ENERGY / SOC
    # =============================================================

    @property
    def available_energy_mwh(self) -> float:
        """Return current stored energy."""

        return (
            self.energy_capacity_mwh
            * self.soc
        )

    @property
    def minimum_energy_mwh(self) -> float:
        """Return energy corresponding to minimum SOC."""

        return (
            self.energy_capacity_mwh
            * self.soc_min
        )

    @property
    def maximum_energy_mwh(self) -> float:
        """Return energy corresponding to maximum SOC."""

        return (
            self.energy_capacity_mwh
            * self.soc_max
        )

    def set_soc(
        self,
        soc: float,
    ) -> None:
        """Set state of charge."""

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
                f"Battery '{self.id}' soc_min cannot exceed "
                "soc_max."
            )

        if not soc_min <= self.soc <= soc_max:
            raise ValueError(
                f"Battery '{self.id}' current SOC is outside "
                "the proposed SOC limits."
            )

        self.soc_min = soc_min
        self.soc_max = soc_max

    # =============================================================
    # ELECTRICAL OPERATING PARAMETERS
    # =============================================================

    def set_voltage(
        self,
        voltage_pu: float,
    ) -> None:
        """Set static operating voltage in per-unit."""

        self.voltage_pu = self._validate_positive(
            voltage_pu,
            "voltage_pu",
        )

    def set_frequency(
        self,
        frequency_hz: float,
    ) -> None:
        """Set nominal operating frequency."""

        self.frequency_hz = self._validate_positive(
            frequency_hz,
            "frequency_hz",
        )

    # =============================================================
    # DYNAMIC MODEL BINDING
    # =============================================================

    @property
    def dynamic_model(self) -> Any | None:
        """
        Return the optional dynamic-model binding.

        The Battery itself does not execute the dynamic model.
        """

        return self._dynamic_model

    def attach_dynamic_model(
        self,
        dynamic_model: Any,
    ) -> None:
        """
        Attach an external dynamic-model object.

        The supplied object is stored only as a reference.

        Dynamic simulation remains the responsibility of the
        simulation layer.
        """

        if dynamic_model is None:
            raise ValueError(
                "dynamic_model cannot be None."
            )

        self._dynamic_model = dynamic_model

    def detach_dynamic_model(self) -> Any | None:
        """
        Detach and return the current dynamic model.
        """

        dynamic_model = self._dynamic_model
        self._dynamic_model = None

        return dynamic_model

    # =============================================================
    # EXTENSIONS
    # =============================================================

    def set_extension(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Store an optional engineering extension.

        Extensions are metadata only. They do not modify the
        electrical topology.
        """

        if not isinstance(key, str) or not key.strip():
            raise ValueError(
                "Extension key must be a non-empty string."
            )

        self._extensions[key] = value

    def get_extension(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Return an extension value."""

        return self._extensions.get(
            key,
            default,
        )

    def remove_extension(
        self,
        key: str,
    ) -> Any:
        """Remove and return an extension value."""

        return self._extensions.pop(
            key,
            None,
        )

    @property
    def extensions(self) -> dict[str, Any]:
        """
        Return a copy of engineering extensions.
        """

        return dict(self._extensions)

    # =============================================================
    # VALIDATION
    # =============================================================

    def validate_parameters(self) -> bool:
        """
        Validate Battery-local engineering parameters.

        This does not validate:

            - network topology
            - connected Bus
            - power-flow convergence
            - protection
            - dynamic simulation
        """

        self.p_mw = self._validate_finite(
            self.p_mw,
            "p_mw",
        )

        self.q_mvar = self._validate_finite(
            self.q_mvar,
            "q_mvar",
        )

        self.p_discharge_max_mw = (
            self._validate_non_negative(
                self.p_discharge_max_mw,
                "p_discharge_max_mw",
            )
        )

        self.p_charge_max_mw = (
            self._validate_non_negative(
                self.p_charge_max_mw,
                "p_charge_max_mw",
            )
        )

        self.q_min_mvar = self._validate_finite(
            self.q_min_mvar,
            "q_min_mvar",
        )

        self.q_max_mvar = self._validate_finite(
            self.q_max_mvar,
            "q_max_mvar",
        )

        if self.q_min_mvar > self.q_max_mvar:
            raise ValueError(
                f"Battery '{self.id}' q_min_mvar cannot "
                "exceed q_max_mvar."
            )

        self.energy_capacity_mwh = (
            self._validate_non_negative(
                self.energy_capacity_mwh,
                "energy_capacity_mwh",
            )
        )

        self.soc_min = self._validate_soc(
            self.soc_min,
            "soc_min",
        )

        self.soc_max = self._validate_soc(
            self.soc_max,
            "soc_max",
        )

        if self.soc_min > self.soc_max:
            raise ValueError(
                f"Battery '{self.id}' soc_min cannot "
                "exceed soc_max."
            )

        self.soc = self._validate_soc(
            self.soc,
            "soc",
        )

        if not self.soc_min <= self.soc <= self.soc_max:
            raise ValueError(
                f"Battery '{self.id}' SOC must be between "
                f"soc_min={self.soc_min} and "
                f"soc_max={self.soc_max}."
            )

        self.nominal_voltage_kv = (
            self._validate_optional_positive(
                self.nominal_voltage_kv,
                "nominal_voltage_kv",
            )
        )

        self.frequency_hz = self._validate_positive(
            self.frequency_hz,
            "frequency_hz",
        )

        self.voltage_pu = self._validate_positive(
            self.voltage_pu,
            "voltage_pu",
        )

        self.round_trip_efficiency = (
            self._validate_efficiency(
                self.round_trip_efficiency,
                "round_trip_efficiency",
            )
        )

        self._validate_active_power(
            self.p_mw,
        )

        self._validate_reactive_power(
            self.q_mvar,
        )

        return True

    def validate(self) -> bool:
        """Public Battery validation entry point."""

        return self.validate_parameters()

    # =============================================================
    # DIAGNOSTICS
    # =============================================================

    def summary(self) -> dict[str, Any]:
        """Return structured Battery diagnostics."""

        return {
            "id": self.id,
            "name": self.name,
            "type": self.TYPE,

            "endpoint": self.endpoint,
            "connected": self.is_connected,

            "in_service": self.in_service,

            "p_mw": self.p_mw,
            "q_mvar": self.q_mvar,

            "p_discharge_max_mw":
                self.p_discharge_max_mw,

            "p_charge_max_mw":
                self.p_charge_max_mw,

            "q_min_mvar":
                self.q_min_mvar,

            "q_max_mvar":
                self.q_max_mvar,

            "energy_capacity_mwh":
                self.energy_capacity_mwh,

            "soc": self.soc,
            "soc_min": self.soc_min,
            "soc_max": self.soc_max,

            "available_energy_mwh":
                self.available_energy_mwh,

            "nominal_voltage_kv":
                self.nominal_voltage_kv,

            "frequency_hz":
                self.frequency_hz,

            "voltage_pu":
                self.voltage_pu,

            "round_trip_efficiency":
                self.round_trip_efficiency,

            "dynamic_model_attached":
                self._dynamic_model is not None,
        }

    # =============================================================
    # REPRESENTATION
    # =============================================================

    def __repr__(self) -> str:
        """Return concise developer-facing representation."""

        return (
            f"<Battery "
            f"id={self.id}, "
            f"P={self.p_mw:.6f} MW, "
            f"Q={self.q_mvar:.6f} MVAr, "
            f"SOC={self.soc:.4f}, "
            f"in_service={self.in_service}>"
        )

    # =============================================================
    # INTERNAL VALIDATION
    # =============================================================

    def _validate_active_power(
        self,
        p_mw: float,
    ) -> None:
        """Validate active power against charge/discharge limits."""

        if p_mw > self.p_discharge_max_mw:
            raise ValueError(
                f"Battery '{self.id}' active power "
                f"{p_mw} MW exceeds discharge limit "
                f"{self.p_discharge_max_mw} MW."
            )

        if p_mw < -self.p_charge_max_mw:
            raise ValueError(
                f"Battery '{self.id}' active power "
                f"{p_mw} MW exceeds charge limit "
                f"-{self.p_charge_max_mw} MW."
            )

        # Static SOC boundary checks.
        if self.energy_capacity_mwh > 0.0:

            if (
                p_mw > 0.0
                and self.soc <= self.soc_min
            ):
                raise ValueError(
                    f"Battery '{self.id}' cannot discharge "
                    "below soc_min."
                )

            if (
                p_mw < 0.0
                and self.soc >= self.soc_max
            ):
                raise ValueError(
                    f"Battery '{self.id}' cannot charge "
                    "above soc_max."
                )

    def _validate_reactive_power(
        self,
        q_mvar: float,
    ) -> None:
        """Validate reactive power against capability limits."""

        if not (
            self.q_min_mvar
            <= q_mvar
            <= self.q_max_mvar
        ):
            raise ValueError(
                f"Battery '{self.id}' reactive power "
                f"{q_mvar} MVAr is outside the capability "
                f"range "
                f"[{self.q_min_mvar}, "
                f"{self.q_max_mvar}] MVAr."
            )

    @staticmethod
    def _validate_finite(
        value: float,
        name: str,
    ) -> float:
        """Return a finite floating-point value."""

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
    def _validate_non_negative(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Return a finite non-negative value."""

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
    def _validate_positive(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Return a finite positive value."""

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
    def _validate_soc(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Validate SOC in the range 0.0 ... 1.0."""

        value = cls._validate_finite(
            value,
            name,
        )

        if not 0.0 <= value <= 1.0:
            raise ValueError(
                f"{name} must be between 0.0 and 1.0."
            )

        return value

    @classmethod
    def _validate_efficiency(
        cls,
        value: float,
        name: str,
    ) -> float:
        """Validate efficiency in the range (0.0, 1.0]."""

        value = cls._validate_finite(
            value,
            name,
        )

        if not 0.0 < value <= 1.0:
            raise ValueError(
                f"{name} must be greater than 0.0 "
                "and less than or equal to 1.0."
            )

        return value
