# ============================================================

# File: core/model/branch.py

# GridForge V2 — Branch Model

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Branch Model.

Generic two-terminal electrical branch foundation.

## Architecture

A Branch owns exactly two physical terminals:

```
Branch
  |
  +-- from_terminal
  |       |
  |       +-- endpoint
  |
  +-- to_terminal
          |
          +-- endpoint
```

Terminal ownership is established by the Branch and is not transferred.

The Branch owns:

```
- its two terminals;
- branch-local engineering parameters;
- branch-local operational state;
- branch-local validation;
- optional engineering extensions.
```

The Branch does not own:

```
- global network topology;
- Bus collections;
- terminal ownership belonging to another object;
- Y-bus construction;
- numerical indexing;
- load-flow solving;
- short-circuit solving;
- protection calculations;
- dynamic simulation;
- SLD geometry;
- GUI state.
```

## Endpoint contract

Each Branch terminal stores one local endpoint reference.

The canonical relationship is:

```
Branch Terminal -> endpoint -> Bus-like endpoint
```

The Branch does not adopt another object's Terminal as one of its own
physical terminals.

Terminal-to-Terminal chaining is not part of the Branch contract.

Network-level interpretation of terminal endpoints belongs to
`core.network.endpoint`.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import math
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal

# ============================================================

# BRANCH

# ============================================================

class Branch(ElectricalObject):
"""
Generic two-terminal electrical branch.

```
Specialized equipment such as Line, Cable, Transformer and
Breaker may inherit this common terminal and operational contract.
"""

TYPE = "BRANCH"

def __init__(
    self,
    id: str,
    endpoint_from: Any = None,
    endpoint_to: Any = None,
    *,
    r: float | None = None,
    x: float | None = None,
    b: float | None = None,
    name: str = "",
    rate_mva: float | None = None,
    tap: float = 1.0,
    shift: float = 0.0,
    in_service: bool = True,
) -> None:

    super().__init__(
        id=id,
        name=name,
    )

    # =============================================================
    # PHYSICAL TERMINALS
    # =============================================================

    self.from_terminal = self._create_terminal(
        endpoint=endpoint_from,
        role="from",
    )

    self.to_terminal = self._create_terminal(
        endpoint=endpoint_to,
        role="to",
    )

    # =============================================================
    # GENERIC ELECTRICAL PARAMETERS
    # =============================================================

    self.r = self._validate_optional_finite(
        r,
        "r",
    )

    self.x = self._validate_optional_finite(
        x,
        "x",
    )

    self.b = self._validate_optional_finite(
        b,
        "b",
    )

    # =============================================================
    # TRANSFORMER-COMPATIBLE PARAMETERS
    # =============================================================

    self.tap = self._validate_positive(
        tap,
        "tap",
    )

    self.shift = self._validate_finite(
        shift,
        "shift",
    )

    # =============================================================
    # RATING
    # =============================================================

    if rate_mva is None:
        self.rate_mva = None
    else:
        self.rate_mva = self._validate_positive(
            rate_mva,
            "rate_mva",
        )

    # =============================================================
    # OPERATIONAL STATE
    # =============================================================

    self.in_service = bool(
        in_service
    )

    # =============================================================
    # EXTENSIONS
    # =============================================================

    self._extensions: dict[str, Any] = {}

    self.validate_parameters()

# ================================================================
# IDENTITY
# ================================================================

@property
def element_type(self) -> str:
    """Return the canonical GridForge element type."""

    return self.TYPE

# ================================================================
# TERMINAL CREATION
# ================================================================

def _create_terminal(
    self,
    endpoint: Any = None,
    *,
    role: str,
) -> Terminal:
    """
    Create a Branch-owned Terminal.

    A Branch always creates its own Terminal.

    Existing Terminal instances cannot be supplied as endpoints.
    This prevents:

        - ownership transfer;
        - ownership reassignment;
        - accidental sharing of a physical terminal;
        - Terminal-to-Terminal endpoint chaining.

    Parameters
    ----------
    endpoint:
        Optional Bus-like local endpoint.

    role:
        Required role of the newly created terminal.

    Returns
    -------
    Terminal
        A new Terminal owned by this Branch.

    Raises
    ------
    TypeError
        If an existing Terminal is supplied as an endpoint.
    """

    if isinstance(
        endpoint,
        Terminal,
    ):
        raise TypeError(
            f"Branch '{self.id}' endpoint '{role}' "
            "cannot be a Terminal. Branch terminals are "
            "owned exclusively by the Branch."
        )

    return Terminal(
        endpoint=endpoint,
        owner=self,
        role=role,
    )

# ================================================================
# TERMINALS
# ================================================================

@property
def terminals(
    self,
) -> tuple[Terminal, Terminal]:
    """Return the authoritative Branch terminals."""

    return (
        self.from_terminal,
        self.to_terminal,
    )

# ================================================================
# ENDPOINTS
# ================================================================

@property
def from_endpoint(self) -> Any:
    """Return the from-side local endpoint."""

    return self.from_terminal.endpoint

@property
def to_endpoint(self) -> Any:
    """Return the to-side local endpoint."""

    return self.to_terminal.endpoint

def endpoints(
    self,
) -> tuple[Any, Any]:
    """Return the authoritative endpoint pair."""

    return (
        self.from_endpoint,
        self.to_endpoint,
    )

# ================================================================
# BUS ACCESS
# ================================================================

@property
def from_bus(self) -> Any:
    """
    Return the Bus resolved from the from-side endpoint.

    This is derived information and is not independent topology
    state.
    """

    from core.network.endpoint import resolve_terminal_bus

    if not self.from_terminal.is_connected:
        return None

    return resolve_terminal_bus(
        self.from_terminal
    )

@property
def to_bus(self) -> Any:
    """
    Return the Bus resolved from the to-side endpoint.

    This is derived information and is not independent topology
    state.
    """

    from core.network.endpoint import resolve_terminal_bus

    if not self.to_terminal.is_connected:
        return None

    return resolve_terminal_bus(
        self.to_terminal
    )

def buses(
    self,
) -> tuple[Any, Any]:
    """Return the derived endpoint Bus pair."""

    return (
        self.from_bus,
        self.to_bus,
    )

# ================================================================
# CONNECTIVITY
# ================================================================

@property
def is_connected(self) -> bool:
    """Return True when both terminals have local endpoints."""

    return (
        self.from_terminal.is_connected
        and self.to_terminal.is_connected
    )

@property
def is_fully_connected(self) -> bool:
    """Alias for ``is_connected``."""

    return self.is_connected

@property
def has_from_endpoint(self) -> bool:
    """Return whether the from-side endpoint is attached."""

    return self.from_terminal.is_connected

@property
def has_to_endpoint(self) -> bool:
    """Return whether the to-side endpoint is attached."""

    return self.to_terminal.is_connected

# ================================================================
# TERMINAL ATTACHMENT
# ================================================================

def connect_from(
    self,
    endpoint: Any,
) -> None:
    """
    Attach the from-side local endpoint.

    This does not construct or mutate global topology.
    """

    if isinstance(
        endpoint,
        Terminal,
    ):
        raise TypeError(
            "A Branch endpoint cannot be another Terminal."
        )

    self.from_terminal.attach(
        endpoint
    )

def connect_to(
    self,
    endpoint: Any,
) -> None:
    """
    Attach the to-side local endpoint.

    This does not construct or mutate global topology.
    """

    if isinstance(
        endpoint,
        Terminal,
    ):
        raise TypeError(
            "A Branch endpoint cannot be another Terminal."
        )

    self.to_terminal.attach(
        endpoint
    )

def disconnect_from(
    self,
) -> None:
    """Detach the from-side local endpoint."""

    self.from_terminal.detach()

def disconnect_to(
    self,
) -> None:
    """Detach the to-side local endpoint."""

    self.to_terminal.detach()

# ================================================================
# GENERIC ELECTRICAL PARAMETERS
# ================================================================

@property
def has_per_unit_parameters(self) -> bool:
    """Return True when both generic r and x are defined."""

    return (
        self.r is not None
        and self.x is not None
    )

@property
def impedance(self) -> complex:
    """
    Return generic series impedance.

        Z = R + jX
    """

    if (
        self.r is None
        or self.x is None
    ):
        raise ValueError(
            f"Branch '{self.id}' does not define "
            "generic per-unit series impedance."
        )

    return complex(
        self.r,
        self.x,
    )

@property
def series_impedance(self) -> complex:
    """Alias for ``impedance``."""

    return self.impedance

@property
def admittance(self) -> complex:
    """
    Return generic series admittance.

        Y = 1 / Z
    """

    z = self.impedance

    if z == 0.0 + 0.0j:
        raise ZeroDivisionError(
            f"Branch '{self.id}' has zero series impedance."
        )

    return 1.0 / z

@property
def series_admittance(self) -> complex:
    """Alias for ``admittance``."""

    return self.admittance

@property
def shunt_admittance(self) -> complex:
    """
    Return generic total shunt admittance.

        Ysh = jB
    """

    if self.b is None:
        return 0.0 + 0.0j

    return complex(
        0.0,
        self.b,
    )

# ================================================================
# PER-UNIT ACCESSORS
# ================================================================

@property
def r_pu(self) -> float | None:
    """Return generic resistance in per-unit."""

    return self.r

@property
def x_pu(self) -> float | None:
    """Return generic reactance in per-unit."""

    return self.x

@property
def b_pu(self) -> float | None:
    """Return generic shunt susceptance in per-unit."""

    return self.b

# ================================================================
# TAP / PHASE SHIFT
# ================================================================

@property
def tap_ratio(self) -> float:
    """Return magnitude tap ratio."""

    return self.tap

@property
def phase_shift(self) -> float:
    """Return phase shift in radians."""

    return self.shift

# ================================================================
# RATING
# ================================================================

@property
def has_rating(self) -> bool:
    """Return whether a thermal rating is defined."""

    return self.rate_mva is not None

def set_rating(
    self,
    rate_mva: float | None,
) -> None:
    """Set or clear the thermal rating."""

    if rate_mva is None:
        self.rate_mva = None
        return

    self.rate_mva = self._validate_positive(
        rate_mva,
        "rate_mva",
    )

# ================================================================
# OPERATIONAL STATE
# ================================================================

def connect(
    self,
) -> None:
    """
    Place the Branch in service.

    This does not attach physical terminals.
    """

    self.in_service = True

def disconnect(
    self,
) -> None:
    """
    Take the Branch out of service.

    This does not detach physical terminals.
    """

    self.in_service = False

def close(
    self,
) -> None:
    """Compatibility alias for ``connect``."""

    self.connect()

def trip(
    self,
) -> None:
    """Compatibility alias for ``disconnect``."""

    self.disconnect()

@property
def is_in_service(self) -> bool:
    """Return whether the Branch is in service."""

    return self.in_service

@property
def is_out_of_service(self) -> bool:
    """Return whether the Branch is out of service."""

    return not self.in_service

# ================================================================
# EXTENSIONS
# ================================================================

def register_extension(
    self,
    extension_id: str,
    extension: Any,
) -> None:
    """
    Register an optional engineering extension.

    Extensions are references only and do not bypass Core or
    Application contracts.
    """

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

    self._extensions[
        extension_id
    ] = extension

def get_extension(
    self,
    extension_id: str,
) -> Any | None:
    """Return a registered extension or ``None``."""

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

# ================================================================
# VALIDATION
# ================================================================

def validate_parameters(
    self,
) -> bool:
    """
    Validate Branch-local engineering parameters.

    Generic r/x/b values are optional because specialized branch
    models may use another physical parameterization.
    """

    self.r = self._validate_optional_finite(
        self.r,
        "r",
    )

    self.x = self._validate_optional_finite(
        self.x,
        "x",
    )

    self.b = self._validate_optional_finite(
        self.b,
        "b",
    )

    self.tap = self._validate_positive(
        self.tap,
        "tap",
    )

    self.shift = self._validate_finite(
        self.shift,
        "shift",
    )

    if self.rate_mva is not None:
        self.rate_mva = self._validate_positive(
            self.rate_mva,
            "rate_mva",
        )

    self.from_terminal.validate()
    self.to_terminal.validate()

    if self.from_terminal.owner is not self:
        raise ValueError(
            f"Branch '{self.id}' does not own its "
            "from_terminal."
        )

    if self.to_terminal.owner is not self:
        raise ValueError(
            f"Branch '{self.id}' does not own its "
            "to_terminal."
        )

    if self.from_terminal is self.to_terminal:
        raise ValueError(
            f"Branch '{self.id}' cannot use the same "
            "Terminal object for both ends."
        )

    return True

@staticmethod
def _validate_finite(
    value: float,
    name: str,
) -> float:
    """
    Validate a finite numeric value.
    """

    try:
        numeric_value = float(
            value
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise TypeError(
            f"{name} must be numeric."
        ) from exc

    if not math.isfinite(
        numeric_value
    ):
        raise ValueError(
            f"{name} must be finite."
        )

    return numeric_value

@classmethod
def _validate_optional_finite(
    cls,
    value: float | None,
    name: str,
) -> float | None:
    """
    Validate an optional finite numeric value.
    """

    if value is None:
        return None

    return cls._validate_finite(
        value,
        name,
    )

@classmethod
def _validate_positive(
    cls,
    value: float,
    name: str,
) -> float:
    """
    Validate a finite positive numeric value.
    """

    numeric_value = cls._validate_finite(
        value,
        name,
    )

    if numeric_value <= 0.0:
        raise ValueError(
            f"{name} must be greater than zero."
        )

    return numeric_value

# ================================================================
# REPRESENTATION
# ================================================================

def __repr__(
    self,
) -> str:
    """Return a concise developer representation."""

    return (
        f"<{self.__class__.__name__} "
        f"id={self.id!r} "
        f"from={self.from_terminal.endpoint_id!r} "
        f"to={self.to_terminal.endpoint_id!r} "
        f"in_service={self.in_service}>"
    )
```

# ============================================================

# PUBLIC API

# ============================================================

__all__ = [
"Branch",
]
