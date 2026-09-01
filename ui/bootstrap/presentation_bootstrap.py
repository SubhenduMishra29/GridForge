# ============================================================
# File: ui/bootstrap/presentation_bootstrap.py
# GridForge V2 — Presentation Bootstrap Boundary
# Author: Subhendu Mishra
# ============================================================
"""Compose presentation services from an application context.

This boundary deliberately does not own application services or Core state.
Qt widgets may be attached by the concrete UI shell without moving application
responsibility into the presentation layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from application.application_context import ApplicationContext


@dataclass
class PresentationBootstrap:
    """Expose application-owned services to presentation composition."""

    application_context: ApplicationContext
    shell: Any = None

    @property
    def command_dispatcher(self):
        return self.application_context.command_dispatcher

    @property
    def ui_update_bus(self):
        return self.application_context.ui_update_bus

    def attach_shell(self, shell: Any) -> None:
        """Attach the concrete presentation shell without taking ownership of it."""
        self.shell = shell

    def detach_shell(self) -> Any:
        shell = self.shell
        self.shell = None
        return shell


__all__ = ["PresentationBootstrap"]
