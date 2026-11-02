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

    def matches_study_state(self, other: object) -> bool:
        """Whether two snapshots describe the same numerical study input state.

        Persistence bookkeeping and SLD presentation revisions are deliberately
        excluded: neither changes the committed electrical model/topology consumed
        by numerical study preparation. Project identity and activation generation
        are checked by the Application read boundary alongside this comparison.
        """
        return (
            isinstance(other, ProjectRevision)
            and self.model_revision == other.model_revision
            and self.topology_revision == other.topology_revision
        )

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
