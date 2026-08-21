# ============================================================
# GridForge V2
# ============================================================
#
# File:
#     ui/panels/default_panels.py
#
# Purpose:
#     Authoritative presentation definitions for the initial
#     SLD-first application panels.
#
# Architectural boundary
# ----------------------
#
# This module defines:
#     - canonical panel IDs;
#     - panel titles;
#     - panel presentation widgets;
#     - panel capabilities.
#
# This module does NOT define:
#     - WorkspaceDefinition;
#     - WorkspaceLayout;
#     - PanelArea;
#     - dock placement;
#     - dock ordering;
#     - tab groups;
#     - visibility policy;
#     - Workspace activation;
#     - MainWindow layout policy.
#
# PanelsPlugin owns dock creation.
# WorkspaceRealizer owns dock arrangement.
#
# ============================================================

"""
GridForge V2 — Default Application Panels.

The initial SLD-first application contains three supporting
dockable panels:

    project
    equipment
    properties

The SLD/Grid canvas remains the central application surface and
is deliberately not represented as a dock panel.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ui.core.qt import QWidget

from ui.plugins.panels_plugin import PanelSpec


# ============================================================
# PANEL WIDGET FACTORIES
# ============================================================


class ProjectPanelWidget(QWidget):
    """
    Presentation widget for the Project Explorer panel.

    This class intentionally contains only presentation state.
    Project/network ownership remains outside the panel.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName(
            "GridForgePanel_project"
        )


class EquipmentPanelWidget(QWidget):
    """
    Presentation widget for the Equipment Browser panel.

    Equipment creation remains delegated to the application's
    command/tool/model workflow.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName(
            "GridForgePanel_equipment"
        )


class PropertiesPanelWidget(QWidget):
    """
    Presentation widget for the Properties panel.

    The authoritative selected object remains outside this widget.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName(
            "GridForgePanel_properties"
        )


# ============================================================
# CANONICAL PANEL SPECIFICATIONS
# ============================================================


PROJECT_PANEL = PanelSpec(
    panel_id="project",
    title="Project Explorer",
    widget=None,
    closable=True,
    movable=True,
    floatable=True,
)


EQUIPMENT_PANEL = PanelSpec(
    panel_id="equipment",
    title="Equipment Browser",
    widget=None,
    closable=True,
    movable=True,
    floatable=True,
)


PROPERTIES_PANEL = PanelSpec(
    panel_id="properties",
    title="Properties",
    widget=None,
    closable=True,
    movable=True,
    floatable=True,
)


DEFAULT_PANEL_SPECS: tuple[PanelSpec, ...] = (
    PROJECT_PANEL,
    EQUIPMENT_PANEL,
    PROPERTIES_PANEL,
)


# ============================================================
# FACTORIES
# ============================================================


_PANEL_WIDGET_FACTORIES: dict[
    str,
    Callable[[QWidget | None], QWidget],
] = {
    "project": ProjectPanelWidget,
    "equipment": EquipmentPanelWidget,
    "properties": PropertiesPanelWidget,
}


def create_panel_widget(
    panel_id: str,
    parent: QWidget | None = None,
) -> QWidget:
    """
    Create the presentation widget for a canonical panel ID.
    """

    if not isinstance(panel_id, str):
        raise TypeError(
            "panel_id must be a string."
        )

    if not panel_id.strip():
        raise ValueError(
            "panel_id must not be empty."
        )

    factory = _PANEL_WIDGET_FACTORIES.get(
        panel_id
    )

    if factory is None:
        raise KeyError(
            f"Unknown default panel ID: {panel_id!r}"
        )

    return factory(parent)


def panel_spec_with_widget(
    spec: PanelSpec,
) -> PanelSpec:
    """
    Return a PanelSpec containing its concrete presentation
    widget.

    Workspace information is never added here.
    """

    if not isinstance(
        spec,
        PanelSpec,
    ):
        raise TypeError(
            "spec must be a PanelSpec."
        )

    widget = create_panel_widget(
        spec.panel_id
    )

    return PanelSpec(
        panel_id=spec.panel_id,
        title=spec.title,
        widget=widget,
        closable=spec.closable,
        movable=spec.movable,
        floatable=spec.floatable,
        metadata=dict(spec.metadata),
    )


def default_panel_specs() -> tuple[PanelSpec, ...]:
    """
    Return the canonical immutable panel specifications.
    """

    return DEFAULT_PANEL_SPECS


def default_panel_ids() -> tuple[str, ...]:
    """
    Return the canonical application panel IDs.
    """

    return tuple(
        spec.panel_id
        for spec in DEFAULT_PANEL_SPECS
    )


def compose_default_panel_specs() -> tuple[PanelSpec, ...]:
    """
    Create the concrete presentation specifications used by
    PanelsPlugin.

    This is the only application-level conversion from the
    declarative panel definitions to concrete QWidget-backed
    PanelSpec objects.
    """

    return tuple(
        panel_spec_with_widget(spec)
        for spec in DEFAULT_PANEL_SPECS
    )


# ============================================================
# VALIDATION
# ============================================================


_EXPECTED_PANEL_IDS = (
    "project",
    "equipment",
    "properties",
)


def validate_default_panel_ids() -> tuple[str, ...]:
    """
    Validate and return the canonical panel IDs.

    This function checks the invariant locally without touching
    PanelsPlugin, MainWindow, or Workspace.
    """

    ids = default_panel_ids()

    if ids != _EXPECTED_PANEL_IDS:
        raise RuntimeError(
            "Default panel IDs do not match the canonical "
            f"application panel set: {ids!r}"
        )

    if len(set(ids)) != len(ids):
        raise RuntimeError(
            "Default panel IDs must be unique."
        )

    return ids


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "ProjectPanelWidget",
    "EquipmentPanelWidget",
    "PropertiesPanelWidget",
    "PROJECT_PANEL",
    "EQUIPMENT_PANEL",
    "PROPERTIES_PANEL",
    "DEFAULT_PANEL_SPECS",
    "create_panel_widget",
    "panel_spec_with_widget",
    "default_panel_specs",
    "default_panel_ids",
    "compose_default_panel_specs",
    "validate_default_panel_ids",
]
