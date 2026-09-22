# ============================================================
# File: ui/lifecycle/project_close_controller.py
# GridForge V2 — Project Close Decision Boundary
# Author: Subhendu Mishra
# ============================================================

"""Resolve the UI side of dirty-project shutdown before Application close."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.application.project_transition import ProjectTransitionDecision, ProjectTransitionRequired


DecisionProvider = Callable[[Any], ProjectTransitionDecision | str]


class ProjectCloseController:
    """Bridge the window-close request to the Application transition contract."""

    def __init__(self, *, application: Any, decision_provider: DecisionProvider) -> None:
        if application is None:
            raise TypeError("application is required.")
        if not callable(decision_provider):
            raise TypeError("decision_provider must be callable.")
        self._application = application
        self._decision_provider = decision_provider

    @property
    def application(self) -> Any:
        return self._application

    def request_close(self) -> bool:
        """Return True only when Application project closure may proceed."""
        application = self._application
        if not bool(application.is_dirty):
            application.close_project()
            return True

        context = application.project_lifecycle.context
        try:
            decision = self._decision_provider(context)
            normalized = (
                decision
                if isinstance(decision, ProjectTransitionDecision)
                else ProjectTransitionDecision(str(decision).strip().lower())
            )
            if normalized is ProjectTransitionDecision.CANCEL:
                # CANCEL is a completed UI decision, not an exception path.
                return False
            application.close_project(decision=normalized)
            return True
        except ProjectTransitionRequired:
            # A provider that fails to resolve the required decision must
            # keep the window open rather than accidentally closing it.
            return False


__all__ = ["DecisionProvider", "ProjectCloseController"]
