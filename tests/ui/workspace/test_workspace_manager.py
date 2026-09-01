# ============================================================
# File: tests/ui/workspace/test_workspace_manager.py
# GridForge V2 — Workspace Manager Tests
# Author: Subhendu Mishra
# ============================================================

from ui.workspace.workspace import Workspace
from ui.workspace.workspace_manager import WorkspaceManager


def test_manager_registers_and_activates_workspace() -> None:
    manager = WorkspaceManager()
    workspace = Workspace("WS-001", object())

    manager.register(workspace)
    manager.activate("WS-001")

    assert manager.active_workspace is workspace
    assert manager.get("WS-001") is workspace


def test_manager_can_remove_active_workspace() -> None:
    manager = WorkspaceManager()
    workspace = Workspace("WS-001", object())
    manager.register(workspace)
    manager.activate("WS-001")

    manager.remove("WS-001")

    assert manager.active_workspace is None
    assert manager.get("WS-001") is None
