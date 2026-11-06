# ============================================================
# File: core/network/indexing.py
# GridForge V2 — Network Bus Indexing
# Author: Subhendu Mishra
# ============================================================

"""
Deterministic bus indexing for GridForge Network.

The BusIndex is the single owner of:

    bus.id -> matrix index

It does not own Bus objects and does not perform topology or
electrical validation.

The index is derived state and therefore becomes invalid whenever
network bus membership changes.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable


class BusIndex:
    """
    Canonical deterministic bus-ID to matrix-index mapping.
    """

    def __init__(self) -> None:
        self._mapping: Dict[Any, int] = {}
        self._valid = False

    # ============================================================
    # STATE
    # ============================================================

    @property
    def valid(self) -> bool:
        """
        Return True when the mapping corresponds to the current
        network bus collection.
        """
        return self._valid

    # ------------------------------------------------------------

    @property
    def mapping(self) -> Dict[Any, int]:
        """
        Return a defensive copy of the current mapping.

        An invalid mapping is returned as an empty mapping.
        """
        if not self._valid:
            return {}

        return dict(self._mapping)

    # ============================================================
    # INVALIDATION
    # ============================================================

    def invalidate(self) -> None:
        """
        Invalidate the current derived index.
        """
        self._mapping.clear()
        self._valid = False

    # ============================================================
    # BUILD
    # ============================================================

    def rebuild(
        self,
        buses: Iterable[Any],
    ) -> Dict[Any, int]:
        """
        Rebuild the index from the authoritative Network bus
        collection.
        """

        mapping: Dict[Any, int] = {}

        for position, bus in enumerate(buses):

            if not hasattr(bus, "id"):
                raise TypeError(
                    "Every bus must provide an 'id' attribute."
                )

            if bus.id in mapping:
                raise ValueError(
                    f"Duplicate bus ID: {bus.id}"
                )

            mapping[bus.id] = position

        self._mapping = mapping
        self._valid = True

        return dict(self._mapping)

    # ------------------------------------------------------------

    def ensure(
        self,
        buses: Iterable[Any],
    ) -> Dict[Any, int]:
        """
        Return a valid index, rebuilding it when necessary.
        """

        if not self._valid:
            return self.rebuild(buses)

        return dict(self._mapping)

    # ============================================================
    # LOOKUP
    # ============================================================

    def get(
        self,
        bus_id: Any,
    ) -> int:
        """
        Return the matrix index for a bus ID.
        """

        if not self._valid:
            raise RuntimeError(
                "Bus index is invalid; rebuild it first."
            )

        try:
            return self._mapping[bus_id]

        except KeyError as exc:
            raise KeyError(
                f"Unknown bus ID: {bus_id}"
            ) from exc

    # ------------------------------------------------------------

    def __contains__(
        self,
        bus_id: Any,
    ) -> bool:
        """
        Return whether a bus ID exists in the valid index.
        """

        return (
            self._valid
            and bus_id in self._mapping
        )

    # ------------------------------------------------------------

    def __len__(self) -> int:
        """
        Return the number of indexed buses.
        """

        return len(self._mapping) if self._valid else 0
