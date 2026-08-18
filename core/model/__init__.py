"""
GridForge Model Layer V2
========================

Public API for the GridForge Model Layer.

The model layer contains the authoritative engineering representation
of the GridForge digital twin.

Model-layer responsibilities
----------------------------

The model layer owns:

- Persistent model-object identity.
- Physical equipment representation.
- Electrical equipment parameters.
- Physical terminals.
- Local physical connectivity.
- Authoritative equipment operating state.
- Electrical injection interfaces.
- Equipment ratings and limits.
- Local model validation.
- Model diagnostics.

The model layer does NOT own:

- Global network topology assembly.
- Network connectivity algorithms.
- Y-bus construction.
- Numerical power-flow calculations.
- Short-circuit calculations.
- Contingency calculations.
- Protection coordination algorithms.
- Dynamic state integration.
- DAE solving.
- GUI geometry or rendering.
- Study orchestration.

Those responsibilities belong to the appropriate GridForge
network, solver, analysis, protection, simulation, plugin,
and UI layers.

Public API
----------

The package exports the canonical GridForge model classes so that
higher-level layers can use:

    from core.model import Bus, Line, Transformer

instead of depending unnecessarily on individual implementation
modules.

Architecture
------------

The semantic model classifications used by GridForge are not a
rigid inheritance hierarchy:

    Asset
        Persistent uniquely identifiable Digital Twin entity.

    Equipment
        Engineered physical apparatus.

    Component
        Engineering-significant constituent part.

    Device
        Independently identifiable functional apparatus or element.

These classifications describe engineering semantics and do not
require a giant Asset -> Equipment -> Component -> Device class tree.

Specialized engineering implementations may be supplied by the
appropriate plugin/domain layers.

Frozen Model Layer Boundary
---------------------------

The model layer provides the authoritative physical/model state.

    core/model
         |
         v
    core/network
         |
         v
    core/solver
         |
         v
    core/analysis

The model must remain independent of numerical study algorithms.

GridForge V2 Status
-------------------

This package represents the frozen GridForge Model Layer V2
baseline.

Changes to the model layer require evidence of a genuinely
fundamental engineering-model requirement that cannot be satisfied
by an existing model interface, specialized model, plugin,
network layer, solver layer, analysis layer, protection layer,
simulation layer, or UI layer.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations


# =====================================================================
# CORE
# =====================================================================

from .base import ElectricalObject
from .terminal import Terminal


# =====================================================================
# NETWORK / ELECTRICAL TOPOLOGY MODELS
# =====================================================================

from .bus import Bus, BusType
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
# MEASUREMENT / INSTRUMENT TRANSFORMERS
# =====================================================================

from .ct import CTPolarity, CurrentTransformer
from .pt import PTPolarity, PotentialTransformer
from .cvt import CVT


# =====================================================================
# PROTECTION
# =====================================================================

from .relay import Relay


# =====================================================================
# NETWORK CONTAINER / STATE / GRAPH
# =====================================================================

from .state import BusState, DynamicState
from .graph import Graph
from .grid import Grid


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = (
    # -----------------------------------------------------------------
    # Core
    # -----------------------------------------------------------------
    "ElectricalObject",
    "Terminal",

    # -----------------------------------------------------------------
    # Bus / branch / switchgear
    # -----------------------------------------------------------------
    "Bus",
    "BusType",
    "Branch",
    "Line",
    "Cable",
    "Transformer",
    "Disconnector",
    "Breaker",
    "Fuse",

    # -----------------------------------------------------------------
    # Electrical injections
    # -----------------------------------------------------------------
    "Injection",
    "Load",
    "Generator",
    "Motor",
    "Shunt",

    # -----------------------------------------------------------------
    # Measurement
    # -----------------------------------------------------------------
    "CT",
    "PT",
    "CVT",

    # -----------------------------------------------------------------
    # Protection
    # -----------------------------------------------------------------
    "Relay",

    # -----------------------------------------------------------------
    # Network / state infrastructure
    # -----------------------------------------------------------------
    "State",
    "Graph",
    "Grid",
)

