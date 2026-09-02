# ============================================================
# File: ui/workspace/workspace.py
# GridForge V2 — Logical Workspace
# Author: Subhendu Mishra
# ============================================================
"""Logical UI Workspace composition boundary.

Project is the persistent container, Document is an open/editable
representation within that project, and Workspace is the active UI context.
This object owns neither electrical truth nor Qt realization.
"""

from __future__ import annotations

from typing import Optional

from .document import Document
from .document_manager import DocumentManager
from .view_manager import ViewManager, ViewRecord


class Workspace:
    """Logical GridForge UI workspace containing documents and views."""

    def __init__(self, workspace_id: str, name: str = "Default Workspace", *, project_id: str | None = None) -> None:
        if not workspace_id:
            raise ValueError("workspace_id must not be empty")
        if not name:
            raise ValueError("name must not be empty")
        if project_id is not None and not str(project_id).strip():
            raise ValueError("project_id must not be empty")

        self._workspace_id = str(workspace_id)
        self._name = str(name)
        self._project_id = str(project_id) if project_id is not None else None
        self._documents = DocumentManager()
        self._views = ViewManager()

    @property
    def workspace_id(self) -> str:
        return self._workspace_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def project_id(self) -> str | None:
        return self._project_id

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

    def add_document(self, document: Document) -> None:
        if self._project_id is not None and document.project_id not in (None, self._project_id):
            raise ValueError("Document belongs to a different project")
        self._documents.register(document)

    def remove_document(self, document_id: str) -> Document:
        views = self._views.views_for_document(document_id)
        for view in views:
            self._views.unregister(view.view_id)
        return self._documents.unregister(document_id)

    def add_view(self, view: ViewRecord) -> None:
        if self._documents.get(view.document_id) is None:
            raise KeyError(f"Document does not exist: {view.document_id}")
        self._views.register(view)

    def close(self) -> None:
        self._views.clear()
        self._documents.clear()


__all__ = ["Workspace"]
