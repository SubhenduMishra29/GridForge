# ============================================================

# File: core/model/transformer.py

#

# GridForge V2 — Transformer Model

#

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Transformer Model
==============================

A Transformer is a specialized two-terminal Branch representing
a static physical transformer.

## Architecture

```
ElectricalObject
      |
      v
    Branch
      |
      v
  Transformer
```

## Ownership

ElectricalObject owns:

```
- stable identity;
- human-readable name;
- base validation contract.
```

Branch owns:

```
- authoritative terminals;
- endpoint connectivity;
- generic branch electrical parameters;
- r;
- x;
- b;
- rate_mva;
- in_service.
```

Transformer owns only transformer-specific configuration:

```
- tap;
- shift.
```

Transformer does NOT own:

```
- Bus objects;
- external Terminal objects;
- Network topology;
- Network collections;
- endpoint resolution;
- study formulation;
- solved numerical state;
- Y-bus construction;
- solver indices;
- OLTC control logic;
- protection logic;
- dynamic simulation;
- GUI state;
- SLD geometry;
- persistence.
```

## Terminal Boundary

Transformer inherits its authoritative terminal interface from
Branch. It does not adopt externally supplied Terminal instances.

Topology remains terminal-centric. Network is responsible for
authoritative topology and endpoint interpretation.

## Electrical Boundary

The generic branch electrical parameters:

```
r
x
b
```

remain owned and validated by Branch.

Transformer exposes these parameters in its constructor only
because they are required to initialize the inherited Branch
state. Transformer does not duplicate their storage.

Transformer-specific electrical configuration is:

```
tap
shift
```

Automatic tap-changing, voltage regulation, and OLTC behavior
belong outside this physical model.

## Validation Boundary

The public validation entry point remains inherited from
ElectricalObject.

The validation chain is:

```
ElectricalObject.validate()
        |
        v
Transformer.validate_parameters()
        |
        v
Branch.validate_parameters()
        |
        v
ElectricalObject.validate_parameters()
```

The constructor does not invoke validate() or
validate_parameters().

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from **future** import annotations

import math
from typing import Any

from .branch import Branch

class Transformer(Branch):
"""
Static two-terminal transformer.

```
Branch owns terminals, endpoint connectivity, r/x/b, rating,
and operational state.

Transformer owns only tap ratio and phase shift.
"""

TYPE = "TRANSFORMER"

def __init__(
    self,
    id: str,
    endpoint_from: Any = None,
    endpoint_to: Any = None,
    *,
    r: float | None = None,
    x: float | None = None,
    b: float | None = None,
    tap: float = 1.0,
    shift: float = 0.0,
    name: str = "",
    rate_mva: float | None = None,
    in_service: bool = True,
) -> None:
    """
    Construct a static two-terminal Transformer.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    endpoint_from:
        Optional initial endpoint reference for the
        inherited from terminal.

    endpoint_to:
        Optional initial endpoint reference for the
        inherited to terminal.

    r:
        Branch-owned series resistance.

    x:
        Branch-owned series reactance.

    b:
        Branch-owned shunt susceptance.

    tap:
        Transformer-owned static magnitude tap ratio.

    shift:
        Transformer-owned static phase shift in radians.

    name:
        Human-readable transformer name.

    rate_mva:
        Branch-owned optional equipment rating.

    in_service:
        Branch-owned operational state.
    """

    super().__init__(
        id=id,
        endpoint_from=endpoint_from,
        endpoint_to=endpoint_to,
        r=r,
        x=x,
        b=b,
        name=name,
        rate_mva=rate_mva,
        in_service=in_service,
    )

    self._tap = self._validate_positive(
        tap,
        "tap",
    )

    self._shift = self._validate_finite(
        shift,
        "shift",
    )

# ============================================================
# IDENTITY
# ============================================================

@property
def element_type(self) -> str:
    """Return the canonical GridForge element type."""
    return self.TYPE

# ============================================================
# TAP RATIO
# ============================================================

@property
def tap(self) -> float:
    """Return the static magnitude tap ratio."""
    return self._tap

@tap.setter
def tap(
    self,
    value: float,
) -> None:
    self._tap = self._validate_positive(
        value,
        "tap",
    )

@property
def tap_ratio(self) -> float:
    """Alias for the static magnitude tap ratio."""
    return self._tap

@tap_ratio.setter
def tap_ratio(
    self,
    value: float,
) -> None:
    self._tap = self._validate_positive(
        value,
        "tap_ratio",
    )

@property
def turns_ratio(self) -> float:
    """Return the configured static transformer ratio."""
    return self._tap

def set_tap(
    self,
    tap: float,
) -> None:
    """Set the static transformer tap ratio."""
    self.tap = tap

# ============================================================
# PHASE SHIFT
# ============================================================

@property
def shift(self) -> float:
    """Return static phase shift in radians."""
    return self._shift

@shift.setter
def shift(
    self,
    value: float,
) -> None:
    self._shift = self._validate_finite(
        value,
        "shift",
    )

@property
def phase_shift_rad(self) -> float:
    """Return static phase shift in radians."""
    return self._shift

@phase_shift_rad.setter
def phase_shift_rad(
    self,
    value: float,
) -> None:
    self._shift = self._validate_finite(
        value,
        "phase_shift_rad",
    )

@property
def phase_shift_deg(self) -> float:
    """Return static phase shift in degrees."""
    return math.degrees(
        self._shift
    )

@phase_shift_deg.setter
def phase_shift_deg(
    self,
    value: float,
) -> None:
    value = self._validate_finite(
        value,
        "phase_shift_deg",
    )

    self._shift = math.radians(
        value
    )

def set_phase_shift(
    self,
    shift: float,
) -> None:
    """Set static phase shift in radians."""
    self.shift = shift

def set_phase_shift_degrees(
    self,
    degrees: float,
) -> None:
    """Set static phase shift in degrees."""
    self.phase_shift_deg = degrees

# ============================================================
# VALIDATION
# ============================================================

def validate_parameters(self) -> bool:
    """
    Validate Transformer-specific and inherited parameters.

    Validation order:

        Transformer
            ↓
        Branch
            ↓
        ElectricalObject
    """

    Branch.validate_parameters(self)

    self._tap = self._validate_positive(
        self._tap,
        "tap",
    )

    self._shift = self._validate_finite(
        self._shift,
        "shift",
    )

    return True

# ============================================================
# DIAGNOSTICS
# ============================================================

def summary(self) -> dict[str, Any]:
    """
    Return structured Transformer diagnostics.

    Generic branch state remains supplied by Branch.
    Transformer adds only its own parameters.
    """

    summary = super().summary()

    summary.update(
        {
            "type": self.TYPE,
            "tap": self._tap,
            "tap_ratio": self._tap,
            "shift_rad": self._shift,
            "shift_deg": self.phase_shift_deg,
        }
    )

    return summary

# ============================================================
# REPRESENTATION
# ============================================================

def __repr__(self) -> str:
    """Return a concise developer-facing representation."""

    from_endpoint = self.from_endpoint
    to_endpoint = self.to_endpoint

    from_id = getattr(
        from_endpoint,
        "id",
        None,
    )

    to_id = getattr(
        to_endpoint,
        "id",
        None,
    )

    return (
        f"<Transformer "
        f"id={self.id}, "
        f"{from_id} -> {to_id}, "
        f"tap={self._tap:.6f}, "
        f"shift={self._shift:.6f} rad>"
    )

# ============================================================
# VALIDATION HELPERS
# ============================================================

@staticmethod
def _validate_finite(
    value: float,
    name: str,
) -> float:
    """Validate a finite numeric value."""

    try:
        value = float(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            f"{name} must be numeric."
        ) from exc

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
    """Validate a finite positive numeric value."""

    value = Transformer._validate_finite(
        value,
        name,
    )

    if value <= 0.0:
        raise ValueError(
            f"{name} must be greater than zero."
        )

    return value

__all__ = [
"Transformer",
]
