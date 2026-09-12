# ============================================================
# File: core/application/revision.py
# GridForge V2 — Immutable Project Revision Snapshot
# Author: Subhendu Mishra
# ============================================================

"""Immutable revision state exposed by the Application layer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProjectRevision:
    """Immutable revision counters for one active project state."""

    model_revision: int = 0
    topology_revision: int = 0
    presentation_revision: int = 0
    persisted_revision: int = 0

    def __post_init__(self) -> None:
        for name in (
            "model_revision",
            "topology_revision",
            "presentation_revision",
            "persisted_revision",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"{name} must be an integer.")
            if value < 0:
                raise ValueError(f"{name} must not be negative.")


__all__ = ["ProjectRevision"]
