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

from ui.sld.sld_read_synchronizer import SLDReadSynchronizer
from ui.workspace.workspace_manager import WorkspaceManager


@dataclass
class PresentationBootstrap:
    """Own presentation composition and its explicit Application boundary."""

    workspace_manager: WorkspaceManager
    application: Any = None
    sld_read_synchronizer: SLDReadSynchronizer | None = None
    shell: Any = None

    @classmethod
    def create(
        cls,
        workspace_manager: WorkspaceManager | None = None,
        application: Any = None,
        sld_read_synchronizer: SLDReadSynchronizer | None = None,
    ) -> "PresentationBootstrap":
        """Compose presentation infrastructure with injected Application/read boundaries."""
        bootstrap = cls(
            workspace_manager=workspace_manager or WorkspaceManager(),
            application=application,
            sld_read_synchronizer=sld_read_synchronizer,
        )
        bootstrap._synchronize_application_boundary()
        return bootstrap

    def attach_application(self, application: Any) -> None:
        """Attach the Application facade without taking ownership of Core state."""
        if application is None:
            raise TypeError("application must not be None")
        self.application = application
        self._synchronize_application_boundary()

    def detach_application(self) -> Any:
        """Detach and return the Application facade."""
        application = self.application
        self.application = None
        self._synchronize_application_boundary()
        return application

    def attach_sld_read_synchronizer(self, synchronizer: SLDReadSynchronizer) -> None:
        """Attach the SLD read synchronizer and bind the current Application facade."""
        if not isinstance(synchronizer, SLDReadSynchronizer):
            raise TypeError("synchronizer must be an SLDReadSynchronizer")
        self.sld_read_synchronizer = synchronizer
        self._synchronize_application_boundary()

    def detach_sld_read_synchronizer(self) -> SLDReadSynchronizer | None:
        """Detach and return the SLD read synchronizer."""
        synchronizer = self.sld_read_synchronizer
        if synchronizer is not None:
            synchronizer.detach_application()
        self.sld_read_synchronizer = None
        return synchronizer

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

    def _synchronize_application_boundary(self) -> None:
        """Propagate the injected Application facade into read-only SLD composition."""
        if self.sld_read_synchronizer is None:
            return
        if self.application is None:
            self.sld_read_synchronizer.detach_application()
            return
        self.sld_read_synchronizer.attach_application(self.application)


__all__ = ["PresentationBootstrap"]
