# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/connections/topology_adapter.py
#
# Purpose:
#     Defines the synchronization boundary between the UI SLD
#     connection subsystem and the authoritative GridForge Core
#     topology.
#
# Architectural Role:
#     Prevents the UI connection subsystem from becoming a second
#     electrical-network database.
#
# Responsibilities:
#     - define the UI-to-Core connection creation boundary;
#     - define the UI-to-Core connection removal boundary;
#     - provide an explicit synchronization contract;
#     - keep the UI independent from the concrete Core API.
#
# Does NOT:
#     - own Core;
#     - store electrical topology;
#     - implement electrical calculations;
#     - validate electrical-network topology;
#     - create UI connections;
#     - create QGraphicsItems;
#     - import Core implementation classes;
#     - silently mutate Core objects.
#
# Architecture
# ----------
#
#     SLD / ConnectionManager
#              │
#              ▼
#       TopologyAdapter
#              │
#              ▼
#       Core Network API
#
# The adapter is intentionally a Protocol. The concrete Core
# integration is supplied separately once the authoritative Core
# network API is selected.
#
# This prevents the UI architecture from inventing or duplicating
# a Core topology contract merely to make the UI compile.
#
# ============================================================

"""
GridForge V2 — Topology Adapter.

Defines the explicit synchronization contract between the
UI-level SLD connection subsystem and the authoritative Core
network layer.
"""

from __future__ import annotations

from typing import Protocol

from .connection import Connection


class TopologyAdapter(Protocol):
    """
    UI/Core topology synchronization contract.

    ``TopologyAdapter`` is intentionally a Protocol rather than a
    concrete implementation.

    The UI connection subsystem depends only on this boundary.
    The concrete implementation is responsible for translating
    UI ``Connection`` objects into the actual Core network API.

    Core remains authoritative for electrical topology.
    """

    def add_connection(
        self,
        connection: Connection,
    ) -> None:
        """
        Synchronize a committed UI connection into Core.

        Parameters
        ----------
        connection:
            Committed logical UI connection.

        Notes
        -----
        The adapter implementation must translate this logical
        connection into the authoritative Core topology API.

        The UI layer must not directly mutate Core topology.
        """
        ...

    def remove_connection(
        self,
        connection: Connection,
    ) -> None:
        """
        Synchronize removal of a UI connection into Core.

        Parameters
        ----------
        connection:
            Logical connection being removed.

        Notes
        -----
        The adapter implementation must perform the corresponding
        Core topology operation through the official Core API.

        The UI layer must not directly mutate Core topology.
        """
        ...


__all__ = [
    "TopologyAdapter",
]
