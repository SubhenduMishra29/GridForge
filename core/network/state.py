# ============================================================
# File: core/network/state.py
# GridForge V2 — Network Derived State
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Network Derived State
====================================

NetworkState owns lifecycle and revision information for
Network-derived structural state.

It owns:

    topology_revision
    topology_dirty

It does not own:

    - canonical model objects
    - equipment membership
    - topology graphs
    - terminal relationships
    - BusIndex mappings
    - numerical Y-bus objects
    - Y-bus validity or revision state
    - solver state
    - study state
    - numerical operating-point state

Ownership
---------

Network:

    authoritative domain objects and structural lifecycle

NetworkState:

    topology revision and topology synchronization state

BusIndex:

    derived bus.id -> matrix index mapping and its validity

Numerical:

    derived numerical artifacts, including YBus

A numerical artifact records the Network topology revision from
which it was derived. Its freshness is determined externally by
comparison:

    artifact.revision == network.state.topology_revision

NetworkState never owns or mutates numerical artifacts.
"""

from __future__ import annotations


class NetworkState:
    """
    Lifecycle and revision state for an assembled Network.

    NetworkState tracks whether Network-derived topology is
    synchronized with the current authoritative Network revision.

    It deliberately has no knowledge of numerical artifacts such
    as YBus or numerical indexing structures such as BusIndex.
    """

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self) -> None:
        """
        Initialize Network-derived structural state.

        A newly created Network has not yet synchronized its
        derived topology representation.
        """

        self.topology_revision = 0
        self.topology_dirty = True

    # ============================================================
    # INVALIDATION
    # ============================================================

    def invalidate_topology(self) -> None:
        """
        Invalidate derived topology for a structural Network change.

        This method represents a new authoritative topology
        revision.

        Callers responsible for other derived artifacts, such as
        BusIndex, must invalidate those artifacts according to their
        own ownership contracts.
        """

        self.topology_revision += 1
        self.topology_dirty = True

    # ============================================================
    # SYNCHRONIZATION
    # ============================================================

    def topology_rebuilt(self) -> None:
        """
        Mark derived topology as synchronized with the current
        topology revision.

        Rebuilding topology does not create a new authoritative
        topology revision. It synchronizes derived topology with the
        existing revision.
        """

        self.topology_dirty = False

    # ============================================================
    # QUERIES
    # ============================================================

    @property
    def topology_valid(self) -> bool:
        """
        Return whether derived topology is synchronized with the
        current Network topology revision.
        """

        return not self.topology_dirty

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            "NetworkState("
            f"topology_revision={self.topology_revision}, "
            f"topology_dirty={self.topology_dirty}"
            ")"
        )


__all__ = [
    "NetworkState",
]
