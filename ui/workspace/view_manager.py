# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/workspace/view_manager.py
#
# Purpose:
#     Manages logical workspace views.
#
# Architectural Role:
#     Connects documents to visual view identities without
#     directly constructing Qt widgets.
#
# Responsibilities:
#     - register views;
#     - associate views with documents;
#     - activate views;
#     - maintain viewport state;
#     - close views.
#
# Does NOT:
#     - create QGraphicsView;
#     - create QGraphicsScene;
#     - perform rendering.
#
# ============================================================

"""
GridForge V2 — View Manager.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from .viewport_state import ViewportState


@dataclass
class ViewRecord:
    """
    Logical representation of one workspace view.
    """

    view_id: str
    document_id: str
    view_type: str = "sld"
    viewport: ViewportState = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.viewport is None:
            self.viewport = ViewportState()


class ViewManager:
    """
    Manages logical views in the workspace.
    """

    def __init__(self) -> None:
        self._views: Dict[
            str,
            ViewRecord,
        ] = {}

        self._active_view_id: Optional[
            str
        ] = None

    @property
    def active_view_id(self) -> Optional[str]:
        return self._active_view_id

    @property
    def active_view(self) -> Optional[ViewRecord]:
        if self._active_view_id is None:
            return None

        return self._views.get(
            self._active_view_id
        )

    def register(
        self,
        view: ViewRecord,
    ) -> None:
        if view.view_id in self._views:
            raise ValueError(
                f"View already registered: "
                f"{view.view_id}"
            )

        self._views[view.view_id] = view

        if self._active_view_id is None:
            self.activate(view.view_id)

    def unregister(
        self,
        view_id: str,
    ) -> ViewRecord:
        view = self._views.pop(
            view_id,
            None,
        )

        if view is None:
            raise KeyError(view_id)

        if self._active_view_id == view_id:
            self._active_view_id = None

            if self._views:
                self._active_view_id = next(
                    iter(self._views)
                )

        return view

    def get(
        self,
        view_id: str,
    ) -> Optional[ViewRecord]:
        return self._views.get(view_id)

    def require(
        self,
        view_id: str,
    ) -> ViewRecord:
        view = self.get(view_id)

        if view is None:
            raise KeyError(view_id)

        return view

    def activate(
        self,
        view_id: str,
    ) -> ViewRecord:
        view = self.require(view_id)

        self._active_view_id = view_id

        return view

    def views(
        self,
    ) -> Iterable[ViewRecord]:
        return tuple(
            self._views.values()
        )

    def views_for_document(
        self,
        document_id: str,
    ) -> tuple[ViewRecord, ...]:
        return tuple(
            view
            for view in self._views.values()
            if view.document_id
            == document_id
        )

    def clear(self) -> None:
        self._views.clear()
        self._active_view_id = None

    def __len__(self) -> int:
        return len(self._views)
