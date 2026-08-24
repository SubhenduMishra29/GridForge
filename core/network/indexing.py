# ============================================================
# File: core/network/indexing.py
# GridForge V2 — Network Layer
# ============================================================
"""
Deterministic Network Bus Index
===============================

Provides the numerical bus-index representation required by
matrix-based network calculations.

Responsibilities
----------------
- Derive deterministic bus indices from Network membership.
- Maintain bus.id -> numerical matrix index.
- Rebuild the index after bus membership changes.

Does NOT
--------
- Own Bus objects.
- Register/remove buses.
- Build Y-bus.
- Perform topology analysis.
- Perform numerical calculations.
- Define electrical meaning.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any


class BusIndex:
    """
    Deterministic mapping from canonical Bus IDs to matrix indices.

    The Network remains the owner of canonical bus membership.
    """

    def __init__(
        self,
        network: Any,
    ) -> None:
        if network is None:
            raise ValueError(
                "BusIndex requires a Network."
            )

        self._network = network
        self.mapping: dict[Any, int] = {}

    # ============================================================
    # REBUILD
    # ============================================================

    def rebuild(self) -> dict[Any, int]:
        """
        Rebuild the complete deterministic bus index.

        Index order is the current order of Network.buses.
        """

        index: dict[Any, int] = {}

        for position, bus in enumerate(
            self._network.buses
        ):

            if not hasattr(bus, "id"):
                raise TypeError(
                    "Every bus must provide an 'id' attribute."
                )

            if bus.id in index:
                raise ValueError(
                    f"Duplicate bus ID: {bus.id}"
                )

            index[bus.id] = position

        self.mapping = index

        return self.mapping

    # ============================================================
    # LOOKUP
    # ============================================================

    def get(
        self,
        bus_or_id: Any,
    ) -> int:
        """
        Return the numerical matrix index for a Bus or Bus ID.
        """

        if not self.mapping:
            self.rebuild()

        bus_id = (
            bus_or_id.id
            if hasattr(bus_or_id, "id")
            else bus_or_id
        )

        try:
            return self.mapping[bus_id]

        except KeyError as exc:
            raise KeyError(
                f"Unknown network bus: {bus_id}"
            ) from exc

    # ------------------------------------------------------------

    def contains(
        self,
        bus_or_id: Any,
    ) -> bool:
        """
        Return whether a Bus or Bus ID exists in the current index.
        """

        if not self.mapping:
            self.rebuild()

        bus_id = (
            bus_or_id.id
            if hasattr(bus_or_id, "id")
            else bus_or_id
        )

        return bus_id in self.mapping

    # ============================================================
    # INVALIDATION
    # ============================================================

    def clear(self) -> None:
        """
        Clear the derived mapping.

        This does not modify Network membership.
        """

        self.mapping.clear()
