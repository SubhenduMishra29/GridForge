# ============================================================
# File: tests/ui/workspace/test_workspace.py
# GridForge V2 — Workspace Tests
# Author: Subhendu Mishra
# ============================================================

from ui.workspace.workspace import Workspace


def test_workspace_has_stable_identity_and_active_document() -> None:
    document = object()
    workspace = Workspace("WS-001", document)

    assert workspace.workspace_id == "WS-001"
    assert workspace.active_document is document


def test_workspace_can_track_active_surface_without_core_mutation() -> None:
    workspace = Workspace("WS-001", object())

    workspace.set_active_surface("sld")

    assert workspace.active_surface == "sld"
