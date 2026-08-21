# ============================================================
# GridForge V2
# ============================================================
#
# File:
#     ui/workspace/workspace_defaults.py
#
# Purpose:
#     Authoritative logical definitions for the initial
#     SLD-first application Workspace.
#
# Architectural boundary:
#     Logical Workspace data only.
#
# This module does NOT:
#     - import Qt;
#     - create QWidget/QDockWidget;
#     - access MainWindow;
#     - create panels;
#     - register panels;
#     - arrange docks;
#     - activate a Workspace;
#     - perform Workspace realization.
#
# WorkspaceManager consumes these definitions.
# WorkspaceController orchestrates transitions.
# WorkspaceRealizer performs Qt realization.
#
# ============================================================

"""
GridForge V2 — Default Workspace Definitions.

Initial Workspace:

    SLD/Grid canvas
        +
    Project Explorer
    Equipment Browser
    Properties

The SLD/Grid canvas is the central application surface.
The three supporting surfaces are logical dock placements.
"""

from __future__ import annotations

from .panel_area import PanelArea
from .workspace_definition import (
    WorkspaceDefinition,
    WorkspacePlacement,
)


# ============================================================
# CANONICAL IDENTIFIERS
# ============================================================

SLD_WORKSPACE_ID = "sld"

PROJECT_PANEL_ID = "project"
EQUIPMENT_PANEL_ID = "equipment"
PROPERTIES_PANEL_ID = "properties"


CANONICAL_PANEL_IDS: tuple[str, ...] = (
    PROJECT_PANEL_ID,
    EQUIPMENT_PANEL_ID,
    PROPERTIES_PANEL_ID,
)


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
        order=0,
        visible=True,
    ),
    WorkspacePlacement(
        panel_id=EQUIPMENT_PANEL_ID,
        area=PanelArea.LEFT,
        order=1,
        visible=True,
    ),
    WorkspacePlacement(
        panel_id=PROPERTIES_PANEL_ID,
        area=PanelArea.RIGHT,
        order=0,
        visible=True,
    ),
)


# ============================================================
# CANONICAL WORKSPACE
# ============================================================

SLD_WORKSPACE = WorkspaceDefinition(
    workspace_id=SLD_WORKSPACE_ID,
    title="SLD Workspace",
    placements=SLD_WORKSPACE_PLACEMENTS,
    metadata={
        "kind": "sld",
        "description": (
            "Initial GridForge single-line-diagram "
            "workspace."
        ),
        "central_surface": "sld",
    },
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

    if not workspace_id.strip():
        raise ValueError(
            "workspace_id must not be empty."
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

def validate_default_workspace() -> None:
    """
    Validate the canonical initial Workspace.

    Validation is entirely logical and Qt-independent.
    """

    if SLD_WORKSPACE.workspace_id != SLD_WORKSPACE_ID:
        raise RuntimeError(
            "Initial Workspace ID does not match "
            "SLD_WORKSPACE_ID."
        )

    if not SLD_WORKSPACE.title.strip():
        raise RuntimeError(
            "Initial Workspace title must not be empty."
        )

    placements = SLD_WORKSPACE.placements

    if not isinstance(
        placements,
        tuple,
    ):
        raise RuntimeError(
            "Initial Workspace placements must be a tuple."
        )

    placement_ids = tuple(
        placement.panel_id
        for placement in placements
    )

    if placement_ids != CANONICAL_PANEL_IDS:
        raise RuntimeError(
            "Initial Workspace panel IDs do not match "
            f"the canonical panel set: {placement_ids!r}"
        )

    if len(set(placement_ids)) != len(placement_ids):
        raise RuntimeError(
            "Initial Workspace contains duplicate panel IDs."
        )

    for placement in placements:
        if placement.area == PanelArea.CENTER:
            raise RuntimeError(
                "Supporting panels must not occupy "
                "PanelArea.CENTER."
            )

        if placement.area == PanelArea.FLOATING:
            raise RuntimeError(
                "Initial SLD Workspace must not contain "
                "floating panels."
            )

        if not placement.visible:
            raise RuntimeError(
                "Initial SLD Workspace panels must be "
                "visible by default."
            )

    project = SLD_WORKSPACE.placements[0]
    equipment = SLD_WORKSPACE.placements[1]
    properties = SLD_WORKSPACE.placements[2]

    if project.area != PanelArea.LEFT:
        raise RuntimeError(
            "Project panel must occupy PanelArea.LEFT."
        )

    if equipment.area != PanelArea.LEFT:
        raise RuntimeError(
            "Equipment panel must occupy PanelArea.LEFT."
        )

    if properties.area != PanelArea.RIGHT:
        raise RuntimeError(
            "Properties panel must occupy PanelArea.RIGHT."
        )

    if project.order != 0:
        raise RuntimeError(
            "Project panel must have LEFT order 0."
        )

    if equipment.order != 1:
        raise RuntimeError(
            "Equipment panel must have LEFT order 1."
        )

    if properties.order != 0:
        raise RuntimeError(
            "Properties panel must have RIGHT order 0."
        )


# Validate immutable bootstrap data at import time.
validate_default_workspace()


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "SLD_WORKSPACE_ID",
    "PROJECT_PANEL_ID",
    "EQUIPMENT_PANEL_ID",
    "PROPERTIES_PANEL_ID",
    "CANONICAL_PANEL_IDS",
    "SLD_WORKSPACE_PLACEMENTS",
    "SLD_WORKSPACE",
    "DEFAULT_WORKSPACES",
    "default_workspaces",
    "default_workspace_ids",
    "get_default_workspace",
    "get_initial_workspace",
    "validate_default_workspace",
]
