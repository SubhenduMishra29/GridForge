# ============================================================
# File: core/network/junction_registry.py
# GridForge V2 — Authoritative Junction Registry
# Author: Subhendu Mishra
# ============================================================

"""Authoritative Network membership registry for topology Junctions."""

from __future__ import annotations

from typing import Iterator

from .junction import Junction


class JunctionRegistry:
    """Own canonical Junction membership independently of NetworkRegistry."""

    def __init__(self) -> None:
        self._junctions: dict[str, Junction] = {}
        self._network_token = object()
        self._network = None

    def _bind_network(self, network: object) -> None:
        if network is None:
            raise ValueError("JunctionRegistry network owner cannot be None.")
        if self._network is not None and self._network is not network:
            raise ValueError("JunctionRegistry belongs to another Network.")
        self._network = network

    @staticmethod
    def _canonical_id(junction: Junction) -> str:
        if not isinstance(junction, Junction):
            raise TypeError(f"Expected Junction; received {type(junction).__name__}.")
        junction_id = junction.junction_id
        if not isinstance(junction_id, str) or not junction_id.strip():
            raise ValueError("Junction identity must be a non-empty string.")
        if junction_id != junction_id.strip():
            raise ValueError("Junction identity must already be canonical.")
        return junction_id

    @property
    def snapshot(self) -> tuple[Junction, ...]:
        return tuple(self._junctions[key] for key in sorted(self._junctions))

    def __iter__(self) -> Iterator[Junction]:
        return iter(self.snapshot)

    def __len__(self) -> int:
        return len(self._junctions)

    def add(self, junction: Junction) -> None:
        junction_id = self._canonical_id(junction)
        existing = self._junctions.get(junction_id)
        if existing is not None:
            raise ValueError(f"Duplicate canonical Junction ID: {junction_id}")
        owner = junction._gridforge_network_token
        if owner is not None and owner is not self._network_token:
            raise ValueError(f"Junction {junction_id!r} is already owned by another Network.")
        self._junctions[junction_id] = junction
        try:
            junction._bind_network(self._network_token)
        except Exception:
            del self._junctions[junction_id]
            raise

    def remove(self, junction: Junction) -> None:
        junction_id = self._canonical_id(junction)
        registered = self._junctions.get(junction_id)
        if registered is not junction:
            raise KeyError(f"Junction is not registered: {junction_id}")
        del self._junctions[junction_id]
        junction._unbind_network(self._network_token)

    def get(self, junction_id: str) -> Junction:
        if not isinstance(junction_id, str) or not junction_id.strip():
            raise ValueError("junction_id must be a non-empty string.")
        canonical_id = junction_id.strip()
        try:
            return self._junctions[canonical_id]
        except KeyError as exc:
            raise KeyError(f"Junction is not registered: {canonical_id}") from exc

    def contains(self, junction_id: str) -> bool:
        if not isinstance(junction_id, str) or not junction_id.strip():
            return False
        return junction_id.strip() in self._junctions



__all__ = ["JunctionRegistry"]
