"""
GridForge V2 — Workspace State.

Stores the current logical workspace state.

Qt-independent.
"""
#ui/workspace/workspace_state.py
from __future__ import annotations

from dataclasses import dataclass

from .workspace_layout import WorkspaceLayout


@dataclass(frozen=True, slots=True)
class WorkspaceState:
    """
    Immutable current workspace state.
    """

    workspace_id: str
    layout: WorkspaceLayout

    def __post_init__(self) -> None:
        if not isinstance(self.workspace_id, str):
            raise TypeError(
                "workspace_id must be a string."
            )

        if not self.workspace_id.strip():
            raise ValueError(
                "workspace_id must not be empty."
            )

        if not isinstance(
            self.layout,
            WorkspaceLayout,
        ):
            raise TypeError(
                "layout must be a WorkspaceLayout."
            )


__all__ = [
    "WorkspaceState",
]
