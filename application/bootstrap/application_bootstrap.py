# ============================================================
# File: application/bootstrap/application_bootstrap.py
# GridForge V2 — Application Bootstrap
# Author: Subhendu Mishra
# ============================================================
"""Framework-neutral application composition entry point."""

from __future__ import annotations

from typing import Any

from application.application_context import ApplicationContext


class ApplicationBootstrap:
    """Create the application context without constructing UI objects."""

    def __init__(self, network: Any) -> None:
        self._context = ApplicationContext.create(network)

    @property
    def context(self) -> ApplicationContext:
        return self._context

    def shutdown(self) -> None:
        """Release presentation subscriptions owned by the application context."""
        self._context.ui_update_bus.clear()


__all__ = ["ApplicationBootstrap"]
