# ============================================================

# File: core/model/breaker.py

#

# GridForge V2 — Breaker Model

#

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Breaker Model
==========================

A Breaker is a two-terminal switching device.

## Architecture

```
ElectricalObject
       |
       v
    Breaker
```

Breaker is intentionally NOT a Branch.

Branch represents generic electrical branch parameters such as
r/x/b. A Breaker instead represents a switching/topological
element whose electrical state is governed by its switching
condition.

## Ownership

Breaker owns:

```
- its two local terminals;
- closed/open state;
- in_service state;
- failed state;
- breaker-specific ratings;
- breaker-specific timing/configuration.
```

Breaker does NOT own:

```
- Network topology;
- Network collections;
- global endpoint resolution;
- Y-bus construction;
- solver indices;
- study formulation;
- protection logic;
- control logic;
- GUI state;
- SLD geometry;
- persistence.
```

## Terminal Boundary

The Breaker owns its local Terminal objects.

Terminal objects represent connection points only.

Network remains responsible for interpreting those terminals as
part of authoritative project topology.

## Validation Boundary

The public validation entry point is inherited from
ElectricalObject.

Breaker overrides validate_parameters() only for
Breaker-specific validation and calls the base validation
contract.

Construction does NOT invoke validation.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any

from .base import ElectricalObject
from .terminal import Terminal

class Breaker(ElectricalObject):
"""
Two-terminal switching device.

```
Breaker is a topology/switching element rather than a generic
Branch. It owns two local terminals and its switching state.
"""

TYPE = "BREAKER"

def __init__(
    self,
    id: str,
    endpoint_from: Any = None,
    endpoint_to: Any = None,
    *,
    name: str = "",
    in_service: bool = True,
    closed: bool = True,
    failed: bool = False,
    voltage_kv: float | None = None,
    current_a: float | None = None,
    interrupting_ka: float | None = None,
) -> None:
    """
    Construct a two-terminal Breaker.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    endpoint_from:
        Optional initial reference associated with the
        from-side terminal.

    endpoint_to:
        Optional initial reference associated with the
        to-side terminal.

    name:
        Human-readable breaker name.

    in_service:
        Whether the breaker is operationally in service.

    closed:
        Initial switching state.

    failed:
        Whether the breaker is failed.

    voltage_kv:
        Optional breaker voltage rating.

    current_a:
        Optional continuous-current rating.

    interrupting_ka:
        Optional interrupting-current rating.

    Notes
    -----
    Validation is intentionally deferred.

    The constructor creates the model state but does not call
    validate() or validate_parameters().
    """

    super().__init__(
        id=id,
        name=name,
    )

    self._terminal_from = Terminal(
        owner=self,
        name="from",
    )

    self._terminal_to = Terminal(
        owner=self,
        name="to",
    )

    self._endpoint_from = endpoint_from
    self._endpoint_to = endpoint_to

    self._in_service = bool(in_service)
    self._closed = bool(closed)
    self._failed = bool(failed)

    self._voltage_kv = self._normalize_optional_positive(
        voltage_kv,
        "voltage_kv",
    )

    self._current_a = self._normalize_optional_positive(
        current_a,
        "current_a",
    )

    self._interrupting_ka = self._normalize_optional_positive(
        interrupting_ka,
        "interrupting_ka",
    )

# ============================================================
# TYPE
# ============================================================

@property
def element_type(self) -> str:
    """Return the canonical GridForge model type."""
    return self.TYPE

# ============================================================
# TERMINALS
# ============================================================

@property
def terminal_from(self) -> Terminal:
    """Return the authoritative from-side terminal."""
    return self._terminal_from

@property
def terminal_to(self) -> Terminal:
    """Return the authoritative to-side terminal."""
    return self._terminal_to

@property
def terminals(self) -> tuple[Terminal, Terminal]:
    """Return the authoritative breaker terminals."""
    return (
        self._terminal_from,
        self._terminal_to,
    )

@property
def from_terminal(self) -> Terminal:
    """Compatibility alias for the from-side terminal."""
    return self._terminal_from

@property
def to_terminal(self) -> Terminal:
    """Compatibility alias for the to-side terminal."""
    return self._terminal_to

# ============================================================
# ENDPOINTS
# ============================================================

@property
def endpoint_from(self) -> Any:
    """Return the from-side endpoint reference."""
    return self._endpoint_from

@endpoint_from.setter
def endpoint_from(
    self,
    value: Any,
) -> None:
    self._endpoint_from = value

@property
def endpoint_to(self) -> Any:
    """Return the to-side endpoint reference."""
    return self._endpoint_to

@endpoint_to.setter
def endpoint_to(
    self,
    value: Any,
) -> None:
    self._endpoint_to = value

@property
def from_endpoint(self) -> Any:
    """Compatibility alias for endpoint_from."""
    return self._endpoint_from

@from_endpoint.setter
def from_endpoint(
    self,
    value: Any,
) -> None:
    self._endpoint_from = value

@property
def to_endpoint(self) -> Any:
    """Compatibility alias for endpoint_to."""
    return self._endpoint_to

@to_endpoint.setter
def to_endpoint(
    self,
    value: Any,
) -> None:
    self._endpoint_to = value

@property
def from_bus(self) -> Any:
    """
    Compatibility accessor for the from-side endpoint.

    Network remains responsible for interpreting the endpoint.
    """
    return self._endpoint_from

@from_bus.setter
def from_bus(
    self,
    value: Any,
) -> None:
    self._endpoint_from = value

@property
def to_bus(self) -> Any:
    """
    Compatibility accessor for the to-side endpoint.

    Network remains responsible for interpreting the endpoint.
    """
    return self._endpoint_to

@to_bus.setter
def to_bus(
    self,
    value: Any,
) -> None:
    self._endpoint_to = value

# ============================================================
# OPERATIONAL STATE
# ============================================================

@property
def in_service(self) -> bool:
    """Return whether the breaker is in service."""
    return self._in_service

@in_service.setter
def in_service(
    self,
    value: bool,
) -> None:
    self._in_service = bool(value)

@property
def closed(self) -> bool:
    """Return True when the breaker is closed."""
    return self._closed

@closed.setter
def closed(
    self,
    value: bool,
) -> None:
    self._closed = bool(value)

@property
def is_closed(self) -> bool:
    """Return whether the breaker is closed."""
    return self._closed

@property
def is_open(self) -> bool:
    """Return whether the breaker is open."""
    return not self._closed

@property
def failed(self) -> bool:
    """Return whether the breaker is failed."""
    return self._failed

@failed.setter
def failed(
    self,
    value: bool,
) -> None:
    self._failed = bool(value)

# ============================================================
# RATINGS
# ============================================================

@property
def voltage_kv(self) -> float | None:
    """Return the optional voltage rating in kV."""
    return self._voltage_kv

@voltage_kv.setter
def voltage_kv(
    self,
    value: float | None,
) -> None:
    self._voltage_kv = self._normalize_optional_positive(
        value,
        "voltage_kv",
    )

@property
def current_a(self) -> float | None:
    """Return the optional continuous-current rating."""
    return self._current_a

@current_a.setter
def current_a(
    self,
    value: float | None,
) -> None:
    self._current_a = self._normalize_optional_positive(
        value,
        "current_a",
    )

@property
def interrupting_ka(self) -> float | None:
    """Return the optional interrupting-current rating."""
    return self._interrupting_ka

@interrupting_ka.setter
def interrupting_ka(
    self,
    value: float | None,
) -> None:
    self._interrupting_ka = self._normalize_optional_positive(
        value,
        "interrupting_ka",
    )

# ============================================================
# SWITCHING OPERATIONS
# ============================================================

def open(self) -> None:
    """
    Open the breaker.

    This changes only local breaker state.
    Network topology interpretation remains outside the model.
    """
    self._closed = False

def close(self) -> None:
    """
    Close the breaker.

    This changes only local breaker state.
    Network topology interpretation remains outside the model.
    """
    self._closed = True

def trip(self) -> None:
    """
    Trip the breaker open.

    Protection logic is external to this model. This method
    only represents the resulting local switching state.
    """
    self._closed = False

# ============================================================
# TERMINAL CONNECTION
# ============================================================

def connect_from(
    self,
    endpoint: Any,
) -> None:
    """
    Assign the from-side endpoint reference.

    This does not modify Network topology.
    """
    self._endpoint_from = endpoint

def connect_to(
    self,
    endpoint: Any,
) -> None:
    """
    Assign the to-side endpoint reference.

    This does not modify Network topology.
    """
    self._endpoint_to = endpoint

def disconnect_from(self) -> None:
    """Clear the from-side endpoint reference."""
    self._endpoint_from = None

def disconnect_to(self) -> None:
    """Clear the to-side endpoint reference."""
    self._endpoint_to = None

# ============================================================
# VALIDATION
# ============================================================

def validate_parameters(self) -> bool:
    """
    Validate Breaker-specific parameters.

    The base ElectricalObject validation is executed first.
    """

    super().validate_parameters()

    if not isinstance(self._in_service, bool):
        raise TypeError(
            "in_service must be a boolean."
        )

    if not isinstance(self._closed, bool):
        raise TypeError(
            "closed must be a boolean."
        )

    if not isinstance(self._failed, bool):
        raise TypeError(
            "failed must be a boolean."
        )

    self._voltage_kv = self._normalize_optional_positive(
        self._voltage_kv,
        "voltage_kv",
    )

    self._current_a = self._normalize_optional_positive(
        self._current_a,
        "current_a",
    )

    self._interrupting_ka = self._normalize_optional_positive(
        self._interrupting_ka,
        "interrupting_ka",
    )

    return True

# ============================================================
# DIAGNOSTICS
# ============================================================

def summary(self) -> dict[str, Any]:
    """
    Return structured Breaker diagnostics.
    """

    summary = super().summary()

    summary.update(
        {
            "type": self.TYPE,
            "closed": self._closed,
            "in_service": self._in_service,
            "failed": self._failed,
            "voltage_kv": self._voltage_kv,
            "current_a": self._current_a,
            "interrupting_ka": self._interrupting_ka,
            "endpoint_from": self._endpoint_identifier(
                self._endpoint_from
            ),
            "endpoint_to": self._endpoint_identifier(
                self._endpoint_to
            ),
        }
    )

    return summary

# ============================================================
# REPRESENTATION
# ============================================================

def __repr__(self) -> str:
    """Return a concise developer-facing representation."""

    from_id = self._endpoint_identifier(
        self._endpoint_from
    )

    to_id = self._endpoint_identifier(
        self._endpoint_to
    )

    state = (
        "closed"
        if self._closed
        else "open"
    )

    return (
        f"<Breaker "
        f"id={self.id}, "
        f"{from_id} -> {to_id}, "
        f"state={state}>"
    )

# ============================================================
# INTERNAL HELPERS
# ============================================================

@staticmethod
def _normalize_optional_positive(
    value: float | None,
    name: str,
) -> float | None:
    """
    Normalize an optional positive numeric value.

    None is permitted for optional ratings.
    """

    if value is None:
        return None

    try:
        normalized = float(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            f"{name} must be numeric or None."
        ) from exc

    if normalized <= 0.0:
        raise ValueError(
            f"{name} must be greater than zero."
        )

    return normalized

@staticmethod
def _endpoint_identifier(
    endpoint: Any,
) -> Any:
    """
    Return a stable diagnostic identifier where available.

    No endpoint resolution is performed here.
    """

    if endpoint is None:
        return None

    return getattr(
        endpoint,
        "id",
        endpoint,
    )
```

__all__ = [
"Breaker",
]
