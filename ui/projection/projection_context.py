# ============================================================
# File: ui/projection/projection_context.py
# GridForge V2 — Projection Context
# Author: Subhendu Mishra
# ============================================================
"""Read-only context supplied to UI projections.

The context carries authoritative model objects or lookup services needed by
projections without making the projection layer responsible for mutation.
"""

from __future__ import annotations

from typing import Any, Callable


class ProjectionContext:
    """Provide controlled model lookup to a projection."""

    def __init__(self, resolver: Callable[[str], Any | None]) -> None:
        if not callable(resolver):
            raise TypeError("ProjectionContext resolver must be callable")
        self._resolver = resolver

    def resolve(self, object_id: str) -> Any | None:
        """Resolve a stable Core object ID through the supplied read boundary."""
        return self._resolver(object_id)
