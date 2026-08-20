# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/workspace/workspace.py
#
# Purpose:
#     Represents one GridForge UI workspace.
#
# Architectural Role:
#     Provides the composition boundary between documents and
#     views.
#
# Responsibilities:
#     - own document manager;
#     - own view manager;
#     - provide active document/view access;
#     - provide workspace lifecycle.
#
# Does NOT:
#     - create the MainWindow;
#     - construct Qt widgets;
#     - render SLD objects;
#     - own Core network state.
#
# ============================================================

"""
GridForge V2 — Workspace.
"""

from __future__ import annotations

from typing import Optional

from .document import Document
from .document_manager import DocumentManager
from .view_manager import ViewManager, ViewRecord


class Workspace:
    """
    Logical GridForge UI workspace.

    One workspace can contain multiple documents and multiple views.
    """

    def __init__(
        self,
        workspace_id: str,
        name: str = "Default Workspace",
    ) -> None:
        if not workspace_id:
            raise ValueError(
                "workspace_id must not be empty"
            )

        if not name:
            raise ValueError(
                "name must not be empty"
            )

        self._workspace_id = str(
            workspace_id
        )
        self._name = str(name)

        self._documents = DocumentManager()
        self._views = ViewManager()

    @property
    def workspace_id(self) -> str:
        return self._workspace_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def documents(self) -> DocumentManager:
        return self._documents

    @property
    def views(self) -> ViewManager:
        return self._views

    @property
    def active_document(self) -> Optional[Document]:
        return self._documents.active_document

    @property
    def active_view(self) -> Optional[ViewRecord]:
        return self._views.active_view

    def add_document(
        self,
        document: Document,
    ) -> None:
        self._documents.register(
            document
        )

    def remove_document(
        self,
        document_id: str,
    ) -> Document:
        views = self._views.views_for_document(
            document_id
        )

        for view in views:
            self._views.unregister(
                view.view_id
            )

        return self._documents.unregister(
            document_id
        )

    def add_view(
        self,
        view: ViewRecord,
    ) -> None:
        if self._documents.get(
            view.document_id
        ) is None:
            raise KeyError(
                f"Document does not exist: "
                f"{view.document_id}"
            )

        self._views.register(view)

    def close(self) -> None:
        """
        Close the workspace logically.

        Actual Qt widget destruction is performed by the UI composition
        layer, not by this object.
        """
        self._views.clear()
        self._documents.clear()
