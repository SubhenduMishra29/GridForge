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
#     Prevents the UI connection manager from becoming a second
#     electrical-network database.
#
# Responsibilities:
#     - define UI-to-Core connection hooks;
#     - define UI-to-Core removal hooks;
#     - provide a controlled synchronization boundary.
#
# Does NOT:
#     - implement electrical calculations;
#     - own the Core network;
#     - silently mutate Core objects;
#     - import the Core implementation.
#
# Detailed Working:
#
#     UI:
#         ConnectionManager
#                |
#                v
#         TopologyAdapter
#                |
#                v
#         Core Network API
#
# The adapter remains deliberately minimal until the actual Core
# network API is selected. This avoids inventing a Core contract
# merely to make the UI compile.
#
# ============================================================

"""
GridForge V2 — Topology Adapter.
"""

from __future__ import annotations

from typing import Protocol

from .connection import Connection


class TopologyAdapter(Protocol):
    """
    Protocol defining the future UI/Core topology boundary.

    A concrete implementation will be supplied when the SLD UI is
    connected to the authoritative Core network API.
    """

    def add_connection(
        self,
        connection: Connection,
    ) -> None:
        """
        Synchronize a committed UI connection into Core.
        """
        ...

    def remove_connection(
        self,
        connection: Connection,
    ) -> None:
        """
        Synchronize connection removal into Core.
        """
        ...
