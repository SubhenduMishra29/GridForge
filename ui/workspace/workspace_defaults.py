# ============================================================
# File: ui/workspace/workspace_defaults.py
# GridForge V2 — Canonical Workspace Defaults
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from .area import AreaDefinition
from .editor import EditorDefinition, SLD_EDITOR, CONTROL_EDITOR, PROTECTION_EDITOR, STUDY_EDITOR\nfrom .panel_area import PanelArea\nfrom .region import (CANVAS_REGION, DIAGNOSTICS_REGION, HEADER_REGION, OVERLAY_REGION, SIDEBAR_REGION, STATUS_REGION, TOOL_SHELF_REGION, RegionDefinition)\nfrom .workspace_definition import WorkspaceDefinition, WorkspacePlacement

SLD_WORKSPACE_ID = "sld"
CONTROL_WORKSPACE_ID = "control"
PROTECTION_WORKSPACE_ID = "protection"
PROJECT_PANEL_ID = "project"
EQUIPMENT_PANEL_ID = "equipment"
PROPERTIES_PANEL_ID = "properties"
ELEMENT_LIST_PANEL_ID = "element_list"
MESSAGES_PANEL_ID = "messages"
STUDY_CASES_PANEL_ID = "study_cases"

EDITOR_REGIONS: tuple[RegionDefinition, ...] = (
    RegionDefinition(HEADER_REGION, HEADER_REGION),
    RegionDefinition(TOOL_SHELF_REGION, TOOL_SHELF_REGION),
    RegionDefinition(CANVAS_REGION, CANVAS_REGION),
    RegionDefinition(SIDEBAR_REGION, SIDEBAR_REGION),
    RegionDefinition(OVERLAY_REGION, OVERLAY_REGION),
    RegionDefinition(STATUS_REGION, STATUS_REGION),
    RegionDefinition(DIAGNOSTICS_REGION, DIAGNOSTICS_REGION),
)

SLD_EDITOR_DEFINITION = EditorDefinition("sld-editor", SLD_EDITOR, "SLD Editor", EDITOR_REGIONS)
CONTROL_EDITOR_DEFINITION = EditorDefinition("control-editor", CONTROL_EDITOR, "Control Editor", EDITOR_REGIONS)
PROTECTION_EDITOR_DEFINITION = EditorDefinition("protection-editor", PROTECTION_EDITOR, "Protection Editor", EDITOR_REGIONS)
STUDY_EDITOR_DEFINITION = EditorDefinition("study-editor", STUDY_EDITOR, "Study Editor", (
    RegionDefinition(HEADER_REGION, HEADER_REGION),
    RegionDefinition(TOOL_SHELF_REGION, TOOL_SHELF_REGION),
    RegionDefinition(CANVAS_REGION, CANVAS_REGION),
    RegionDefinition(SIDEBAR_REGION, SIDEBAR_REGION),
    RegionDefinition(DIAGNOSTICS_REGION, DIAGNOSTICS_REGION),
    RegionDefinition("timeline", "timeline"),
))

CANONICAL_PANEL_IDS: tuple[str, ...] = (
    PROJECT_PANEL_ID,
    EQUIPMENT_PANEL_ID,
    PROPERTIES_PANEL_ID,
    ELEMENT_LIST_PANEL_ID,
    MESSAGES_PANEL_ID,
    STUDY_CASES_PANEL_ID,
)

SLD_WORKSPACE_PLACEMENTS: tuple[WorkspacePlacement, ...] = (
    WorkspacePlacement(PROJECT_PANEL_ID, PanelArea.LEFT, visible=True, order=0),
    WorkspacePlacement(EQUIPMENT_PANEL_ID, PanelArea.LEFT, visible=True, order=1),
    WorkspacePlacement(PROPERTIES_PANEL_ID, PanelArea.RIGHT, visible=True, order=0),
    WorkspacePlacement(ELEMENT_LIST_PANEL_ID, PanelArea.BOTTOM, visible=True, order=0),
    WorkspacePlacement(MESSAGES_PANEL_ID, PanelArea.BOTTOM, visible=True, order=1),
    WorkspacePlacement(STUDY_CASES_PANEL_ID, PanelArea.BOTTOM, visible=True, order=2),
)

SLD_WORKSPACE = WorkspaceDefinition(
    workspace_id=SLD_WORKSPACE_ID,
    title="SLD Workspace",
    placements=SLD_WORKSPACE_PLACEMENTS,
    metadata={"kind": "sld", "description": "Blender-inspired engineering editor composition.", "central_surface": "sld"},
)


PROTECTION_WORKSPACE = WorkspaceDefinition(
    workspace_id=PROTECTION_WORKSPACE_ID,
    title="Protection Workspace",
    placements=SLD_WORKSPACE_PLACEMENTS,
    metadata={"kind": "protection", "description": "Protection engineering/readout workspace.", "central_surface": "protection"},
)


CONTROL_WORKSPACE = WorkspaceDefinition(
    workspace_id=CONTROL_WORKSPACE_ID,
    title="Control Workspace",
    placements=SLD_WORKSPACE_PLACEMENTS,
    metadata={"kind": "control", "description": "Ladder/control engineering workspace.", "central_surface": "control"},
)

STUDY_WORKSPACE = WorkspaceDefinition(workspace_id="study", title="Study Workspace", areas=(AreaDefinition("main-study", STUDY_EDITOR_DEFINITION, metadata={"role": "main"}), AreaDefinition("diagnostics", EditorDefinition("diagnostics-editor", "diagnostics", "Diagnostics", (RegionDefinition(CANVAS_REGION, "diagnostics"),)), metadata={"role": "bottom"})), metadata={"kind": "study", "central_surface": "reports"})\n\nDEFAULT_WORKSPACES: tuple[WorkspaceDefinition, ...] = (SLD_WORKSPACE, CONTROL_WORKSPACE, PROTECTION_WORKSPACE, STUDY_WORKSPACE)


def default_workspaces() -> tuple[WorkspaceDefinition, ...]:
    return DEFAULT_WORKSPACES


def default_workspace_ids() -> tuple[str, ...]:
    return tuple(workspace.workspace_id for workspace in DEFAULT_WORKSPACES)


def get_default_workspace(workspace_id: str) -> WorkspaceDefinition:
    if not isinstance(workspace_id, str) or not workspace_id.strip(): raise ValueError("workspace_id must be a non-empty string.")
    for workspace in DEFAULT_WORKSPACES:
        if workspace.workspace_id == workspace_id: return workspace
    raise KeyError(f"Unknown default workspace: {workspace_id!r}")


def get_initial_workspace() -> WorkspaceDefinition: return SLD_WORKSPACE


def validate_default_workspace() -> None:
    if SLD_WORKSPACE.workspace_id != SLD_WORKSPACE_ID: raise RuntimeError("Initial Workspace ID is invalid.")
    placement_ids = tuple(placement.panel_id for placement in SLD_WORKSPACE.placements)
    if placement_ids != CANONICAL_PANEL_IDS: raise RuntimeError(f"Initial Workspace panel IDs are invalid: {placement_ids!r}")
    if len(set(placement_ids)) != len(placement_ids): raise RuntimeError("Initial Workspace contains duplicate panel IDs.")
    for placement in SLD_WORKSPACE.placements:
        if placement.area in (PanelArea.CENTER, PanelArea.FLOATING) or not placement.visible: raise RuntimeError("Supporting panels must be visible and non-central in the initial workspace.")


validate_default_workspace()

__all__ = [
    "SLD_WORKSPACE_ID", "CONTROL_WORKSPACE_ID", "PROJECT_PANEL_ID", "EQUIPMENT_PANEL_ID", "PROPERTIES_PANEL_ID",
    "ELEMENT_LIST_PANEL_ID", "MESSAGES_PANEL_ID", "STUDY_CASES_PANEL_ID", "CANONICAL_PANEL_IDS",
    "SLD_WORKSPACE_PLACEMENTS", "SLD_WORKSPACE", "CONTROL_WORKSPACE", "PROTECTION_WORKSPACE", "STUDY_WORKSPACE", "DEFAULT_WORKSPACES", "SLD_EDITOR_DEFINITION", "CONTROL_EDITOR_DEFINITION", "PROTECTION_EDITOR_DEFINITION", "STUDY_EDITOR_DEFINITION", "default_workspaces",
    "default_workspace_ids", "get_default_workspace", "get_initial_workspace", "validate_default_workspace",
]
