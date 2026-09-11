# ============================================================
# File: ui/bootstrap/presentation_bootstrap.py
# GridForge V2 — Presentation Bootstrap Boundary
# Author: Subhendu Mishra
# ============================================================
"""Compose presentation infrastructure around an explicit Application boundary.

Presentation composition receives an Application facade from the outer
composition root. The UI does not construct Core services or reach into Core
state; read access is supplied by the Application facade.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ui.workspace.workspace_manager import WorkspaceManager


@dataclass
class PresentationBootstrap:
    """Own presentation composition and its explicit Application boundary."""

    workspace_manager: WorkspaceManager
    application: Any = None
    shell: Any = None

    @classmethod
    def create(
        cls,
        workspace_manager: WorkspaceManager | None = None,
        application: Any = None,
    ) -> "PresentationBootstrap":
        """Compose presentation infrastructure with an injected Application facade."""
        return cls(
            workspace_manager=workspace_manager or WorkspaceManager(),
            application=application,
        )

    def attach_application(self, application: Any) -> None:
        """Attach the Application facade without taking ownership of Core state."""
        if application is None:
            raise TypeError("application must not be None")
        self.application = application

    def detach_application(self) -> Any:
        """Detach and return the Application facade."""
        application = self.application
        self.application = None
        return application

    def require_application(self) -> Any:
        """Return the configured Application facade or fail at the boundary."""
        if self.application is None:
            raise RuntimeError("Presentation Application facade is not configured")
        return self.application

    def attach_shell(self, shell: Any) -> None:
        """Attach the concrete presentation shell without taking ownership of it."""
        self.shell = shell

    def detach_shell(self) -> Any:
        """Detach and return the current presentation shell."""
        shell = self.shell
        self.shell = None
        return shell


__all__ = ["PresentationBootstrap"]
