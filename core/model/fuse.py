# ============================================================

# File: core/model/fuse.py

# GridForge V2 — Model Layer

# Author: Subhendu Mishra

# ============================================================

"""
GridForge V2 Fuse Model
=======================

A fuse is a passive series protection device.

The Fuse model represents the physical/electrical state of the
fuse element. Protection calculations, fault detection, network
topology management, and SLD representation remain outside this
model.

## Architecture

```
             FUSE
      ┌─────────────────┐
      │                 │
IN ───┤    Fuse Link    ├─── OUT
      │                 │
      └─────────────────┘
```

The Fuse owns:

```
- equipment identity;
- two electrical terminals;
- rated current;
- rated voltage;
- interrupting rating;
- service state;
- blown state.
```

The Fuse does NOT own:

```
- network topology;
- Bus collections;
- fault calculations;
- short-circuit studies;
- relay logic;
- protection coordination;
- SLD state;
- GUI state;
- solver state;
- simulation state.
```

## State Semantics

A fuse conducts when:

```
in_service == True
AND
blown == False
```

A blown fuse does not conduct.

Resetting a fuse changes only the fuse's local physical state.
It does not create or modify network topology.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from math import isfinite
from typing import Any

from .base import ElectricalObject
from .terminal import Terminal

class Fuse(ElectricalObject):
"""
Static GridForge V2 fuse model.

```
The Fuse is a two-terminal passive series protection device.

Its physical state is represented by:

    - in_service
    - blown

The model does not perform protection calculations.
"""

TYPE = "FUSE"

def __init__(
    self,
    id: str,
    name: str = "",
    *,
    rated_current_a: float = 1.0,
    rated_voltage_v: float = 1.0,
    interrupting_rating_ka: float = 0.0,
    in_service: bool = True,
    blown: bool = False,
    endpoint_from: Any = None,
    endpoint_to: Any = None,
) -> None:
    """
    Create a Fuse.

    Parameters
    ----------
    id:
        Stable GridForge object identifier.

    name:
        Human-readable equipment name.

    rated_current_a:
        Continuous rated current in amperes.

    rated_voltage_v:
        Maximum rated operating voltage in volts.

    interrupting_rating_ka:
        Maximum fault-current interrupting capability in kA.

    in_service:
        Whether the fuse is installed and in service.

    blown:
        Whether the fuse element has operated/opened.

    endpoint_from:
        Optional initial endpoint for the input-side terminal.

    endpoint_to:
        Optional initial endpoint for the output-side terminal.
    """

    super().__init__(
        id=id,
        name=name,
    )

    # ============================================================
    # NAMEPLATE PARAMETERS
    # ============================================================

    self.rated_current_a = (
        self._validate_positive(
            rated_current_a,
            "rated_current_a",
        )
    )

    self.rated_voltage_v = (
        self._validate_positive(
            rated_voltage_v,
            "rated_voltage_v",
        )
    )

    self.interrupting_rating_ka = (
        self._validate_non_negative(
            interrupting_rating_ka,
            "interrupting_rating_ka",
        )
    )

    # ============================================================
    # PHYSICAL STATE
    # ============================================================

    if not isinstance(in_service, bool):
        raise TypeError(
            "in_service must be a bool."
        )

    if not isinstance(blown, bool):
        raise TypeError(
            "blown must be a bool."
        )

    self.in_service = in_service
    self.blown = blown

    # ============================================================
    # AUTHORITATIVE ELECTRICAL TERMINALS
    # ============================================================

    self.from_terminal = Terminal(
        endpoint=endpoint_from,
        owner=self,
        role="from",
    )

    self.to_terminal = Terminal(
        endpoint=endpoint_to,
        owner=self,
        role="to",
    )

    self.validate()

# =================================================================
# IDENTITY
# =================================================================

@property
def element_type(self) -> str:
    """
    Return the canonical GridForge element type.
    """

    return self.TYPE

# =================================================================
# TERMINALS
# =================================================================

@property
def terminals(
    self,
) -> tuple[Terminal, Terminal]:
    """
    Return the Fuse terminals in deterministic order.

    Order:

        from
        to
    """

    return (
        self.from_terminal,
        self.to_terminal,
    )

@property
def input_terminal(self) -> Terminal:
    """
    Return the input-side terminal.

    Alias for ``from_terminal``.
    """

    return self.from_terminal

@property
def output_terminal(self) -> Terminal:
    """
    Return the output-side terminal.

    Alias for ``to_terminal``.
    """

    return self.to_terminal

# =================================================================
# ENDPOINT ACCESS
# =================================================================

@property
def from_endpoint(self) -> Any:
    """Return the from-side endpoint."""

    return self.from_terminal.endpoint

@property
def to_endpoint(self) -> Any:
    """Return the to-side endpoint."""

    return self.to_terminal.endpoint

def endpoints(
    self,
) -> tuple[Any | None, Any | None]:
    """Return the local endpoint pair."""

    return (
        self.from_endpoint,
        self.to_endpoint,
    )

# =================================================================
# LOCAL TERMINAL CONNECTION
# =================================================================

def connect_from(
    self,
    endpoint: Any,
) -> None:
    """
    Connect the from-side terminal locally.

    This does not mutate global network topology.
    """

    if endpoint is None:
        raise ValueError(
            f"Fuse '{self.id}' from endpoint "
            "cannot be None."
        )

    self.from_terminal.connect(endpoint)

def connect_to(
    self,
    endpoint: Any,
) -> None:
    """
    Connect the to-side terminal locally.

    This does not mutate global network topology.
    """

    if endpoint is None:
        raise ValueError(
            f"Fuse '{self.id}' to endpoint "
            "cannot be None."
        )

    self.to_terminal.connect(endpoint)

def disconnect_from(self) -> None:
    """Disconnect the from-side terminal locally."""

    self.from_terminal.disconnect()

def disconnect_to(self) -> None:
    """Disconnect the to-side terminal locally."""

    self.to_terminal.disconnect()

# =================================================================
# PHYSICAL STATE
# =================================================================

@property
def conducts(self) -> bool:
    """
    Return whether the Fuse currently conducts.

    Conductivity requires both:

        in_service == True
        blown == False
    """

    return (
        self.in_service
        and not self.blown
    )

@property
def is_open(self) -> bool:
    """Return whether the Fuse is electrically open."""

    return not self.conducts

@property
def is_blown(self) -> bool:
    """Return whether the Fuse element has operated."""

    return self.blown

# =================================================================
# FUSE OPERATIONS
# =================================================================

def blow(self) -> None:
    """
    Operate the Fuse element.

    This changes only local physical state.

    It does not calculate the fault that caused the operation
    and does not directly modify network topology.
    """

    self.blown = True

def reset(self) -> None:
    """
    Reset the Fuse element.

    A reset Fuse is conductive only if it is also in service.
    """

    self.blown = False

# =================================================================
# SERVICE STATE
# =================================================================

def set_in_service(
    self,
    in_service: bool,
) -> None:
    """
    Set the Fuse service state.

    This does not modify network topology.
    """

    if not isinstance(in_service, bool):
        raise TypeError(
            "in_service must be a bool."
        )

    self.in_service = in_service

def connect(self) -> None:
    """Place the Fuse in service."""

    self.in_service = True

def disconnect(self) -> None:
    """
    Remove the Fuse from service.

    This does not change the blown state.
    """

    self.in_service = False

# =================================================================
# CONNECTIVITY
# =================================================================

@property
def connected(self) -> bool:
    """
    Return whether both Fuse terminals have endpoints.
    """

    return (
        self.from_terminal.is_connected
        and self.to_terminal.is_connected
    )

@property
def is_connected(self) -> bool:
    """
    Canonical connectivity alias.

    A Fuse is locally connected when both physical terminals
    have endpoints.
    """

    return self.connected

# =================================================================
# VALIDATION
# =================================================================

def validate_parameters(self) -> bool:
    """
    Validate Fuse-local engineering parameters.

    This does not validate network topology, fault studies,
    protection coordination, or solver state.
    """

    # Participate in the common ElectricalObject validation
    # contract.
    super().validate_parameters()

    self.rated_current_a = (
        self._validate_positive(
            self.rated_current_a,
            "rated_current_a",
        )
    )

    self.rated_voltage_v = (
        self._validate_positive(
            self.rated_voltage_v,
            "rated_voltage_v",
        )
    )

    self.interrupting_rating_ka = (
        self._validate_non_negative(
            self.interrupting_rating_ka,
            "interrupting_rating_ka",
        )
    )

    if not isinstance(
        self.in_service,
        bool,
    ):
        raise TypeError(
            "in_service must be a bool."
        )

    if not isinstance(
        self.blown,
        bool,
    ):
        raise TypeError(
            "blown must be a bool."
        )

    if self.from_terminal.owner is not self:
        raise ValueError(
            f"Fuse '{self.id}' from terminal "
            "ownership is invalid."
        )

    if self.to_terminal.owner is not self:
        raise ValueError(
            f"Fuse '{self.id}' to terminal "
            "ownership is invalid."
        )

    if self.from_terminal.role != "from":
        raise ValueError(
            f"Fuse '{self.id}' from terminal "
            "role is invalid."
        )

    if self.to_terminal.role != "to":
        raise ValueError(
            f"Fuse '{self.id}' to terminal "
            "role is invalid."
        )

    self.from_terminal.validate()
    self.to_terminal.validate()

    return True

def validate(self) -> bool:
    """
    Public Fuse validation entry point.
    """

    return self.validate_parameters()

# =================================================================
# DIAGNOSTICS
# =================================================================

def summary(self) -> dict[str, Any]:
    """
    Return static Fuse information and local state.

    No calculated fault or protection result is included.
    """

    return {
        "id": self.id,
        "name": self.name,
        "type": self.TYPE,

        "from_terminal_role":
            self.from_terminal.role,

        "to_terminal_role":
            self.to_terminal.role,

        "rated_current_a":
            self.rated_current_a,

        "rated_voltage_v":
            self.rated_voltage_v,

        "interrupting_rating_ka":
            self.interrupting_rating_ka,

        "in_service":
            self.in_service,

        "blown":
            self.blown,

        "conducts":
            self.conducts,

        "connected":
            self.connected,

        "from_endpoint":
            self._endpoint_id(
                self.from_terminal,
            ),

        "to_endpoint":
            self._endpoint_id(
                self.to_terminal,
            ),
    }

# =================================================================
# REPRESENTATION
# =================================================================

def __repr__(self) -> str:
    """
    Return a concise developer-facing representation.
    """

    return (
        f"<Fuse "
        f"id={self.id}, "
        f"rated_current="
        f"{self.rated_current_a:.3f}A, "
        f"rated_voltage="
        f"{self.rated_voltage_v:.3f}V, "
        f"blown={self.blown}, "
        f"in_service={self.in_service}>"
    )

# =================================================================
# INTERNAL HELPERS
# =================================================================

@staticmethod
def _validate_positive(
    value: float,
    field_name: str,
) -> float:
    """
    Validate and return a finite positive quantity.
    """

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
    """
    Validate and return a finite non-negative quantity.
    """

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
    """
    Safely return the terminal endpoint identifier.

    The Fuse does not impose a particular endpoint
    implementation beyond the Terminal contract.
    """

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

__all__ = [
"Fuse",
]
