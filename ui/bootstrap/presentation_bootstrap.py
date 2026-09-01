# ============================================================
# File: ui/bootstrap/presentation_bootstrap.py
# GridForge V2 — Presentation Bootstrap Boundary
# Author: Subhendu Mishra
# ============================================================
"""Compose presentation infrastructure without owning Application/Core.

The Presentation layer is intentionally independent of the Application layer
at this stage. A future Core↔UI integration boundary may be supplied through
explicit interfaces without moving Application responsibilities into UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ui.workspace.workspace_manager import WorkspaceManager


@dataclass
class PresentationBootstrap:
    """Own presentation composition and the active workspace infrastructure."""

    workspace_manager: WorkspaceManager
    shell: Any = None

    @classmethod
    def create(
        cls,
        workspace_manager: WorkspaceManager | None = None,
    ) -> "PresentationBootstrap":
        """Compose presentation infrastructure without an Application dependency."""
        return cls(
            workspace_manager=workspace_manager or WorkspaceManager(),
        )

    def attach_shell(self, shell: Any) -> None:
        """Attach the concrete presentation shell without taking ownership of it."""
        self.shell = shell

    def detach_shell(self) -> Any:
        """Detach and return the current presentation shell."""
        shell = self.shell
        self.shell = None
        return shell


__all__ = ["PresentationBootstrap"]
