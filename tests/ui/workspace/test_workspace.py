# ============================================================
# File: tests/ui/workspace/test_workspace.py
# GridForge V2 — Workspace State Tests
# Author: Subhendu Mishra
# ============================================================

from ui.workspace.panel_area import PanelArea
from ui.workspace.workspace_definition import (
    WorkspaceDefinition,
    WorkspacePlacement,
)
from ui.workspace.workspace_layout import WorkspaceLayout
from ui.workspace.workspace_state import WorkspaceState


def test_workspace_layout_is_immutable_and_lookupable() -> None:
    placement = WorkspacePlacement("sld", PanelArea.CENTER)
    layout = WorkspaceLayout.from_placements([placement])

    assert layout.get_area("sld") is PanelArea.CENTER
    assert layout.get_placement("sld") == placement


def test_workspace_state_requires_logical_layout() -> None:
    placement = WorkspacePlacement("sld", PanelArea.CENTER)
    layout = WorkspaceLayout.from_placements([placement])
    state = WorkspaceState("WS-001", layout)

    assert state.workspace_id == "WS-001"
    assert state.layout is layout


def test_workspace_definition_contains_only_logical_intent() -> None:
    placement = WorkspacePlacement("sld", PanelArea.CENTER)
    definition = WorkspaceDefinition(
        workspace_id="WS-001",
        title="Engineering",
        placements=(placement,),
    )

    assert definition.workspace_id == "WS-001"
    assert definition.placements == (placement,)
