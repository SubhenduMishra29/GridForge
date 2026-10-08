# ============================================================
# File: core/network/junction.py
# GridForge V2 — Core Junction Identity
# Author: Subhendu Mishra
# ============================================================

"""First-class topology Junction identity for the Core Network layer."""

from __future__ import annotations

from typing import Any


class Junction:
    """Immutable-identity topology primitive owned by exactly one Network.

    Junction is deliberately not an ElectricalObject. It has no electrical
    equipment parameters, terminals, endpoint references, or presentation
    state. Its only public identity is the canonical junction_id.
    """

    __slots__ = ("_junction_id", "_gridforge_network_token")

    def __init__(self, junction_id: str) -> None:
        if not isinstance(junction_id, str):
            raise TypeError("junction_id must be a string.")
        canonical_id = junction_id.strip()
        if not canonical_id:
            raise ValueError("junction_id must be a non-empty string.")
        object.__setattr__(self, "_junction_id", canonical_id)
        object.__setattr__(self, "_gridforge_network_token", None)

    @property
    def junction_id(self) -> str:
        return self._junction_id

    @property
    def id(self) -> str:
        return self._junction_id

    def _bind_network(self, token: object) -> None:
        if token is None:
            raise ValueError("Junction network binding token cannot be None.")
        current = self._gridforge_network_token
        if current is not None and current is not token:
            raise ValueError(f"Junction {self.junction_id!r} is already owned by another Network.")
        object.__setattr__(self, "_gridforge_network_token", token)

    def _unbind_network(self, token: object) -> None:
        if self._gridforge_network_token is token:
            object.__setattr__(self, "_gridforge_network_token", None)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"_junction_id", "junction_id", "id"}:
            raise AttributeError("Junction identity is immutable after construction.")
        if name == "_gridforge_network_token":
            raise AttributeError("Junction network ownership is registry-controlled.")
        raise AttributeError("Junction is immutable and exposes no mutable state.")

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if type(self) is not type(other):
            return NotImplemented
        return self.junction_id == other.junction_id  # type: ignore[attr-defined]

    def __hash__(self) -> int:
        return hash((Junction, self.junction_id))

    def __repr__(self) -> str:
        return f"<Junction junction_id={self.junction_id!r}>"



__all__ = ["Junction"]
