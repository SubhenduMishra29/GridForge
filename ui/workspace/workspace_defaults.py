# ============================================================
# GridForge V2
# ============================================================
#
# File:
#     ui/workspace/workspace_defaults.py
#
# Purpose:
#     Authoritative logical definition of the initial
#     SLD-first application Workspace.
#
# Architectural boundary:
#     This module defines logical WorkspaceDefinition data only.
#
# It does NOT:
#     - import Qt;
#     - create QDockWidget;
#     - access MainWindow;
#     - create widgets;
#     - register panels;
#     - activate a Workspace;
#     - realize a Workspace;
#     - manipulate dock geometry.
#
# WorkspaceManager consumes these definitions.
# WorkspaceController orchestrates activation.
# WorkspaceRealizer translates the resulting WorkspaceLayout
# into Qt operations.
#
# ============================================================

"""
GridForge V2 — Default Workspace Definitions.

The initial application Workspace is SLD-first:

    central SLD/Grid canvas
        +
    project
    equipment
    properties

The SLD canvas is the central application surface. The three
listed IDs are supporting dockable panels.

Only logical placement information belongs here.
"""

from __future__ import annotations

from ui.workspace.workspace_definition import (
    WorkspaceDefinition,
)
from ui.workspace.workspace_layout import (
    PanelArea,
    WorkspacePlacement,
)


# ============================================================
# CANONICAL IDENTIFIERS
# ============================================================

SLD_WORKSPACE_ID = "sld"

PROJECT_PANEL_ID = "project"
EQUIPMENT_PANEL_ID = "equipment"
PROPERTIES_PANEL_ID = "properties"


# ============================================================
# CANONICAL PLACEMENTS
# ============================================================

SLD_WORKSPACE_PLACEMENTS: tuple[
    WorkspacePlacement,
    ...,
] = (
    WorkspacePlacement(
        panel_id=PROJECT_PANEL_ID,
        area=PanelArea.LEFT,
        visible=True,
        floating=False,
    ),
    WorkspacePlacement(
        panel_id=EQUIPMENT_PANEL_ID,
        area=PanelArea.LEFT,
        visible=True,
        floating=False,
    ),
    WorkspacePlacement(
        panel_id=PROPERTIES_PANEL_ID,
        area=PanelArea.RIGHT,
        visible=True,
        floating=False,
    ),
)


# ============================================================
# CANONICAL WORKSPACE DEFINITION
# ============================================================

SLD_WORKSPACE = WorkspaceDefinition(
    workspace_id=SLD_WORKSPACE_ID,
    name="SLD Workspace",
    description=(
        "Initial GridForge single-line-diagram workspace "
        "with project, equipment, and properties panels."
    ),
    placements=SLD_WORKSPACE_PLACEMENTS,
)


# ============================================================
# DEFAULT WORKSPACE COLLECTION
# ============================================================

DEFAULT_WORKSPACES: tuple[
    WorkspaceDefinition,
    ...
] = (
    SLD_WORKSPACE,
)


# ============================================================
# ACCESSORS
# ============================================================

def default_workspaces() -> tuple[
    WorkspaceDefinition,
    ...
]:
    """
    Return the canonical default Workspace definitions.

    A tuple is returned so callers cannot mutate the
    authoritative collection.
    """

    return DEFAULT_WORKSPACES


def default_workspace_ids() -> tuple[str, ...]:
    """
    Return the canonical default Workspace identifiers.
    """

    return tuple(
        workspace.workspace_id
        for workspace in DEFAULT_WORKSPACES
    )


def get_default_workspace(
    workspace_id: str,
) -> WorkspaceDefinition:
    """
    Return a canonical default Workspace by ID.
    """

    if not isinstance(
        workspace_id,
        str,
    ):
        raise TypeError(
            "workspace_id must be a string."
        )

    for workspace in DEFAULT_WORKSPACES:
        if workspace.workspace_id == workspace_id:
            return workspace

    raise KeyError(
        f"Unknown default workspace: {workspace_id!r}"
    )


def get_initial_workspace() -> WorkspaceDefinition:
    """
    Return the Workspace used for initial application
    activation.
    """

    return SLD_WORKSPACE


# ============================================================
# VALIDATION
# ============================================================

_EXPECTED_PANEL_IDS = (
    PROJECT_PANEL_ID,
    EQUIPMENT_PANEL_ID,
    PROPERTIES_PANEL_ID,
)


def validate_default_workspace() -> None:
    """
    Validate the invariants of the initial Workspace.

    This function performs logical validation only and has no
    Qt or application-host dependency.
    """

    if SLD_WORKSPACE.workspace_id != SLD_WORKSPACE_ID:
        raise RuntimeError(
            "Initial Workspace ID does not match the "
            "canonical SLD Workspace ID."
        )

    placement_ids = tuple(
        placement.panel_id
        for placement in SLD_WORKSPACE.placements
    )

    if placement_ids != _EXPECTED_PANEL_IDS:
        raise RuntimeError(
            "Initial Workspace panel IDs do not match the "
            f"canonical panel set: {placement_ids!r}"
        )

    if len(set(placement_ids)) != len(placement_ids):
        raise RuntimeError(
            "Initial Workspace contains duplicate panel IDs."
        )

    for placement in SLD_WORKSPACE.placements:
        if placement.area == PanelArea.CENTER:
            raise RuntimeError(
                "Supporting panels must not occupy the "
                "central SLD canvas area."
            )

        if placement.floating:
            raise RuntimeError(
                "Initial SLD Workspace must not contain "
                "floating panels."
            )


# Validate the immutable module-level definition once when
# imported. This catches malformed bootstrap data early while
# remaining independent of Qt and application construction.
validate_default_workspace()


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "SLD_WORKSPACE_ID",
    "PROJECT_PANEL_ID",
    "EQUIPMENT_PANEL_ID",
    "PROPERTIES_PANEL_ID",
    "SLD_WORKSPACE_PLACEMENTS",
    "SLD_WORKSPACE",
    "DEFAULT_WORKSPACES",
    "default_workspaces",
    "default_workspace_ids",
    "get_default_workspace",
    "get_initial_workspace",
    "validate_default_workspace",
]
