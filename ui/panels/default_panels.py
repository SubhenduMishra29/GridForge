# ============================================================
# GridForge V2 — Default Panels
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ui.core.qt import QWidget
from ui.plugins.panels_plugin import PanelSpec
from .element_list_panel import ElementListPanelWidget
from .messages_panel import MessagesPanelWidget
from .properties_panel import PropertiesPanel
from .study_cases_panel import StudyCasesPanelWidget


class ProjectPanelWidget(QWidget):
    """Presentation surface for the Application project hierarchy projection."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgePanel_project")
        self._hierarchy: Any | None = None

    @property
    def hierarchy(self) -> Any | None:
        return self._hierarchy

    def set_hierarchy(self, hierarchy: Any | None) -> None:
        self._hierarchy = hierarchy

    def clear_hierarchy(self) -> None:
        self._hierarchy = None


class EquipmentPanelWidget(QWidget):
    """Canonical Equipment Browser surface; projection contract remains undefined."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgePanel_equipment")


class PropertiesPanelWidget(QWidget):
    """Qt realization that delegates inspection state to PropertiesPanel."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgePanel_properties")
        self.logical_panel = PropertiesPanel()
        self.logical_panel.on_create()

    @property
    def target(self) -> Any | None:
        return self.logical_panel.target

    def set_target(self, target: Any | None) -> None:
        self.logical_panel.set_target(target)

    def clear_target(self) -> None:
        self.logical_panel.clear_target()


PROJECT_PANEL = PanelSpec(panel_id="project", title="Project Explorer")
EQUIPMENT_PANEL = PanelSpec(panel_id="equipment", title="Equipment Browser")
PROPERTIES_PANEL = PanelSpec(panel_id="properties", title="Properties")
ELEMENT_LIST_PANEL = PanelSpec(panel_id="element_list", title="Element List")
MESSAGES_PANEL = PanelSpec(panel_id="messages", title="Messages / Events")
STUDY_CASES_PANEL = PanelSpec(panel_id="study_cases", title="Study Cases")

DEFAULT_PANEL_SPECS: tuple[PanelSpec, ...] = (
    PROJECT_PANEL,
    EQUIPMENT_PANEL,
    PROPERTIES_PANEL,
    ELEMENT_LIST_PANEL,
    MESSAGES_PANEL,
    STUDY_CASES_PANEL,
)

_PANEL_WIDGET_FACTORIES: dict[str, Callable[[QWidget | None], QWidget]] = {
    "project": ProjectPanelWidget,
    "equipment": EquipmentPanelWidget,
    "properties": PropertiesPanelWidget,
    "element_list": ElementListPanelWidget,
    "messages": MessagesPanelWidget,
    "study_cases": StudyCasesPanelWidget,
}


def create_panel_widget(panel_id: str, parent: QWidget | None = None) -> QWidget:
    factory = _PANEL_WIDGET_FACTORIES.get(panel_id)
    if factory is None:
        raise KeyError(f"Unknown default panel ID: {panel_id!r}")
    return factory(parent)


def panel_spec_with_widget(spec: PanelSpec) -> PanelSpec:
    return PanelSpec(
        panel_id=spec.panel_id,
        title=spec.title,
        widget=create_panel_widget(spec.panel_id),
        closable=spec.closable,
        movable=spec.movable,
        floatable=spec.floatable,
        metadata=dict(spec.metadata),
    )


def default_panel_specs() -> tuple[PanelSpec, ...]:
    return DEFAULT_PANEL_SPECS


def default_panel_ids() -> tuple[str, ...]:
    return tuple(spec.panel_id for spec in DEFAULT_PANEL_SPECS)


def compose_default_panel_specs() -> tuple[PanelSpec, ...]:
    return tuple(panel_spec_with_widget(spec) for spec in DEFAULT_PANEL_SPECS)


def validate_default_panel_ids() -> tuple[str, ...]:
    ids = default_panel_ids()
    if len(ids) != 6 or len(set(ids)) != 6:
        raise RuntimeError("Default panel IDs must be unique and complete.")
    return ids


__all__ = [
    "ProjectPanelWidget",
    "EquipmentPanelWidget",
    "PropertiesPanelWidget",
    "ElementListPanelWidget",
    "MessagesPanelWidget",
    "StudyCasesPanelWidget",
    "PROJECT_PANEL",
    "EQUIPMENT_PANEL",
    "PROPERTIES_PANEL",
    "ELEMENT_LIST_PANEL",
    "MESSAGES_PANEL",
    "STUDY_CASES_PANEL",
    "DEFAULT_PANEL_SPECS",
    "create_panel_widget",
    "panel_spec_with_widget",
    "default_panel_specs",
    "default_panel_ids",
    "compose_default_panel_specs",
    "validate_default_panel_ids",
]
