# ============================================================
# File: core/model/battery.py
# GridForge V2 — Model Layer
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Battery Model
==========================

Defines the static electrical Battery model.

## Architecture

```
Battery
├── ElectricalObject
├── Injection
└── Terminal
```

The Battery model owns only its local engineering state and local
terminal reference.

The Battery does NOT own:

```
- network topology;
- Bus collections;
- graph management;
- Y-bus construction;
- power-flow solving;
- short-circuit calculations;
- protection logic;
- dynamic simulation;
- inverter/controller execution;
- project persistence;
- UI or SLD state.
```

## Power Convention

GridForge uses the network-injection convention:

```
P > 0
    Battery discharges and injects active power.

P < 0
    Battery charges and absorbs active power.
```

Reactive power follows the same injection convention:

```
Q > 0
    Reactive power injected.

Q < 0
    Reactive power absorbed.
```

## Connectivity

Electrical connectivity is represented locally through:

```
Battery.terminal.endpoint
```

The Network layer remains responsible for global topology and
electrical connectivity validation.

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

```
Parameters
----------
id:
    Stable GridForge object identifier.

name:
    Human-readable object name.

endpoint:
    Initial electrical endpoint for the Battery terminal.

bus:
    Compatibility alias for ``endpoint``.

p_mw:
    Active power injection.

    Positive values represent discharge.
    Negative values represent charging.

q_mvar:
    Reactive power injection.

p_discharge_max_mw:
    Maximum discharge power.

p_charge_max_mw:
    Maximum charging power.

q_min_mvar:
    Minimum reactive-power injection.

q_max_mvar:
    Maximum reactive-power injection.

energy_capacity_mwh:
    Usable battery energy capacity.

soc:
    Current state of charge in the range 0.0 to 1.0.

soc_min:
    Minimum permissible state of charge.

soc_max:
    Maximum permissible state of charge.

nominal_voltage_kv:
    Optional nominal AC voltage.

frequency_hz:
    Nominal system frequency.

in_service:
    Whether the Battery is electrically in service.
"""

TYPE = "BATTERY"

def __init__(
    self,
    id: str,
    name: str = "",
    *,
    endpoint: Any = None,
    bus: Any = None,
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
    in_service: bool = True,
) -> None:
    super().__init__(
        id=id,
        name=name,
    )

    endpoint = self._resolve_endpoint(
        endpoint=endpoint,
        bus=bus,
    )

    self.p_discharge_max_mw = self._validate_non_negative(
        p_discharge_max_mw,
        "p_discharge_max_mw",
    )

    self.p_charge_max_mw = self._validate_non_negative(
        p_charge_max_mw,
        "p_charge_max_mw",
    )

    self.q_min_mvar = self._validate_limit(
        q_min_mvar,
        "q_min_mvar",
    )

    self.q_max_mvar = self._validate_limit(
        q_max_mvar,
        "q_max_mvar",
    )

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
            "soc_min cannot exceed soc_max."
        )

    self.soc = self._validate_soc(
        soc,
        "soc",
    )

    if not self.soc_min <= self.soc <= self.soc_max:
        raise ValueError(
            "soc must be within the configured "
            "soc_min and soc_max limits."
        )

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

    self.in_service = bool(in_service)

    self.terminal = Terminal(
        endpoint=endpoint,
        owner=self,
    )

    self.p_mw = self._validate_finite(
        p_mw,
        "p_mw",
    )

    self.q_mvar = self._validate_finite(
        q_mvar,
        "q_mvar",
    )

    self.validate_parameters()

# ============================================================
# IDENTITY
# ============================================================

@property
def element_type(self) -> str:
    """Return the canonical GridForge element type."""

    return self.TYPE

# ============================================================
# CONNECTIVITY
# ============================================================

@property
def endpoint(self) -> Any:
    """
    Return the Battery terminal endpoint.

    This is a local model reference only. Global topology belongs
    to the Network layer.
    """

    return self.terminal.endpoint

@property
def bus(self) -> Any:
    """
    Return the Bus-like endpoint for compatibility.

    The authoritative local connection remains:

        terminal.endpoint
    """

    return self.terminal.bus

@property
def terminals(self) -> tuple[Terminal, ...]:
    """Return the Battery electrical terminal."""

    return (self.terminal,)

@property
def is_connected(self) -> bool:
    """Return whether the Battery terminal has an endpoint."""

    return self.terminal.is_connected

def connect_endpoint(
    self,
    endpoint: Any,
) -> None:
    """Connect the Battery terminal to an endpoint."""

    self.terminal.connect(endpoint)

def disconnect_endpoint(self) -> None:
    """Disconnect the Battery terminal."""

    self.terminal.disconnect()

# ============================================================
# SERVICE STATE
# ============================================================

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

# ============================================================
# INJECTION CONTRACT
# ============================================================

def get_power(self) -> tuple[float, float]:
    """
    Return the Battery network power injection.

    Returns
    -------
    tuple[float, float]
        ``(P, Q)`` in MW and MVAr.

    When the Battery is out of service, zero injection is
    returned.
    """

    if not self.in_service:
        return 0.0, 0.0

    return (
        self.p_mw,
        self.q_mvar,
    )

@property
def active_power(self) -> float:
    """Return active-power injection in MW."""

    return self.p_mw

@property
def reactive_power(self) -> float:
    """Return reactive-power injection in MVAr."""

    return self.q_mvar

# ============================================================
# POWER CONTROL
# ============================================================

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

# ============================================================
# OPERATING STATE
# ============================================================

@property
def is_discharging(self) -> bool:
    """Return True when the Battery injects active power."""

    return self.p_mw > 0.0

@property
def is_charging(self) -> bool:
    """Return True when the Battery absorbs active power."""

    return self.p_mw < 0.0

@property
def is_idle(self) -> bool:
    """Return True when active power is effectively zero."""

    return math.isclose(
        self.p_mw,
        0.0,
        abs_tol=1e-12,
    )

# ============================================================
# ACTIVE POWER CAPABILITY
# ============================================================

@property
def active_power_limits(
    self,
) -> tuple[float, float]:
    """
    Return active-power capability.

    Returns
    -------
    tuple[float, float]
        ``(minimum, maximum)`` in MW.
    """

    return (
        -self.p_charge_max_mw,
        self.p_discharge_max_mw,
    )

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
            "Current active power exceeds the proposed "
            "discharge limit."
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
            "Current active power exceeds the proposed "
            "charging limit."
        )

    self.p_charge_max_mw = value_mw

# ============================================================
# REACTIVE POWER CAPABILITY
# ============================================================

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

    q_min_mvar = self._validate_limit(
        q_min_mvar,
        "q_min_mvar",
    )

    q_max_mvar = self._validate_limit(
        q_max_mvar,
        "q_max_mvar",
    )

    if q_min_mvar > q_max_mvar:
        raise ValueError(
            "q_min_mvar cannot exceed q_max_mvar."
        )

    if not (
        q_min_mvar
        <= self.q_mvar
        <= q_max_mvar
    ):
        raise ValueError(
            "Current reactive power would violate the "
            "proposed reactive-power limits."
        )

    self.q_min_mvar = q_min_mvar
    self.q_max_mvar = q_max_mvar

# ============================================================
# ENERGY / STATE OF CHARGE
# ============================================================

@property
def available_energy_mwh(self) -> float:
    """Return stored energy corresponding to the current SOC."""

    return (
        self.energy_capacity_mwh
        * self.soc
    )

@property
def minimum_energy_mwh(self) -> float:
    """Return energy corresponding to the minimum SOC."""

    return (
        self.energy_capacity_mwh
        * self.soc_min
    )

@property
def maximum_energy_mwh(self) -> float:
    """Return energy corresponding to the maximum SOC."""

    return (
        self.energy_capacity_mwh
        * self.soc_max
    )

def set_soc(
    self,
    soc: float,
) -> None:
    """Set the Battery state of charge."""

    soc = self._validate_soc(
        soc,
        "soc",
    )

    if not self.soc_min <= soc <= self.soc_max:
        raise ValueError(
            "soc must remain within the configured "
            "soc_min and soc_max limits."
        )

    self.soc = soc

def set_soc_limits(
    self,
    soc_min: float,
    soc_max: float,
) -> None:
    """Set permissible Battery SOC limits."""

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
            "soc_min cannot exceed soc_max."
        )

    if not soc_min <= self.soc <= soc_max:
        raise ValueError(
            "Current SOC is outside the proposed SOC limits."
        )

    self.soc_min = soc_min
    self.soc_max = soc_max

# ============================================================
# ELECTRICAL RATINGS
# ============================================================

def set_nominal_voltage(
    self,
    nominal_voltage_kv: float | None,
) -> None:
    """Set or clear the nominal AC voltage."""

    self.nominal_voltage_kv = (
        self._validate_optional_positive(
            nominal_voltage_kv,
            "nominal_voltage_kv",
        )
    )

def set_frequency(
    self,
    frequency_hz: float,
) -> None:
    """Set the nominal system frequency."""

    self.frequency_hz = self._validate_positive(
        frequency_hz,
        "frequency_hz",
    )

# ============================================================
# VALIDATION
# ============================================================

def validate_parameters(self) -> bool:
    """Validate Battery-local engineering parameters."""

    super().validate_parameters()

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

    self.q_min_mvar = self._validate_limit(
        self.q_min_mvar,
        "q_min_mvar",
    )

    self.q_max_mvar = self._validate_limit(
        self.q_max_mvar,
        "q_max_mvar",
    )

    if self.q_min_mvar > self.q_max_mvar:
        raise ValueError(
            "q_min_mvar cannot exceed q_max_mvar."
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
            "soc_min cannot exceed soc_max."
        )

    self.soc = self._validate_soc(
        self.soc,
        "soc",
    )

    if not (
        self.soc_min
        <= self.soc
        <= self.soc_max
    ):
        raise ValueError(
            "soc must remain within the configured "
            "soc_min and soc_max limits."
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

    self.p_mw = self._validate_finite(
        self.p_mw,
        "p_mw",
    )

    self.q_mvar = self._validate_finite(
        self.q_mvar,
        "q_mvar",
    )

    self._validate_active_power(
        self.p_mw,
    )

    self._validate_reactive_power(
        self.q_mvar,
    )

    self.terminal.validate()

    return True

# ============================================================
# DIAGNOSTICS
# ============================================================

def summary(self) -> dict[str, Any]:
    """Return structured Battery diagnostic information."""

    data = super().summary()

    data.update(
        {
            "endpoint": (
                self.terminal.endpoint_id
            ),
            "connected": self.is_connected,
            "in_service": self.in_service,
            "p_mw": self.p_mw,
            "q_mvar": self.q_mvar,
            "p_discharge_max_mw": (
                self.p_discharge_max_mw
            ),
            "p_charge_max_mw": (
                self.p_charge_max_mw
            ),
            "q_min_mvar": self.q_min_mvar,
            "q_max_mvar": self.q_max_mvar,
            "energy_capacity_mwh": (
                self.energy_capacity_mwh
            ),
            "soc": self.soc,
            "soc_min": self.soc_min,
            "soc_max": self.soc_max,
            "available_energy_mwh": (
                self.available_energy_mwh
            ),
            "nominal_voltage_kv": (
                self.nominal_voltage_kv
            ),
            "frequency_hz": self.frequency_hz,
        }
    )

    return data

# ============================================================
# REPRESENTATION
# ============================================================

def __repr__(self) -> str:
    """Return a concise developer-facing representation."""

    return (
        f"<Battery "
        f"id={self.id} "
        f"P={self.p_mw}MW "
        f"Q={self.q_mvar}MVAr "
        f"SOC={self.soc}>"
    )

# ============================================================
# INTERNAL HELPERS
# ============================================================

@staticmethod
def _resolve_endpoint(
    *,
    endpoint: Any,
    bus: Any,
) -> Any:
    """
    Resolve ``endpoint`` and compatibility ``bus`` arguments.
    """

    if (
        endpoint is not None
        and bus is not None
        and endpoint is not bus
    ):
        raise ValueError(
            "endpoint and bus refer to different objects."
        )

    return (
        endpoint
        if endpoint is not None
        else bus
    )

def _validate_active_power(
    self,
    p_mw: float,
) -> None:
    """Validate active power against Battery capability."""

    if p_mw > self.p_discharge_max_mw:
        raise ValueError(
            "Active power exceeds the maximum "
            "discharge capability."
        )

    if p_mw < -self.p_charge_max_mw:
        raise ValueError(
            "Active power exceeds the maximum "
            "charging capability."
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
            "Reactive power is outside the configured "
            "capability limits."
        )

@staticmethod
def _validate_finite(
    value: float,
    name: str,
) -> float:
    """Validate and return a finite numeric value."""

    try:
        value = float(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise TypeError(
            f"{name} must be numeric."
        ) from exc

    if not math.isfinite(value):
        raise ValueError(
            f"{name} must be finite."
        )

    return value

@classmethod
def _validate_limit(
    cls,
    value: float,
    name: str,
) -> float:
    """
    Validate a numeric capability limit.

    Infinite values are allowed for open-ended capability limits.
    """

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise TypeError(
            f"{name} must be numeric."
        ) from exc

@classmethod
def _validate_non_negative(
    cls,
    value: float,
    name: str,
) -> float:
    """Validate a finite non-negative value."""

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
    """Validate a finite positive value."""

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
    """Validate SOC in the inclusive range 0.0 to 1.0."""

    value = cls._validate_finite(
        value,
        name,
    )

    if not 0.0 <= value <= 1.0:
        raise ValueError(
            f"{name} must be between 0.0 and 1.0."
        )

    return value
```

__all__ = [
"Battery",
]
