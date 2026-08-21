# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/default_panels.py
#
# Purpose:
#     Authoritative registration source for the initial
#     application panels.
#
# Architectural boundary:
#     This module defines which concrete panels exist.
#
# It does NOT:
#     - define WorkspaceLayout;
#     - define dock areas;
#     - arrange panels;
#     - activate a Workspace;
#     - manipulate MainWindow;
#     - create QDockWidget;
#     - own runtime panel state.
# ============================================================

"""
GridForge V2 — Default Panel Registration.

Initial SLD-first supporting panels:

    project
    equipment
    properties

The SLD/Grid canvas remains the central application surface and
is deliberately not registered as a dock panel here.
"""

from __future__ import annotations

from .equipment_panel import EquipmentPanel
from .panel_descriptor import PanelDescriptor
from .panel_registry import PanelRegistry
from .properties_panel import PropertiesPanel
from .project_panel import ProjectPanel


# ============================================================
# CANONICAL PANEL DESCRIPTORS
# ============================================================

PROJECT_PANEL = PanelDescriptor(
    panel_id="project",
    title="Project Explorer",
    factory=ProjectPanel,
    singleton=True,
    visible_by_default=True,
    closable=True,
    movable=True,
    floatable=True,
)

EQUIPMENT_PANEL = PanelDescriptor(
    panel_id="equipment",
    title="Equipment Browser",
    factory=EquipmentPanel,
    singleton=True,
    visible_by_default=True,
    closable=True,
    movable=True,
    floatable=True,
)

PROPERTIES_PANEL = PanelDescriptor(
    panel_id="properties",
    title="Properties",
    factory=PropertiesPanel,
    singleton=True,
    visible_by_default=True,
    closable=True,
    movable=True,
    floatable=True,
)


DEFAULT_PANEL_DESCRIPTORS: tuple[PanelDescriptor, ...] = (
    PROJECT_PANEL,
    EQUIPMENT_PANEL,
    PROPERTIES_PANEL,
)


# ============================================================
# REGISTRATION
# ============================================================

def register_default_panels(
    registry: PanelRegistry,
) -> tuple[PanelDescriptor, ...]:
    """
    Register all canonical application panels.

    Registration is intentionally strict. PanelRegistry owns
    duplicate detection, so this function does not attempt to
    make registration idempotent.

    Workspace placement is deliberately not performed here.
    """

    if not isinstance(registry, PanelRegistry):
        raise TypeError(
            "registry must be a PanelRegistry."
        )

    for descriptor in DEFAULT_PANEL_DESCRIPTORS:
        registry.register(descriptor)

    return DEFAULT_PANEL_DESCRIPTORS


# ============================================================
# READ-ONLY DEFAULT DEFINITIONS
# ============================================================

def default_panel_descriptors() -> tuple[PanelDescriptor, ...]:
    """
    Return the canonical default panel descriptors.
    """

    return DEFAULT_PANEL_DESCRIPTORS


def default_panel_ids() -> tuple[str, ...]:
    """
    Return the canonical default panel identifiers.
    """

    return tuple(
        descriptor.panel_id
        for descriptor in DEFAULT_PANEL_DESCRIPTORS
    )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "PROJECT_PANEL",
    "EQUIPMENT_PANEL",
    "PROPERTIES_PANEL",
    "DEFAULT_PANEL_DESCRIPTORS",
    "register_default_panels",
    "default_panel_descriptors",
    "default_panel_ids",
]
