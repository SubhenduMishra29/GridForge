# ============================================================
# File: ui/lifecycle/ui_lifecycle.py
# GridForge V2 — Presentation UI Lifecycle
# Author: Subhendu Mishra
# ============================================================
"""Explicit presentation lifecycle coordinator.

Architecture boundary
---------------------
UI lifecycle is deliberately explicit and independent from Python/Qt object
 destruction. Bootstrap creates the coordinator and supplies already-created
presentation services. The coordinator orders startup and shutdown without
owning Core engineering truth.

Lifecycle:
    bootstrap -> shell -> workspace -> document/view activation
    -> close -> workspace teardown -> presentation cleanup

This module does not create domain models, execute electrical operations, or
rely on garbage collection as a lifecycle mechanism.
"""

from __future__ import annotations

from enum import Enum
from typing import Callable


class UILifecyclePhase(str, Enum):
    """Explicit presentation lifecycle phases."""

    NEW = "new"
    BOOTSTRAPPED = "bootstrapped"
    SHELL_READY = "shell_ready"
    WORKSPACE_READY = "workspace_ready"
    DOCUMENT_READY = "document_ready"
    CLOSING = "closing"
    CLOSED = "closed"


class UILifecycle:
    """Coordinate deterministic startup and shutdown callbacks."""

    def __init__(
        self,
        *,
        bootstrap: Callable[[], None] | None = None,
        shell_ready: Callable[[], None] | None = None,
        workspace_ready: Callable[[], None] | None = None,
        document_ready: Callable[[], None] | None = None,
        document_close: Callable[[], None] | None = None,
        workspace_teardown: Callable[[], None] | None = None,
        cleanup: Callable[[], None] | None = None,
    ) -> None:
        self._callbacks = {
            UILifecyclePhase.BOOTSTRAPPED: bootstrap,
            UILifecyclePhase.SHELL_READY: shell_ready,
            UILifecyclePhase.WORKSPACE_READY: workspace_ready,
            UILifecyclePhase.DOCUMENT_READY: document_ready,
        }
        self._document_close = document_close
        self._workspace_teardown = workspace_teardown
        self._cleanup = cleanup
        self._phase = UILifecyclePhase.NEW

    @property
    def phase(self) -> UILifecyclePhase:
        return self._phase

    @property
    def closed(self) -> bool:
        return self._phase is UILifecyclePhase.CLOSED

    def start(self) -> UILifecyclePhase:
        """Run the ordered bootstrap/shell/workspace stages."""
        self._require_phase(UILifecyclePhase.NEW)
        self._advance(UILifecyclePhase.BOOTSTRAPPED)
        self._advance(UILifecyclePhase.SHELL_READY)
        self._advance(UILifecyclePhase.WORKSPACE_READY)
        return self._phase

    def activate_document(self) -> UILifecyclePhase:
        """Mark the document/view activation boundary explicitly."""
        self._require_phase(UILifecyclePhase.WORKSPACE_READY)
        self._advance(UILifecyclePhase.DOCUMENT_READY)
        return self._phase

    def close_document(self) -> UILifecyclePhase:
        """Close the active document/view before workspace teardown."""
        if self._phase is not UILifecyclePhase.DOCUMENT_READY:
            return self._phase
        if self._document_close is not None:
            self._document_close()
        self._phase = UILifecyclePhase.WORKSPACE_READY
        return self._phase

    def close(self) -> UILifecyclePhase:
        """Run deterministic presentation teardown exactly once."""
        if self._phase is UILifecyclePhase.CLOSED:
            return self._phase
        if self._phase is UILifecyclePhase.NEW:
            self._phase = UILifecyclePhase.CLOSED
            return self._phase

        self._phase = UILifecyclePhase.CLOSING
        self.close_document()
        if self._workspace_teardown is not None:
            self._workspace_teardown()
        if self._cleanup is not None:
            self._cleanup()
        self._phase = UILifecyclePhase.CLOSED
        return self._phase

    def _advance(self, phase: UILifecyclePhase) -> None:
        callback = self._callbacks[phase]
        if callback is not None:
            callback()
        self._phase = phase

    def _require_phase(self, expected: UILifecyclePhase) -> None:
        if self._phase is not expected:
            raise RuntimeError(
                f"Lifecycle phase must be {expected.value!r}; "
                f"current phase is {self._phase.value!r}."
            )


__all__ = ["UILifecycle", "UILifecyclePhase"]
