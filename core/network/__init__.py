"""
GridForge Network Layer
=======================

GridForge Network Layer V2

Provides the assembled-network infrastructure that connects the
canonical electrical model layer with the numerical solver and
engineering analysis layers.

Architecture
------------

    core/model/
        Canonical electrical entities
                |
                v
    core/network/
        Network
        TopologyManager
        PerUnitSystem
        YBusBuilder
                |
                v
    core/analysis/
        Engineering study orchestration
                |
                v
    core/solver/
        Numerical algorithms


Responsibilities
----------------
The Network Layer provides:

- Assembled electrical network management.
- Canonical model-object collections.
- System MVA-base management.
- Deterministic bus indexing.
- Electrical topology management.
- Network connectivity and island detection.
- Y-bus construction and caching.
- Network-level state and invalidation.
- Per-unit conversion services through the GridForge Base Layer.

The Network Layer does NOT:

- Define electrical equipment models.
- Duplicate Bus, Line, Transformer, Generator, Load, or other
  ``core.model`` classes.
- Implement Newton-Raphson power-flow algorithms.
- Implement Jacobian or mismatch mathematics.
- Implement short-circuit numerical algorithms.
- Implement protection algorithms.
- Implement transient or dynamic numerical integration.
- Implement engineering validation rules.
- Implement GUI behavior.


Canonical Model Boundary
------------------------
``core.model`` remains the single source of truth for electrical
entities.

The Network Layer stores references to canonical model objects.

It does not create alternate network-specific versions of:

    Bus
    Line
    Transformer
    Generator
    Load
    Shunt
    Breaker
    Disconnector
    Fuse
    CT
    PT
    CVT
    Relay
    Motor
    Cable
    or other electrical equipment.


Per-Unit Boundary
-----------------
The canonical per-unit implementation is provided by:

    core.base.per_unit.PerUnitSystem

The Network Layer does not maintain a duplicate ``per_unit.py``.

This keeps fundamental unit-conversion functionality in the Base
Layer while allowing Network to instantiate a system-wide per-unit
service using the Network's MVA base.


Topology Boundary
-----------------
``TopologyManager`` maintains the derived electrical connectivity
graph.

It does not become the source of truth for equipment.

Topology is derived from canonical model objects and their current
service state.

Topology-dependent network representations, including Y-bus, are
invalidated when topology changes.


Y-Bus Boundary
--------------
``YBusBuilder`` constructs the network admittance matrix.

It is responsible for:

- Bus indexing required by Y-bus construction.
- Line admittance stamping.
- Transformer admittance stamping.
- Network shunt stamping.
- Sparse Y-bus construction.

It does NOT:

- Solve power flow.
- Perform Newton-Raphson iterations.
- Calculate faults.
- Perform dynamic simulation.
- Perform protection calculations.


Public API
----------
The principal Network Layer objects are:

    Network
        Central assembled-network container.

    TopologyManager
        Electrical connectivity and island-management service.

    YBusBuilder
        Network admittance-matrix construction service.

    PerUnitSystem
        Re-exported from ``core.base.per_unit`` for convenient
        Network-layer access.

Typical usage
-------------

    from core.network import (
        Network,
        TopologyManager,
        YBusBuilder,
        PerUnitSystem,
    )

    network = Network(base_mva=100.0)

    network.add_bus(bus)
    network.add_line(line)

    network.rebuild_topology()
    Ybus = network.build_ybus()


Design Principles
-----------------
1. ``core/model`` owns electrical entities.
2. ``core/network`` assembles those entities.
3. ``core/base`` owns fundamental reusable infrastructure.
4. ``core/analysis`` orchestrates engineering studies.
5. ``core/solver`` owns numerical algorithms.
6. Network services must not perform solver responsibilities.
7. Derived network state must be invalidated explicitly.
8. No GUI state is stored in the Network Layer.
9. No numerical study state is hidden inside model objects.
10. Network APIs should remain stable and narrow.


GridForge V2 Status
-------------------
This module is part of the GridForge Network Layer V2
freeze-audit baseline.

The package exports the stable public Network Layer API.

Changes after the Network Layer is frozen require evidence of a
genuinely fundamental architectural requirement that cannot be
satisfied through the existing model, base, network, analysis, or
solver boundaries.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations


# =====================================================================
# PUBLIC NETWORK API
# =====================================================================

from .network import Network
from .topology import TopologyManager
from .ybus import YBusBuilder


# =====================================================================
# BASE-LAYER PER-UNIT API
# =====================================================================
#
# PerUnitSystem is fundamentally a Base Layer service.
#
# It is re-exported here for convenient Network-layer access, but the
# implementation remains exclusively in:
#
#     core.base.per_unit
#
# There must be no core/network/per_unit.py duplicate.
#

from core.base.per_unit import PerUnitSystem


# =====================================================================
# PUBLIC PACKAGE EXPORTS
# =====================================================================

__all__ = [
    "Network",
    "TopologyManager",
    "YBusBuilder",
    "PerUnitSystem",
]


# =====================================================================
# PACKAGE VERSION
# =====================================================================

__version__ = "2.0.0"
