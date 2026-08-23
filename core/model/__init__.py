```python
"""
GridForge V2 Model Layer
========================

Author:
    Subhendu Mishra

File:
    core/model/__init__.py

Purpose
-------
Public API for the authoritative GridForge V2 Model Layer.

The model layer owns:

    - persistent engineering-model identity
    - physical equipment representation
    - electrical parameters
    - terminals
    - local equipment connectivity
    - equipment operating state
    - electrical injection contracts
    - ratings and limits
    - local validation
    - model diagnostics

The model layer does NOT own:

    - global network topology
    - graph construction
    - network connectivity algorithms
    - Y-bus construction
    - numerical solving
    - power-flow calculations
    - short-circuit calculations
    - protection coordination
    - dynamic simulation
    - GUI state
    - SLD geometry
    - rendering

Those responsibilities belong to the appropriate Network,
Solver, Analysis, Protection, Simulation, Plugin, and UI layers.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations


# =====================================================================
# CORE MODEL CONTRACTS
# =====================================================================

from .base import ElectricalObject
from .terminal import Terminal
from .injection import Injection


# =====================================================================
# NETWORK / ELECTRICAL ELEMENTS
# =====================================================================

from .bus import Bus, BusType
from .branch import Branch
from .line import Line
from .cable import Cable
from .transformer import Transformer
from .switch import Switch

from .breaker import Breaker
from .disconnector import Disconnector
from .fuse import Fuse


# =====================================================================
# ELECTRICAL POWER / INJECTION MODELS
# =====================================================================

from .load import Load
from .generator import Generator
from .synchronous_machine import (
    SynchronousMachine,
    SyncMachine,
)
from .motor import Motor

from .shunt import Shunt
from .capacitor import Capacitor
from .reactor import Reactor
from .solar import Solar
from .battery import Battery


# =====================================================================
# GRID / SOURCE MODEL
# =====================================================================

from .grid import Grid


# =====================================================================
# MEASUREMENT / INSTRUMENT TRANSFORMERS
# =====================================================================

from .ct import (
    CTPolarity,
    CurrentTransformer,
)

from .pt import (
    PTPolarity,
    PotentialTransformer,
)

from .cvt import CVT


# =====================================================================
# PROTECTION
# =====================================================================

from .relay import Relay


# =====================================================================
# STATE MODELS
# =====================================================================

from .state import (
    BusState,
    DynamicState,
)


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = (
    # -----------------------------------------------------------------
    # Core contracts
    # -----------------------------------------------------------------
    "ElectricalObject",
    "Terminal",
    "Injection",

    # -----------------------------------------------------------------
    # Network / electrical elements
    # -----------------------------------------------------------------
    "Bus",
    "BusType",
    "Branch",
    "Line",
    "Cable",
    "Transformer",
    "Switch",
    "Breaker",
    "Disconnector",
    "Fuse",

    # -----------------------------------------------------------------
    # Power / injection models
    # -----------------------------------------------------------------
    "Load",
    "Generator",
    "SynchronousMachine",
    "SyncMachine",
    "Motor",
    "Shunt",
    "Capacitor",
    "Reactor",
    "Solar",
    "Battery",

    # -----------------------------------------------------------------
    # Grid / source
    # -----------------------------------------------------------------
    "Grid",

    # -----------------------------------------------------------------
    # Measurement
    # -----------------------------------------------------------------
    "CTPolarity",
    "CurrentTransformer",
    "PTPolarity",
    "PotentialTransformer",
    "CVT",

    # -----------------------------------------------------------------
    # Protection
    # -----------------------------------------------------------------
    "Relay",

    # -----------------------------------------------------------------
    # State
    # -----------------------------------------------------------------
    "BusState",
    "DynamicState",
)
```
