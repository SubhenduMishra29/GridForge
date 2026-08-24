# ============================================================
# File: core/network/__init__.py
# GridForge V2 — Network Layer
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Network Layer
==========================

Public package boundary for the assembled electrical network.

The Network Layer assembles canonical objects from ``core.model``
into an engineering network representation.

Architecture
------------

    core.model
        Canonical electrical entities
              |
              v
    core.network
        Network
        Registry
        Index
        State
        Topology
        Y-Bus
              |
              v
    core.analysis
        Engineering studies
              |
              v
    core.solver
        Numerical algorithms


Public Responsibilities
-----------------------

The package provides:

    Network
        Central assembled-network façade.

    NetworkRegistry
        Owns canonical network-element membership.

    BusIndex
        Owns deterministic bus-to-matrix indexing.

    NetworkState
        Owns network-derived validity and revision state.

    TopologyManager
        Builds and queries derived electrical topology.

    YBusBuilder
        Builds the network admittance matrix.

    PerUnitSystem
        Re-export of the canonical Base-Layer per-unit service.


Architectural Boundary
----------------------

``core.model`` owns the canonical electrical entities.

``core.network`` does not define alternate electrical models.

The Network Layer assembles references to canonical model objects
and provides derived network representations required by analysis
and solver layers.


Ownership
---------

Network owns:

    - network membership;
    - network-level assembly;
    - deterministic bus indexing;
    - topology service;
    - Y-bus service;
    - derived network state.

Network does not own:

    - GUI state;
    - SLD representation;
    - engineering study orchestration;
    - numerical solver algorithms;
    - electrical equipment definitions.


Command Boundary
----------------

Commands and application services are responsible for engineering
workflows such as:

    create
    connect
    disconnect
    register
    remove
    reconfigure

The Network Layer provides the assembled-network APIs consumed by
those application-level workflows.

The Network package therefore remains headless and UI-independent.


Internal Utility Boundary
-------------------------

``endpoint.resolve_terminal_bus`` is an internal network utility
used for resolving canonical terminal relationships.

It is intentionally not promoted as a primary package-level API.

This prevents callers from treating endpoint resolution as a
separate network-domain service.


Per-Unit Boundary
-----------------

The canonical implementation remains:

    core.base.per_unit.PerUnitSystem

There is no duplicate Network-layer implementation.

``PerUnitSystem`` is re-exported here only for convenient access.


Stable Public API
-----------------

Typical usage:

    from core.network import Network

    network = Network(base_mva=100.0)

    network.add_bus(bus)
    network.add_line(line)

    network.rebuild_topology()

    Ybus = network.get_ybus()


The package-level exports are intentionally narrow.

Consumers should prefer the Network façade rather than reaching
through internal implementation modules unless a specific service
contract explicitly requires it.


GridForge V2 Status
-------------------

This package is part of the GridForge V2 Network Layer baseline.

The package boundary is intentionally separated into:

    network.py
        façade

    registry.py
        membership

    indexing.py
        deterministic indexing

    state.py
        derived state

    endpoint.py
        terminal-to-bus resolution

    topology.py
        connectivity

    ybus.py
        admittance construction

Changes to this boundary require architectural justification.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations


# =====================================================================
# PRIMARY NETWORK FACADE
# =====================================================================

from .network import Network


# =====================================================================
# NETWORK ASSEMBLY SERVICES
# =====================================================================

from .registry import NetworkRegistry
from .indexing import BusIndex
from .state import NetworkState


# =====================================================================
# DERIVED NETWORK SERVICES
# =====================================================================

from .topology import TopologyManager
from .ybus import YBusBuilder


# =====================================================================
# BASE-LAYER SERVICE
# =====================================================================

# PerUnitSystem fundamentally belongs to core.base.
#
# It is re-exported here for Network-layer convenience only.
#
# There must be no duplicate:
#
#     core/network/per_unit.py

from core.base.per_unit import PerUnitSystem


# =====================================================================
# PUBLIC PACKAGE API
# =====================================================================

__all__ = [
    # Primary façade
    "Network",

    # Assembly infrastructure
    "NetworkRegistry",
    "BusIndex",
    "NetworkState",

    # Derived network services
    "TopologyManager",
    "YBusBuilder",

    # Base-layer service
    "PerUnitSystem",
]


# =====================================================================
# PACKAGE VERSION
# =====================================================================

__version__ = "2.0.0"
