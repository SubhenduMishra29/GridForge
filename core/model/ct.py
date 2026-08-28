# ============================================================

# File: core/model/ct.py

# GridForge V2 — Model Layer

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Current Transformer Model
======================================

Defines the static electrical/instrumentation model of a Current
Transformer (CT).

The CT owns:

```
- stable identity;
- four physical interfaces;
- primary and secondary ratings;
- transformation ratio;
- accuracy class;
- burden;
- polarity;
- nominal frequency;
- service state.
```

The CT does NOT own:

```
- global network topology;
- measurement channels;
- relay inputs;
- relay logic;
- protection calculations;
- CT saturation simulation;
- transient simulation;
- Y-bus construction;
- load-flow calculations;
- short-circuit calculations;
- breaker operation;
- SLD state;
- GUI state.
```

## Terminal architecture

```
Primary:
    P1
    P2

Secondary:
    S1
    S2
```

All four interfaces are represented by GridForge Terminal objects.

The Network layer owns global topology. The CT only owns its local
terminal interfaces and their endpoint references.

Dynamic CT behaviour belongs to the appropriate simulation/protection
layer and must not be embedded in this static model.
"""

from __future__ import annotations

from enum import Enum
from math import isfinite
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal

class CTPolarity(Enum):
"""Current-transformer primary polarity convention."""

```
P1_P2 = "P1-P2"
P2_P1 = "P2-P1"
```

class CurrentTransformer(ElectricalObject):
"""
Static GridForge V2 Current Transformer model.

```
A CT exposes two primary and two secondary interfaces. It contains
static engineering/nameplate data only.
"""

TYPE = "CT"

def __init__(
    self,
    id: str,
    name: str = "",
    *,
    rated_primary_current: float = 1.0,
    rated_secondary_current: float = 1.0,
    accuracy_class: str = "",
    rated_burden_va: float = 0.0,
    polarity: CTPolarity = CTPolarity.P1_P2,
    frequency_hz: float = 50.0,
    in_service: bool = True,
) -> None:
    super().__init__(
        id=id,
        name=name,
    )

    self.rated_primary_current = self._validate_positive(
        rated_primary_current,
        "rated_primary_current",
    )

    self.rated_secondary_current = self._validate_positive(
        rated_secondary_current,
        "rated_secondary_current",
    )

    if not isinstance(accuracy_class, str):
        raise TypeError(
            "accuracy_class must be a string."
        )

    if not isinstance(polarity, CTPolarity):
        raise TypeError(
            "polarity must be a CTPolarity value."
        )

    self.accuracy_class = accuracy_class.strip()

    self.rated_burden_va = self._validate_non_negative(
        rated_burden_va,
        "rated_burden_va",
    )

    self.polarity = polarity

    self.frequency_hz = self._validate_positive(
        frequency_hz,
        "frequency_hz",
    )

    self.in_service = bool(in_service)

    self.primary_p1_terminal = Terminal(
        owner=self,
        role="P1",
    )

    self.primary_p2_terminal = Terminal(
        owner=self,
        role="P2",
    )

    self.secondary_s1_terminal = Terminal(
        owner=self,
        role="S1",
    )

    self.secondary_s2_terminal = Terminal(
        owner=self,
        role="S2",
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
# TERMINALS
# ============================================================

@property
def primary_terminals(self) -> tuple[Terminal, Terminal]:
    """Return the ordered P1 and P2 primary terminals."""

    return (
        self.primary_p1_terminal,
        self.primary_p2_terminal,
    )

@property
def secondary_terminals(self) -> tuple[Terminal, Terminal]:
    """Return the ordered S1 and S2 secondary terminals."""

    return (
        self.secondary_s1_terminal,
        self.secondary_s2_terminal,
    )

@property
def terminals(self) -> tuple[Terminal, ...]:
    """
    Return all CT terminals in deterministic order.

    Order:

        P1, P2, S1, S2
    """

    return (
        self.primary_p1_terminal,
        self.primary_p2_terminal,
        self.secondary_s1_terminal,
        self.secondary_s2_terminal,
    )

@property
def primary_p1(self) -> Terminal:
    """Return the P1 primary terminal."""

    return self.primary_p1_terminal

@property
def primary_p2(self) -> Terminal:
    """Return the P2 primary terminal."""

    return self.primary_p2_terminal

@property
def secondary_s1(self) -> Terminal:
    """Return the S1 secondary terminal."""

    return self.secondary_s1_terminal

@property
def secondary_s2(self) -> Terminal:
    """Return the S2 secondary terminal."""

    return self.secondary_s2_terminal

# ============================================================
# CONNECTIVITY
# ============================================================

@property
def primary_connected(self) -> bool:
    """Return whether both primary terminals are connected."""

    return (
        self.primary_p1_terminal.is_connected
        and self.primary_p2_terminal.is_connected
    )

@property
def secondary_connected(self) -> bool:
    """Return whether both secondary terminals are connected."""

    return (
        self.secondary_s1_terminal.is_connected
        and self.secondary_s2_terminal.is_connected
    )

# ============================================================
# TRANSFORMATION RATIO
# ============================================================

@property
def ratio(self) -> float:
    """
    Return the nominal current transformation ratio.

    Defined as:

        primary rated current / secondary rated current

    Example:

        400 / 5 = 80
    """

    return (
        self.rated_primary_current
        / self.rated_secondary_current
    )

@property
def transformation_ratio(self) -> float:
    """Return the nominal transformation ratio."""

    return self.ratio

# ============================================================
# SERVICE STATE
# ============================================================

def set_in_service(
    self,
    in_service: bool,
) -> None:
    """
    Set the local CT service state.

    This does not alter topology or measurement/protection state.
    """

    self.in_service = bool(in_service)

def connect(self) -> None:
    """Place the CT in service."""

    self.in_service = True

def disconnect(self) -> None:
    """Take the CT out of service."""

    self.in_service = False

# ============================================================
# VALIDATION
# ============================================================

def validate_parameters(self) -> bool:
    """
    Validate CT-local engineering parameters.

    Global topology and downstream measurement/protection
    configuration are deliberately outside this validation.
    """

    super().validate_parameters()

    self.rated_primary_current = self._validate_positive(
        self.rated_primary_current,
        "rated_primary_current",
    )

    self.rated_secondary_current = self._validate_positive(
        self.rated_secondary_current,
        "rated_secondary_current",
    )

    self.rated_burden_va = self._validate_non_negative(
        self.rated_burden_va,
        "rated_burden_va",
    )

    self.frequency_hz = self._validate_positive(
        self.frequency_hz,
        "frequency_hz",
    )

    if not isinstance(self.accuracy_class, str):
        raise TypeError(
            "accuracy_class must be a string."
        )

    if not isinstance(self.polarity, CTPolarity):
        raise TypeError(
            "polarity must be a CTPolarity value."
        )

    for terminal in self.terminals:
        terminal.validate()

    return True

def validate(self) -> bool:
    """Public CT validation entry point."""

    return self.validate_parameters()

# ============================================================
# DIAGNOSTICS
# ============================================================

def summary(self) -> dict[str, Any]:
    """Return static CT engineering and connectivity information."""

    data = super().summary()

    data.update(
        {
            "type": self.TYPE,
            "in_service": self.in_service,
            "rated_primary_current": (
                self.rated_primary_current
            ),
            "rated_secondary_current": (
                self.rated_secondary_current
            ),
            "ratio": self.ratio,
            "accuracy_class": self.accuracy_class,
            "rated_burden_va": self.rated_burden_va,
            "polarity": self.polarity.value,
            "frequency_hz": self.frequency_hz,
            "primary_connected": self.primary_connected,
            "secondary_connected": self.secondary_connected,
            "primary_p1_endpoint": self._endpoint_id(
                self.primary_p1_terminal
            ),
            "primary_p2_endpoint": self._endpoint_id(
                self.primary_p2_terminal
            ),
            "secondary_s1_endpoint": self._endpoint_id(
                self.secondary_s1_terminal
            ),
            "secondary_s2_endpoint": self._endpoint_id(
                self.secondary_s2_terminal
            ),
        }
    )

    return data

# ============================================================
# REPRESENTATION
# ============================================================

def __repr__(self) -> str:
    """Return a concise developer-facing representation."""

    return (
        f"<CurrentTransformer "
        f"id={self.id}, "
        f"ratio="
        f"{self.rated_primary_current:.3f}/"
        f"{self.rated_secondary_current:.3f}, "
        f"accuracy={self.accuracy_class!r}, "
        f"in_service={self.in_service}>"
    )

# ============================================================
# INTERNAL VALIDATION HELPERS
# ============================================================

@staticmethod
def _validate_positive(
    value: float,
    field_name: str,
) -> float:
    """Validate a finite positive numeric quantity."""

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
    """Validate a finite non-negative numeric quantity."""

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
    """Return the endpoint identifier, if one exists."""

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
```

# Compatibility alias retained for existing imports.

CT = CurrentTransformer

__all__ = [
"CTPolarity",
"CurrentTransformer",
"CT",
]
