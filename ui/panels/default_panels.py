# ============================================================
# GridForge V2 — Default Panels
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ui.core.qt import QListWidget, QVBoxLayout, QWidget
from ui.plugins.panels_plugin import PanelSpec
from .element_list_panel import ElementListPanelWidget
from .messages_panel import MessagesPanelWidget
from .properties_panel import PropertiesPanel
from .engineering_parameter_editor import EngineeringParameterEditor
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
    """Canonical Equipment Browser backed by the project-independent catalogue."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgePanel_equipment")
        self._equipment_registry: Any | None = None
        self._tool_manager: Any | None = None
        self._definitions: tuple[Any, ...] = ()
        self._selected_equipment_type: str | None = None
        self._active_tool_id: str | None = None

        self._list = QListWidget(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self._list)
        self._list.itemClicked.connect(self._on_item_clicked)

    @property
    def equipment_registry(self) -> Any | None:
        return self._equipment_registry

    @property
    def equipment_definitions(self) -> tuple[Any, ...]:
        return self._definitions

    @property
    def selected_equipment_type(self) -> str | None:
        return self._selected_equipment_type

    @property
    def active_tool_id(self) -> str | None:
        return self._active_tool_id

    def bind_equipment_runtime(self, equipment_registry: Any, tool_manager: Any) -> None:
        """Receive the canonical catalogue and live ToolManager from composition."""
        if equipment_registry is None or not callable(getattr(equipment_registry, "catalogue", None)):
            raise TypeError("equipment_registry must provide catalogue().")
        if tool_manager is None or not callable(getattr(tool_manager, "activate", None)):
            raise TypeError("tool_manager must provide activate().")
        self._equipment_registry = equipment_registry
        self._tool_manager = tool_manager
        self._definitions = tuple(equipment_registry.catalogue())
        self._list.clear()
        for definition in self._definitions:
            self._list.addItem(definition.display_name)

    def select_equipment_type(self, equipment_type: str | None) -> None:
        if equipment_type is None:
            self._selected_equipment_type = None
            return
        for definition in self._definitions:
            if definition.equipment_type == equipment_type:
                self._selected_equipment_type = equipment_type
                return
        raise KeyError(f"Unknown catalogue equipment type: {equipment_type!r}")

    def activate_selected_equipment(self) -> Any:
        if self._selected_equipment_type is None:
            raise RuntimeError("No equipment type is selected.")
        return self.activate_equipment(self._selected_equipment_type)

    def activate_equipment(self, equipment_type: str) -> Any:
        if self._tool_manager is None:
            raise RuntimeError("Equipment Browser has not been composed with ToolManager.")
        if self._equipment_registry is None:
            raise RuntimeError("Equipment Browser has no EquipmentRegistry.")
        definition = self._equipment_registry.require(equipment_type)
        self._selected_equipment_type = definition.equipment_type
        tool_id = definition.tool_id
        tool = self._tool_manager.activate(tool_id)
        self._active_tool_id = self._tool_manager.active_tool_id
        return tool

    def configure_active_tool(self, **parameters: Any) -> None:
        """Forward typed engineering configuration to the active Tool only.

        The Browser does not retain an engineering-configuration store.
        The active Tool owns the transient pre-placement configuration.
        """
        if self._tool_manager is None:
            raise RuntimeError("Equipment Browser has not been composed with ToolManager.")
        tool = self._tool_manager.get_current_tool()
        setter = getattr(tool, "set_engineering_parameters", None)
        if not callable(setter):
            raise RuntimeError("Active tool does not accept engineering parameters.")
        setter(**parameters)

    def _on_item_clicked(self, item: Any) -> None:
        row = self._list.row(item)
        if row < 0 or row >= len(self._definitions):
            return
        self.activate_equipment(self._definitions[row].equipment_type)


class PropertiesPanelWidget(QWidget):
    """Qt realization that delegates inspection state to PropertiesPanel."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgePanel_properties")
        self.logical_panel = PropertiesPanel()
        self.logical_panel.on_create()
        self._engineering_editor: EngineeringParameterEditor | None = None

    def bind_configuration_runtime(self, application: Any) -> None:
        """Bind the canonical Application command boundary for parameter edits."""
        self._engineering_editor = EngineeringParameterEditor(application)

    def configure_parameter(self, parameter_id: str, value: Any) -> Any:
        """Submit one typed edit from the current immutable projection."""
        if self._engineering_editor is None:
            raise RuntimeError("Properties configuration runtime is not bound.")
        target = self.logical_panel.target
        if target is None:
            raise RuntimeError("No projected element is selected.")
        intent = self._engineering_editor.intent_from_projection(
            target,
            {parameter_id: value},
        )
        return self._engineering_editor.submit(intent)

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
