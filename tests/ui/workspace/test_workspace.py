# ============================================================
# File: tests/ui/workspace/test_workspace.py
# GridForge V2 — Workspace Tests
# Author: Subhendu Mishra
# ============================================================

from ui.workspace.document import Document
from ui.workspace.workspace import Workspace


def test_workspace_owns_document_and_view_managers() -> None:
    workspace = Workspace("WS-001", "Engineering")

    assert workspace.workspace_id == "WS-001"
    assert workspace.active_document is None
    assert workspace.active_view is None


def test_workspace_registers_document_through_document_manager() -> None:
    workspace = Workspace("WS-001")
    document = Document("DOC-001", "sld", "Main SLD")

    workspace.add_document(document)

    assert workspace.documents.get("DOC-001") is document
    assert workspace.active_document is document


def test_workspace_close_clears_logical_views_and_documents() -> None:
    workspace = Workspace("WS-001")
    workspace.add_document(Document("DOC-001", "sld"))

    workspace.close()

    assert workspace.active_document is None
    assert workspace.active_view is None
