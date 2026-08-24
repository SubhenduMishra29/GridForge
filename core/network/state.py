# ============================================================
# File: core/network/state.py
# GridForge V2 — Network Layer
# ============================================================
"""
Network Derived-State Lifecycle
================================

Tracks validity and revisions of derived Network representations.

Responsibilities
----------------
- Track topology revision.
- Track Y-bus revision.
- Track topology dirty state.
- Track Y-bus dirty state.
- Mark derived representations current after successful builds.

Does NOT
--------
- Build topology.
- Build Y-bus.
- Mutate model objects.
- Register network elements.
- Perform engineering calculations.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations


class NetworkState:
    """
    Lifecycle state for Network-derived representations.

    A topology mutation invalidates both topology and Y-bus.

    A Y-bus-only mutation invalidates Y-bus without changing the
    topology revision.
    """

    def __init__(self) -> None:
        self.topology_revision: int = 0
        self.ybus_revision: int = -1

        self.topology_dirty: bool = True
        self.ybus_dirty: bool = True

    # ============================================================
    # INVALIDATION
    # ============================================================

    def invalidate_topology(self) -> None:
        """
        Invalidate topology and everything depending on topology.
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
    # BUILD COMPLETION
    # ============================================================

    def mark_topology_built(self) -> None:
        """
        Mark topology representation as current.
        """

        self.topology_dirty = False

    # ------------------------------------------------------------

    def mark_ybus_built(self) -> None:
        """
        Mark Y-bus representation as current for the current
        topology revision.
        """

        self.ybus_dirty = False
        self.ybus_revision = self.topology_revision

    # ============================================================
    # VALIDITY
    # ============================================================

    def ybus_is_current(
        self,
        ybus: object,
    ) -> bool:
        """
        Determine whether the supplied Y-bus is current.
        """

        return (
            ybus is not None
            and not self.ybus_dirty
            and self.ybus_revision
            == self.topology_revision
        )
