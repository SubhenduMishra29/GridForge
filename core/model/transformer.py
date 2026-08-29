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

A Transformer is a specialized two-terminal Branch.

Architecture:

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

Branch owns:

```
- authoritative terminals;
- endpoint connectivity;
- r;
- x;
- b;
- rate_mva;
- in_service.
```

Transformer adds only:

```
- tap;
- shift.
```

Transformer does not duplicate Branch-owned electrical or
connectivity state.
"""

from __future__ import annotations

import math
from typing import Any

from .branch import Branch

class Transformer(Branch):
"""
Static two-terminal transformer.

Branch owns the generic branch and connectivity state.
Transformer owns only transformer-specific configuration.
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
        Initial reference for the inherited from-side terminal.

    endpoint_to:
        Initial reference for the inherited to-side terminal.

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
        Human-readable name.

    rate_mva:
        Branch-owned optional rating.

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
    """Return the static phase shift in radians."""
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
    """Return the static phase shift in radians."""
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
    """Return the static phase shift in degrees."""
    return math.degrees(self._shift)

@phase_shift_deg.setter
def phase_shift_deg(
    self,
    value: float,
) -> None:
    value = self._validate_finite(
        value,
        "phase_shift_deg",
    )

    self._shift = math.radians(value)

def set_phase_shift(
    self,
    shift: float,
) -> None:
    """Set the static phase shift in radians."""
    self.shift = shift

def set_phase_shift_degrees(
    self,
    degrees: float,
) -> None:
    """Set the static phase shift in degrees."""
    self.phase_shift_deg = degrees

# ============================================================
# VALIDATION
# ============================================================

def validate_parameters(self) -> bool:
    """
    Validate Transformer-specific and inherited parameters.

    The inherited Branch validation is executed first.
    Transformer then validates its own tap and phase-shift state.
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

    Inherited state comes from Branch.
    Transformer adds only transformer-specific state.
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
    except (TypeError, ValueError) as exc:
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
