```python
"""
GridForge Model Layer V2
========================

Public model-layer API for GridForge.

The ``core.model`` package contains the authoritative engineering
models representing the physical and logical entities of the
GridForge digital twin.

Architecture
------------

The model layer owns:

    - Physical equipment models
    - Electrical injection models
    - Terminals and local physical connections
    - Equipment operating state
    - Equipment ratings and parameters
    - Model-level validation
    - Model diagnostics

The model layer does NOT own:

    - Global network topology assembly
    - Y-bus construction
    - Numerical power-flow calculations
    - Short-circuit calculations
    - Contingency studies
    - Protection coordination algorithms
    - Dynamic simulation
    - GUI state or geometry
    - Study execution

Those responsibilities belong to the appropriate GridForge
network, solver, analysis, protection, simulation, and UI layers.

Public API
----------

The commonly used model classes are exported here so higher-level
GridForge layers can import them from:

    from core.model import Bus, Line, Transformer

rather than depending on individual implementation modules.

GridForge V2 Status
-------------------

This package represents the frozen GridForge Model Layer V2
baseline.

Changes to this package require evidence of a genuinely fundamental
model-layer requirement that cannot be satisfied through an existing
model, interface, plugin, network layer, or higher-level service.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations


# =====================================================================
# CORE MODEL OBJECTS
# =====================================================================

from .base import ElectricalObject
from .terminal import Terminal


# =====================================================================
# NETWORK / TOPOLOGY MODELS
# =====================================================================

from .bus import Bus
from .branch import Branch
from .line import Line
from .cable import Cable
from .transformer import Transformer

from .disconnector import Disconnector
from .breaker import Breaker
from .fuse import Fuse


# =====================================================================
# ELECTRICAL INJECTION MODELS
# =====================================================================

from .injection import Injection
from .load import Load
from .generator import Generator
from .motor import Motor
from .shunt import Shunt


# =====================================================================
# MEASUREMENT / INSTRUMENT TRANSFORMER MODELS
# =====================================================================

from .ct import CT
from .pt import PT
from .cvt import CVT


# =====================================================================
# PROTECTION MODELS
# =====================================================================

from .relay import Relay


# =====================================================================
# SYSTEM / STATE / GRAPH MODELS
# =====================================================================

from .state import State
from .graph import Graph
from .grid import Grid


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = (
    # Core
    "ElectricalObject",
    "Terminal",

    # Network / topology
    "Bus",
    "Branch",
    "Line",
    "Cable",
    "Transformer",
    "Disconnector",
    "Breaker",
    "Fuse",

    # Electrical injections
    "Injection",
    "Load",
    "Generator",
    "Motor",
    "Shunt",

    # Measurement
    "CT",
    "PT",
    "CVT",

    # Protection
    "Relay",

    # System / state / graph
    "State",
    "Graph",
    "Grid",
)
```
