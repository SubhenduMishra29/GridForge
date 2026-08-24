# ============================================================
# File: core/network/state.py
# GridForge V2 — Network Derived State
# Author: Subhendu Mishra
# ============================================================

"""
Network-derived state management.

NetworkState owns:

    topology revision
    Y-bus revision
    topology dirty state
    Y-bus dirty state

It does not own model objects, topology graphs, or Y-bus
mathematics.
"""

from __future__ import annotations


class NetworkState:
    """
    Own revision and invalidation state for an assembled Network.
    """

    def __init__(self) -> None:
        self.topology_revision = 0
        self.ybus_revision = -1

        self.topology_dirty = True
        self.ybus_dirty = True

    # ============================================================
    # INVALIDATION
    # ============================================================

    def invalidate_topology(self) -> None:
        """
        Invalidate topology and everything derived from topology.
        """

        self.topology_revision += 1

        self.topology_dirty = True
        self.ybus_dirty = True
        self.ybus_revision = -1

    # ------------------------------------------------------------

    def invalidate_ybus(self) -> None:
        """
        Invalidate Y-bus without changing topology revision.
        """

        self.ybus_dirty = True
        self.ybus_revision = -1

    # ============================================================
    # MARK VALID
    # ============================================================

    def topology_rebuilt(self) -> None:
        """
        Mark topology as synchronized with the current revision.
        """

        self.topology_dirty = False

    # ------------------------------------------------------------

    def ybus_rebuilt(self) -> None:
        """
        Mark Y-bus as synchronized with the current topology
        revision.
        """

        self.ybus_dirty = False
        self.ybus_revision = self.topology_revision

    # ============================================================
    # QUERIES
    # ============================================================

    @property
    def ybus_valid(self) -> bool:
        """
        Return whether the current Y-bus is valid for the current
        topology revision.
        """

        return (
            not self.ybus_dirty
            and self.ybus_revision == self.topology_revision
        )
