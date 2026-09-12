from __future__ import annotations

from .panel_area import PanelArea
from .workspace_definition import WorkspaceDefinition, WorkspacePlacement

SLD_WORKSPACE_ID = "sld"
PROJECT_PANEL_ID = "project"
EQUIPMENT_PANEL_ID = "equipment"
PROPERTIES_PANEL_ID = "properties"
ELEMENT_LIST_PANEL_ID = "element_list"
MESSAGES_PANEL_ID = "messages"
STUDY_CASES_PANEL_ID = "study_cases"

CANONICAL_PANEL_IDS: tuple[str, ...] = (
    PROJECT_PANEL_ID,
    EQUIPMENT_PANEL_ID,
    PROPERTIES_PANEL_ID,
    ELEMENT_LIST_PANEL_ID,
    MESSAGES_PANEL_ID,
    STUDY_CASES_PANEL_ID,
)

SLD_WORKSPACE_PLACEMENTS: tuple[WorkspacePlacement, ...] = (
    WorkspacePlacement(PROJECT_PANEL_ID, PanelArea.LEFT, 0, True),
    WorkspacePlacement(EQUIPMENT_PANEL_ID, PanelArea.LEFT, 1, True),
    WorkspacePlacement(PROPERTIES_PANEL_ID, PanelArea.RIGHT, 0, True),
    WorkspacePlacement(ELEMENT_LIST_PANEL_ID, PanelArea.BOTTOM, 0, True),
    WorkspacePlacement(MESSAGES_PANEL_ID, PanelArea.BOTTOM, 1, True),
    WorkspacePlacement(STUDY_CASES_PANEL_ID, PanelArea.BOTTOM, 2, True),
)

SLD_WORKSPACE = WorkspaceDefinition(
    workspace_id=SLD_WORKSPACE_ID,
    title="SLD Workspace",
    placements=SLD_WORKSPACE_PLACEMENTS,
    metadata={
        "kind": "sld",
        "description": "Initial GridForge engineering workspace.",
        "central_surface": "sld",
    },
)

DEFAULT_WORKSPACES: tuple[WorkspaceDefinition, ...] = (SLD_WORKSPACE,)


def default_workspaces() -> tuple[WorkspaceDefinition, ...]:
    return DEFAULT_WORKSPACES


def default_workspace_ids() -> tuple[str, ...]:
    return tuple(workspace.workspace_id for workspace in DEFAULT_WORKSPACES)


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
    if SLD_WORKSPACE.workspace_id != SLD_WORKSPACE_ID:
        raise RuntimeError("Initial Workspace ID is invalid.")
    placement_ids = tuple(placement.panel_id for placement in SLD_WORKSPACE.placements)
    if placement_ids != CANONICAL_PANEL_IDS:
        raise RuntimeError(f"Initial Workspace panel IDs are invalid: {placement_ids!r}")
    if len(set(placement_ids)) != len(placement_ids):
        raise RuntimeError("Initial Workspace contains duplicate panel IDs.")
    for placement in SLD_WORKSPACE.placements:
        if placement.area in (PanelArea.CENTER, PanelArea.FLOATING) or not placement.visible:
            raise RuntimeError("Supporting panels must be visible and non-central in the initial workspace.")

validate_default_workspace()

__all__ = [
    "SLD_WORKSPACE_ID", "PROJECT_PANEL_ID", "EQUIPMENT_PANEL_ID", "PROPERTIES_PANEL_ID",
    "ELEMENT_LIST_PANEL_ID", "MESSAGES_PANEL_ID", "STUDY_CASES_PANEL_ID", "CANONICAL_PANEL_IDS",
    "SLD_WORKSPACE_PLACEMENTS", "SLD_WORKSPACE", "DEFAULT_WORKSPACES", "default_workspaces",
    "default_workspace_ids", "get_default_workspace", "get_initial_workspace", "validate_default_workspace",
]
