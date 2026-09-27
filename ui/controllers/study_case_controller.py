# ============================================================
# File: ui/controllers/study_case_controller.py
# GridForge V2 — Study Case Interaction Boundary
# Author: Subhendu Mishra
# ============================================================

"""UI interaction boundary for running Application-owned Study Cases."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID
from typing import Any


class StudyCaseController:
    """Translate Study Cases UI intent into the Application study boundary."""

    def __init__(
        self,
        *,
        application: Any,
        error_handler: Callable[[BaseException], object] | None = None,
    ) -> None:
        if application is None:
            raise ValueError("application is required.")
        if not callable(getattr(application, "study_case", None)):
            raise TypeError("application must expose study_case().")
        if not callable(getattr(application, "execute_study_case", None)):
            raise TypeError("application must expose execute_study_case().")
        self._application = application
        self._error_handler = error_handler

    def run_study(self, study_id: UUID) -> object | None:
        """Run the selected structured Study Case through Application only."""
        if not isinstance(study_id, UUID):
            try:
                study_id = UUID(str(study_id))
            except (TypeError, ValueError) as exc:
                return self._handle_error(ValueError("Selected Study Case identity is invalid."), cause=exc)

        try:
            # Resolve the structured definition before execution. No display
            # string is interpreted and no Core state is accessed here.
            self._application.study_case(study_id)
            return self._application.execute_study_case(study_id)
        except BaseException as exc:
            return self._handle_error(exc)

    def _handle_error(self, error: BaseException, *, cause: BaseException | None = None) -> None:
        if self._error_handler is not None:
            self._error_handler(error)
            return None
        if cause is not None:
            raise error from cause
        raise error


__all__ = ["StudyCaseController"]
