# ============================================================
# File: ui/projection/projection_registry.py
# GridForge V2 — Projection Registry
# Author: Subhendu Mishra
# ============================================================
"""Registry for UI projections keyed by stable Core object identity.

Responsibilities:
    - register and resolve projections by Core object ID;
    - enforce explicit projection-domain ownership;
    - expose read-only domain-scoped enumeration;
    - remove projections cleanly.

Boundary rules:
    - does not mutate Core objects;
    - does not create Qt graphics items;
    - does not own rendering or layout policy.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class ProjectionDomain(str, Enum):
    """Authoritative namespaces for presentation projection ownership."""

    NETWORK = "network"
    PROTECTION = "protection"


class ProjectionRegistry:
    """Own the mapping from stable Core IDs to UI projections and their domains."""

    def __init__(self) -> None:
        self._projections: dict[str, Any] = {}
        self._domains: dict[str, ProjectionDomain] = {}

    def register(self, projection: Any, domain: ProjectionDomain) -> None:
        """Register a projection under one explicit presentation domain."""
        if not isinstance(domain, ProjectionDomain):
            raise TypeError("domain must be a ProjectionDomain")

        object_id = getattr(projection, "object_id", None)
        if not isinstance(object_id, str) or not object_id:
            raise ValueError("Projection must provide a non-empty object_id")

        if object_id in self._projections:
            raise ValueError(
                f"Projection already registered for Core object ID {object_id!r}"
            )

        self._projections[object_id] = projection
        self._domains[object_id] = domain

    def get(self, object_id: str) -> Any | None:
        """Return the projection for a Core object ID, if registered."""
        return self._projections.get(object_id)

    def domain_of(self, object_id: str) -> ProjectionDomain | None:
        """Return the owning presentation domain for a registered projection."""
        return self._domains.get(object_id)

    def values(self, domain: ProjectionDomain) -> tuple[Any, ...]:
        """Return a read-only snapshot of projections owned by one domain."""
        if not isinstance(domain, ProjectionDomain):
            raise TypeError("domain must be a ProjectionDomain")
        return tuple(
            projection
            for object_id, projection in self._projections.items()
            if self._domains[object_id] is domain
        )

    def object_ids(self, domain: ProjectionDomain) -> tuple[str, ...]:
        """Return stable Core object IDs owned by one presentation domain."""
        if not isinstance(domain, ProjectionDomain):
            raise TypeError("domain must be a ProjectionDomain")
        return tuple(
            object_id
            for object_id in self._projections
            if self._domains[object_id] is domain
        )

    def contains(self, object_id: str, domain: ProjectionDomain | None = None) -> bool:
        """Return whether an object is registered, optionally in one domain."""
        if domain is not None and not isinstance(domain, ProjectionDomain):
            raise TypeError("domain must be a ProjectionDomain or None")
        return (
            object_id in self._projections
            and (domain is None or self._domains[object_id] is domain)
        )

    def remove(self, object_id: str, domain: ProjectionDomain | None = None) -> Any | None:
        """Remove and return a projection when it belongs to the requested domain."""
        if domain is not None and not isinstance(domain, ProjectionDomain):
            raise TypeError("domain must be a ProjectionDomain or None")
        if object_id not in self._projections:
            return None
        if domain is not None and self._domains[object_id] is not domain:
            return None

        self._domains.pop(object_id, None)
        return self._projections.pop(object_id, None)

    def clear(self, domain: ProjectionDomain | None = None) -> None:
        """Remove all projections, or only projections in one domain."""
        if domain is not None and not isinstance(domain, ProjectionDomain):
            raise TypeError("domain must be a ProjectionDomain or None")
        for object_id in self.object_ids(domain) if domain is not None else tuple(self._projections):
            self._domains.pop(object_id, None)
            self._projections.pop(object_id, None)


__all__ = ["ProjectionDomain", "ProjectionRegistry"]
