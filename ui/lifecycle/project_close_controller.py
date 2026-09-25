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
SaveAsPathProvider = Callable[[Any], str | None]


class ProjectCloseController:
    """Bridge the window-close request to the Application transition contract."""

    def __init__(
        self,
        *,
        application: Any,
        decision_provider: DecisionProvider,
        save_as_path_provider: SaveAsPathProvider | None = None,
    ) -> None:
        if application is None:
            raise TypeError("application is required.")
        if not callable(decision_provider):
            raise TypeError("decision_provider must be callable.")
        if save_as_path_provider is not None and not callable(save_as_path_provider):
            raise TypeError("save_as_path_provider must be callable or None.")
        self._application = application
        self._decision_provider = decision_provider
        self._save_as_path_provider = save_as_path_provider

    @property
    def application(self) -> Any:
        return self._application

    def request_close(self) -> bool:
        """Return True only after the complete project-close transition succeeds."""
        application = self._application
        if not bool(application.is_dirty):
            try:
                application.close_project()
                return True
            except Exception:
                return False

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

            if normalized is ProjectTransitionDecision.SAVE and (
                context is not None and context.path is None
            ):
                if self._save_as_path_provider is None:
                    return False
                path = self._save_as_path_provider(context)
                if not path:
                    # Save As cancellation is a transition cancellation:
                    # keep the dirty project active and do not call close.
                    return False
                application.save_project_as(path)

            # Named SAVE reaches Application.close_project() after persistence.
            # For unnamed SAVE, save_project_as() above marks the project clean,
            # so this close call does not attempt a second path-less save.
            application.close_project(decision=normalized)
            return True
        except Exception:
            # Any unresolved decision, Save As failure, or close-transition
            # failure must keep the window open and preserve the active project.
            return False


__all__ = ["DecisionProvider", "SaveAsPathProvider", "ProjectCloseController"]
