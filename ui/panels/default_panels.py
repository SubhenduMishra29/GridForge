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

The application currently provides three concrete supporting
panels for the SLD-first workflow:

    project
    equipment
    properties

The SLD/Grid canvas remains the central application surface and
is intentionally not registered here as a dock panel.
"""

from __future__ import annotations

from collections.abc import Iterable

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


DEFAULT_PANEL_DESCRIPTORS: tuple[
    PanelDescriptor,
    ...,
] = (
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
    Register the canonical GridForge application panels.

    Registration is intentionally idempotent.

    Existing descriptors with the same panel IDs are accepted
    only when they are the exact same descriptor object.

    Workspace placement is deliberately not performed here.
    """

    if not isinstance(
        registry,
        PanelRegistry,
    ):
        raise TypeError(
            "registry must be a PanelRegistry."
        )

    registered: list[PanelDescriptor] = []

    for descriptor in DEFAULT_PANEL_DESCRIPTORS:
        existing = registry.get(
            descriptor.panel_id
        )

        if existing is None:
            registry.register(
                descriptor
            )
            registered.append(
                descriptor
            )
            continue

        if existing is not descriptor:
            raise RuntimeError(
                "Conflicting panel descriptor already "
                f"registered for panel_id={descriptor.panel_id!r}."
            )

        registered.append(
            existing
        )

    return tuple(
        registered
    )


def default_panel_descriptors() -> tuple[
    PanelDescriptor,
    ...,
]:
    """
    Return the canonical default panel descriptors.

    A tuple is returned so callers cannot mutate the authoritative
    registration collection.
    """

    return DEFAULT_PANEL_DESCRIPTORS


def default_panel_ids() -> tuple[str, ...]:
    """
    Return canonical default panel IDs.
    """

    return tuple(
        descriptor.panel_id
        for descriptor in DEFAULT_PANEL_DESCRIPTORS
    )


def iter_default_panel_descriptors() -> Iterable[
    PanelDescriptor
]:
    """
    Iterate over canonical default panel descriptors.
    """

    return iter(
        DEFAULT_PANEL_DESCRIPTORS
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
    "iter_default_panel_descriptors",
]
