# core/model/line.py

"""
GridForge Transmission Line Model
=================================

GridForge Model Layer V2

Defines the physical transmission-line model.

## Architecture

A Line is a two-terminal impedance-bearing electrical branch:

```
Bus ── Terminal ── Line ── Terminal ── Bus
```

The authoritative physical connection points are:

```
from_terminal
to_terminal
```

The connected buses are derived through the Terminal interface and
are therefore not stored as independent connection state.

The Line uses the standard transmission-line π-equivalent:

```
Z_series = R + jX

Y_shunt,total = jB
```

The numerical network/solver layer is responsible for applying:

```
jB / 2
```

at each terminal when constructing Y-bus.

## Responsibilities

The Line model provides:

* physical two-terminal connectivity
* series resistance
* series reactance
* total shunt susceptance
* thermal/equipment rating
* in-service state
* local parameter validation
* diagnostic information

The Line does NOT:

* build Y-bus
* stamp admittance matrices
* calculate branch power flow
* calculate losses
* perform load flow
* perform short-circuit calculations
* perform contingency analysis
* perform protection calculations
* perform dynamic simulation
* manage global topology
* manage GUI objects

Those responsibilities belong to the appropriate GridForge layers.

## Units

```
r       : per-unit
x       : per-unit
b       : per-unit
rate    : MVA
```

## GridForge V2 Status

This module is part of the GridForge Model Layer V2 baseline.

The physical connection contract is Terminal-based.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from **future** import annotations

from math import isfinite

from .branch import Branch
from .terminal import Terminal

# =====================================================================

# TRANSMISSION LINE

# =====================================================================

class Line(Branch):
"""
GridForge physical transmission-line model.

```
Parameters
----------
id : str
    Unique GridForge line identifier.

endpoint_from :
    From-side electrical endpoint.

endpoint_to :
    To-side electrical endpoint.

r : float
    Series resistance in per-unit.

x : float
    Series reactance in per-unit.

b : float, optional
    Total line shunt susceptance in per-unit.

name : str, optional
    Human-readable line name.

rate_mva : float, optional
    Thermal/equipment rating in MVA.

Notes
-----
``from_terminal`` and ``to_terminal`` are the authoritative local
physical connection points.

The connected buses are derived through the terminals.

The Line has no transformer tap or phase-shift parameter.
"""

def __init__(
    self,
    id: str,
    endpoint_from,
    endpoint_to,
    r: float,
    x: float,
    b: float = 0.0,
    name: str = "",
    rate_mva: float = 100.0,
):
    """
    Initialize a GridForge transmission line.
    """

    # -------------------------------------------------------------
    # Basic branch identity
    # -------------------------------------------------------------

    super().__init__(
        id=id,
        bus_from=(
            endpoint_from
            if hasattr(endpoint_from, "id")
            else None
        ),
        bus_to=(
            endpoint_to
            if hasattr(endpoint_to, "id")
            else None
        ),
        r=r,
        x=x,
        b=b,
        name=name,
        rate_mva=rate_mva,
        tap=1.0,
        shift=0.0,
    )

    # -------------------------------------------------------------
    # Authoritative physical terminals
    # -------------------------------------------------------------

    self.from_terminal = (
        endpoint_from
        if isinstance(endpoint_from, Terminal)
        else Terminal(endpoint_from, owner=self)
    )

    self.to_terminal = (
        endpoint_to
        if isinstance(endpoint_to, Terminal)
        else Terminal(endpoint_to, owner=self)
    )

    if self.from_terminal is self.to_terminal:
        raise ValueError(
            f"Line '{self.id}' cannot connect a terminal to itself."
        )

    # -------------------------------------------------------------
    # Ensure terminal ownership is local to this Line.
    #
    # Existing Terminal objects may already have an owner. Do not
    # silently overwrite a different owner.
    # -------------------------------------------------------------

    if (
        self.from_terminal.owner is not None
        and self.from_terminal.owner is not self
    ):
        raise ValueError(
            f"Line '{self.id}' from_terminal already belongs "
            "to another equipment object."
        )

    if (
        self.to_terminal.owner is not None
        and self.to_terminal.owner is not self
    ):
        raise ValueError(
            f"Line '{self.id}' to_terminal already belongs "
            "to another equipment object."
        )

    self.from_terminal.owner = self
    self.to_terminal.owner = self

    # -------------------------------------------------------------
    # Validate local electrical parameters.
    # -------------------------------------------------------------

    self._validate_line_parameters()

# =================================================================
# TERMINALS
# =================================================================

@property
def terminals(self) -> tuple[Terminal, Terminal]:
    """
    Return the physical terminal pair.

    Returns
    -------
    tuple
        ``(from_terminal, to_terminal)``
    """

    return (
        self.from_terminal,
        self.to_terminal,
    )

# =================================================================
# BUS COMPATIBILITY
# =================================================================

@property
def from_bus(self):
    """
    Return the Bus-like endpoint currently associated with the
    from-side terminal.

    This is a derived compatibility accessor.

    The authoritative connection remains:

        self.from_terminal.endpoint
    """

    return self.from_terminal.bus

@property
def to_bus(self):
    """
    Return the Bus-like endpoint currently associated with the
    to-side terminal.

    This is a derived compatibility accessor.

    The authoritative connection remains:

        self.to_terminal.endpoint
    """

    return self.to_terminal.bus

# =================================================================
# ENDPOINT COMPATIBILITY
# =================================================================

@property
def from_endpoint(self):
    """
    Return the authoritative from-side endpoint.
    """

    return self.from_terminal.endpoint

@property
def to_endpoint(self):
    """
    Return the authoritative to-side endpoint.
    """

    return self.to_terminal.endpoint

def endpoints(self) -> tuple:
    """
    Return the authoritative physical endpoint pair.
    """

    return (
        self.from_endpoint,
        self.to_endpoint,
    )

# =================================================================
# CONNECTION STATE
# =================================================================

@property
def is_connected(self) -> bool:
    """
    Return True when both physical terminals have endpoints.
    """

    return (
        self.from_terminal.is_connected
        and self.to_terminal.is_connected
    )

# =================================================================
# LINE PARAMETERS
# =================================================================

@property
def r_pu(self) -> float:
    """
    Return series resistance in per-unit.
    """

    return self.r

@property
def x_pu(self) -> float:
    """
    Return series reactance in per-unit.
    """

    return self.x

@property
def b_pu(self) -> float:
    """
    Return total line shunt susceptance in per-unit.

    This is the TOTAL B value. The network/Y-bus layer applies
    B/2 at each terminal.
    """

    return self.b

@property
def is_pi_model(self) -> bool:
    """
    Return True because this Line uses the standard π-equivalent.
    """

    return True

# =================================================================
# LOCAL VALIDATION
# =================================================================

def _validate_line_parameters(self) -> None:
    """
    Validate local line parameters.

    Engineering compatibility with the connected network belongs
    to core/network and core/validation.
    """

    if not isfinite(self.r):
        raise ValueError(
            f"Line '{self.id}' resistance must be finite."
        )

    if self.r < 0.0:
        raise ValueError(
            f"Line '{self.id}' resistance cannot be negative."
        )

    if not isfinite(self.x):
        raise ValueError(
            f"Line '{self.id}' reactance must be finite."
        )

    if self.x == 0.0:
        raise ValueError(
            f"Line '{self.id}' reactance cannot be zero."
        )

    if not isfinite(self.b):
        raise ValueError(
            f"Line '{self.id}' shunt susceptance must be finite."
        )

    if not isfinite(self.rate_mva):
        raise ValueError(
            f"Line '{self.id}' MVA rating must be finite."
        )

    if self.rate_mva <= 0.0:
        raise ValueError(
            f"Line '{self.id}' MVA rating must be greater than zero."
        )

# =================================================================
# CONNECTION
# =================================================================

def connect_from(self, endpoint) -> None:
    """
    Connect the from-side terminal to an electrical endpoint.

    This changes only the local physical connection.

    Global topology is managed by core/network.
    """

    self.from_terminal.connect(endpoint)

def connect_to(self, endpoint) -> None:
    """
    Connect the to-side terminal to an electrical endpoint.

    This changes only the local physical connection.

    Global topology is managed by core/network.
    """

    self.to_terminal.connect(endpoint)

def disconnect_from(self) -> None:
    """
    Disconnect the from-side terminal locally.
    """

    self.from_terminal.disconnect()

def disconnect_to(self) -> None:
    """
    Disconnect the to-side terminal locally.
    """

    self.to_terminal.disconnect()

# =================================================================
# DIAGNOSTICS
# =================================================================

def summary(self) -> dict:
    """
    Return structured transmission-line information.
    """

    return {
        "id": self.id,
        "name": self.name,
        "type": "line",

        "from_terminal": self.from_terminal.summary(),
        "to_terminal": self.to_terminal.summary(),

        "from_endpoint": (
            self.from_endpoint.id
            if self.from_endpoint is not None
            else None
        ),

        "to_endpoint": (
            self.to_endpoint.id
            if self.to_endpoint is not None
            else None
        ),

        "from_bus": (
            self.from_bus.id
            if self.from_bus is not None
            else None
        ),

        "to_bus": (
            self.to_bus.id
            if self.to_bus is not None
            else None
        ),

        "connected": self.is_connected,

        "r_pu": self.r,
        "x_pu": self.x,
        "b_pu": self.b,

        "model": "pi",
        "rate_mva": self.rate_mva,

        "tap": 1.0,
        "shift": 0.0,

        "in_service": self.in_service,
    }

# =================================================================
# REPRESENTATION
# =================================================================

def __repr__(self) -> str:
    """
    Return a concise developer-facing representation.
    """

    from_id = (
        self.from_endpoint.id
        if self.from_endpoint is not None
        else None
    )

    to_id = (
        self.to_endpoint.id
        if self.to_endpoint is not None
        else None
    )

    return (
        f"<Line "
        f"id={self.id}, "
        f"{from_id} -> {to_id}, "
        f"r={self.r:.6f}, "
        f"x={self.x:.6f}, "
        f"b={self.b:.6f}, "
        f"rate={self.rate_mva:.2f} MVA, "
        f"in_service={self.in_service}>"
    )
```
