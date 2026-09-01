# ============================================================
# File: tests/ui/workspace/test_workspace_manager.py
# GridForge V2 — Workspace Manager Tests
# Author: Subhendu Mishra
# ============================================================

import pytest

from ui.workspace.panel_area import PanelArea
from ui.workspace.workspace_definition import WorkspaceDefinition, WorkspacePlacement
from ui.workspace.workspace_layout import WorkspaceLayout
from ui.workspace.workspace_manager import WorkspaceManager


def _definition(workspace_id: str) -> WorkspaceDefinition:
    return WorkspaceDefinition(
        workspace_id=workspace_id,
        title="Engineering",
        placements=(WorkspacePlacement("sld", PanelArea.CENTER),),
    )


def test_prepare_activate_does_not_change_authoritative_state() -> None:
    definition = _definition("WS-001")
    manager = WorkspaceManager({"WS-001": definition})

    candidate = manager.prepare_activate("WS-001")

    assert candidate.workspace_id == "WS-001"
    assert manager.active_workspace_id is None
    assert manager.state is None


def test_commit_changes_authoritative_logical_state() -> None:
    definition = _definition("WS-001")
    manager = WorkspaceManager({"WS-001": definition})

    candidate = manager.prepare_activate("WS-001")
    committed = manager.commit(candidate)

    assert committed is candidate
    assert manager.active_workspace_id == "WS-001"
    assert manager.state is candidate


def test_failed_external_realization_can_leave_state_uncommitted() -> None:
    manager = WorkspaceManager({"WS-001": _definition("WS-001")})
    candidate = manager.prepare_activate("WS-001")

    # Simulate the external realization phase failing before commit().
    try:
        raise RuntimeError("simulated realization failure")
    except RuntimeError:
        pass

    assert candidate.workspace_id == "WS-001"
    assert manager.active_workspace_id is None
    assert manager.state is None


def test_prepare_layout_requires_active_workspace() -> None:
    manager = WorkspaceManager({"WS-001": _definition("WS-001")})
    layout = WorkspaceLayout.from_placements(
        [WorkspacePlacement("sld", PanelArea.CENTER)]
    )

    with pytest.raises(RuntimeError):
        manager.prepare_layout(layout)
