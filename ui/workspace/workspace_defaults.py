# ============================================================
# File: ui/workspace/workspace_defaults.py
# GridForge V2 — Canonical Workspace Defaults
# Author: Subhendu Mishra
# ============================================================
"""Canonical Area/Editor workspace definitions with legacy placement compatibility."""

from __future__ import annotations

from .area import AreaDefinition
from .editor import EditorDefinition, SLD_EDITOR, CONTROL_EDITOR, PROTECTION_EDITOR, STUDY_EDITOR
from .panel_area import PanelArea
from .region import CANVAS_REGION, DIAGNOSTICS_REGION, HEADER_REGION, OVERLAY_REGION, SIDEBAR_REGION, STATUS_REGION, TOOL_SHELF_REGION, RegionDefinition
from .workspace_definition import WorkspaceDefinition, WorkspacePlacement

SLD_WORKSPACE_ID = "sld"
CONTROL_WORKSPACE_ID = "control"
PROTECTION_WORKSPACE_ID = "protection"
STUDY_WORKSPACE_ID = "study"

PROJECT_PANEL_ID = "project"
EQUIPMENT_PANEL_ID = "equipment"
PROPERTIES_PANEL_ID = "properties"
ELEMENT_LIST_PANEL_ID = "element_list"
MESSAGES_PANEL_ID = "messages"
STUDY_CASES_PANEL_ID = "study_cases"

CANONICAL_PANEL_IDS = (
    PROJECT_PANEL_ID, EQUIPMENT_PANEL_ID, PROPERTIES_PANEL_ID,
    ELEMENT_LIST_PANEL_ID, MESSAGES_PANEL_ID, STUDY_CASES_PANEL_ID,
)

EDITOR_REGIONS = (
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
STUDY_EDITOR_DEFINITION = EditorDefinition(
    "study-editor", STUDY_EDITOR, "Study Editor",
    EDITOR_REGIONS + (RegionDefinition("timeline", "timeline"),),
)

def _explorer_area() -> AreaDefinition:
    return AreaDefinition("explorer", EditorDefinition("explorer-editor", "explorer", "Engineering Explorer", (RegionDefinition(CANVAS_REGION, "explorer"),)), metadata={"role": "explorer"})

def _inspector_area() -> AreaDefinition:
    return AreaDefinition("inspector", EditorDefinition("properties-editor", "properties", "Contextual Inspector", (RegionDefinition(CANVAS_REGION, "inspector"),)), metadata={"role": "inspector"})

def _diagnostics_area() -> AreaDefinition:
    return AreaDefinition("diagnostics", EditorDefinition("diagnostics-editor", "diagnostics", "Diagnostics", (RegionDefinition(CANVAS_REGION, "diagnostics"),)), metadata={"role": "bottom"})

SLD_WORKSPACE_PLACEMENTS = (
    WorkspacePlacement(PROJECT_PANEL_ID, PanelArea.LEFT, order=0),
    WorkspacePlacement(EQUIPMENT_PANEL_ID, PanelArea.LEFT, order=1),
    WorkspacePlacement(PROPERTIES_PANEL_ID, PanelArea.RIGHT),
    WorkspacePlacement(ELEMENT_LIST_PANEL_ID, PanelArea.BOTTOM),
    WorkspacePlacement(MESSAGES_PANEL_ID, PanelArea.BOTTOM, order=1),
    WorkspacePlacement(STUDY_CASES_PANEL_ID, PanelArea.BOTTOM, order=2),
)

def _workspace(workspace_id: str, title: str, editor: EditorDefinition, central_surface: str) -> WorkspaceDefinition:
    return WorkspaceDefinition(
        workspace_id=workspace_id,
        title=title,
        placements=SLD_WORKSPACE_PLACEMENTS,
        areas=(
            AreaDefinition(f"main-{workspace_id}", editor, metadata={"role": "main"}),
            _explorer_area(),
            _inspector_area(),
            _diagnostics_area(),
        ),
        metadata={"kind": workspace_id, "central_surface": central_surface},
    )

SLD_WORKSPACE = _workspace(SLD_WORKSPACE_ID, "SLD Workspace", SLD_EDITOR_DEFINITION, "sld")
CONTROL_WORKSPACE = _workspace(CONTROL_WORKSPACE_ID, "Control Workspace", CONTROL_EDITOR_DEFINITION, "control")
PROTECTION_WORKSPACE = _workspace(PROTECTION_WORKSPACE_ID, "Protection Workspace", PROTECTION_EDITOR_DEFINITION, "protection")
STUDY_WORKSPACE = WorkspaceDefinition(
    workspace_id=STUDY_WORKSPACE_ID,
    title="Study Workspace",
    areas=(
        AreaDefinition("main-study", STUDY_EDITOR_DEFINITION, metadata={"role": "main"}),
        _diagnostics_area(),
    ),
    metadata={"kind": "study", "central_surface": "reports"},
)

DEFAULT_WORKSPACES = (SLD_WORKSPACE, CONTROL_WORKSPACE, PROTECTION_WORKSPACE, STUDY_WORKSPACE)

def default_workspaces() -> tuple[WorkspaceDefinition, ...]:
    return DEFAULT_WORKSPACES

def default_workspace_ids() -> tuple[str, ...]:
    return tuple(item.workspace_id for item in DEFAULT_WORKSPACES)

def get_default_workspace(workspace_id: str) -> WorkspaceDefinition:
    if not isinstance(workspace_id, str) or not workspace_id.strip():
        raise ValueError("workspace_id must be a non-empty string.")
    for workspace in DEFAULT_WORKSPACES:
        if workspace.workspace_id == workspace_id:
            return workspace
    raise KeyError(f"Unknown default workspace: {workspace_id!r}")

def get_initial_workspace() -> WorkspaceDefinition:
    return SLD_WORKSPACE

def validate_default_workspace() -> None:
    placement_ids = tuple(item.panel_id for item in SLD_WORKSPACE.placements)
    if placement_ids != CANONICAL_PANEL_IDS:
        raise RuntimeError(f"Initial Workspace panel IDs are invalid: {placement_ids!r}")
    if len(set(placement_ids)) != len(placement_ids):
        raise RuntimeError("Initial Workspace contains duplicate panel IDs.")
    for placement in SLD_WORKSPACE.placements:
        if placement.area in (PanelArea.CENTER, PanelArea.FLOATING) or not placement.visible:
            raise RuntimeError("Initial workspace supporting placements must be visible and non-central.")

validate_default_workspace()

__all__ = [
    "SLD_WORKSPACE_ID", "CONTROL_WORKSPACE_ID", "PROTECTION_WORKSPACE_ID", "STUDY_WORKSPACE_ID",
    "PROJECT_PANEL_ID", "EQUIPMENT_PANEL_ID", "PROPERTIES_PANEL_ID", "ELEMENT_LIST_PANEL_ID",
    "MESSAGES_PANEL_ID", "STUDY_CASES_PANEL_ID", "CANONICAL_PANEL_IDS", "SLD_WORKSPACE_PLACEMENTS",
    "SLD_WORKSPACE", "CONTROL_WORKSPACE", "PROTECTION_WORKSPACE", "STUDY_WORKSPACE",
    "DEFAULT_WORKSPACES", "SLD_EDITOR_DEFINITION", "CONTROL_EDITOR_DEFINITION",
    "PROTECTION_EDITOR_DEFINITION", "STUDY_EDITOR_DEFINITION", "default_workspaces",
    "default_workspace_ids", "get_default_workspace", "get_initial_workspace", "validate_default_workspace",
]
