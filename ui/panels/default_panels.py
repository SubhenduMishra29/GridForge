# ============================================================
# GridForge V2 — Default Panels
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4
import logging
from typing import Any

from core.application.errors import ExecutionError

from ui.projection.projection_state import EngineeringParameterState, ProjectionState
from ui.creation.creation_context import CreationContext, CreationDraft

from ui.core.qt import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QLabel, QLineEdit, Signal,
    QListWidget, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QSize, Qt,
    QChart, QChartView, QLineSeries, QLogValueAxis, QPainter,
)
from ui.plugins.panels_plugin import PanelSpec
from ui.equipment.symbol.palette_symbol_adapter import PaletteSymbolAdapter
from .element_list_panel import ElementListPanelWidget
from .messages_panel import MessagesPanelWidget
from .properties_panel import PropertiesPanel
from .engineering_parameter_editor import EngineeringParameterEditor
from .study_cases_panel import StudyCasesPanelWidget


class ProjectPanelWidget(QWidget):
    """Presentation surface for the Application project hierarchy projection."""

    _SYSTEM_GROUPS = (
        "Buses", "Equipment", "Lines", "Transformers", "Loads",
        "Generators", "Shunts", "Measurements", "Protection", "Scenarios",
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgePanel_project")
        self._hierarchy: Any | None = None
        self._selection_manager: Any | None = None
        self._updating_selection = False
        self._tree = QTreeWidget(self)
        self._tree.setHeaderHidden(True)
        self._tree.setObjectName("ProjectHierarchyTree")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self._tree)
        self._tree.itemSelectionChanged.connect(self._on_tree_selection)

    def bind_selection_manager(self, selection_manager: Any) -> None:
        if selection_manager is None or not callable(getattr(selection_manager, "select_single", None)):
            raise TypeError("selection_manager must provide select_single().")
        self._selection_manager = selection_manager
        selection_manager.selection_changed.connect(self._on_canonical_selection)

    @property
    def hierarchy(self) -> Any | None:
        return self._hierarchy

    def set_hierarchy(self, hierarchy: Any | None) -> None:
        self._hierarchy = hierarchy
        self._render_hierarchy()

    def clear_hierarchy(self) -> None:
        self._hierarchy = None
        self._tree.clear()

    def _on_tree_selection(self) -> None:
        if self._updating_selection or self._selection_manager is None:
            return
        items = self._tree.selectedItems()
        if not items:
            return
        object_id = items[0].data(0, 32)
        if object_id:
            self._selection_manager.select_single(str(object_id))

    def _on_canonical_selection(self, ids: object) -> None:
        selected = {str(value) for value in (ids or ())}
        self._updating_selection = True
        try:
            self._tree.clearSelection()
            if not selected:
                return
            iterator = self._tree.findItems("", Qt.MatchFlag.MatchContains | Qt.MatchFlag.MatchRecursive, 0)
            for item in iterator:
                if str(item.data(0, 32) or "") in selected:
                    item.setSelected(True)
                    self._tree.scrollToItem(item)
                    break
        finally:
            self._updating_selection = False

    def _render_hierarchy(self) -> None:
        self._tree.clear()
        if not isinstance(self._hierarchy, dict):
            return
        project = self._hierarchy.get("project") or {}
        root = QTreeWidgetItem([str(project.get("name") or "Project")])
        root.setData(0, 32, str(project.get("id") or ""))
        self._tree.addTopLevelItem(root)

        network = QTreeWidgetItem(["Network Elements"])
        root.addChild(network)
        grouped: dict[str, list[dict[str, Any]]] = {}
        for element in self._hierarchy.get("network_elements") or ():
            grouped.setdefault(str(element.get("type") or "Other"), []).append(element)
        for element_type, elements in sorted(grouped.items()):
            group = QTreeWidgetItem([element_type.title()])
            network.addChild(group)
            for element in elements:
                item = QTreeWidgetItem([str(element.get("name") or element.get("id"))])
                item.setData(0, 32, str(element.get("id") or ""))
                group.addChild(item)

        documents_node = QTreeWidgetItem(["Documents"])
        root.addChild(documents_node)
        for document in project.get("documents") or ():
            if isinstance(document, dict):
                documents_node.addChild(QTreeWidgetItem([
                    str(document.get("name") or document.get("type") or "Document")
                ]))

        studies = QTreeWidgetItem(["Study Cases"])
        root.addChild(studies)
        workspace_id = self._hierarchy.get("workspace_id")
        if workspace_id:
            studies.addChild(QTreeWidgetItem([f"Workspace: {workspace_id}"]))

        root.setExpanded(True)
        network.setExpanded(True)
        for group in (network.child(i) for i in range(network.childCount())):
            group.setExpanded(True)
        documents_node.setExpanded(True)
        studies.setExpanded(True)


class EquipmentPanelWidget(QWidget):
    """Canonical Equipment Browser backed by the project-independent catalogue."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgePanel_equipment")
        self._equipment_registry: Any | None = None
        self._tool_manager: Any | None = None
        self._definitions: tuple[Any, ...] = ()
        self._visible_definitions: tuple[Any, ...] = ()
        self._selected_equipment_type: str | None = None
        self._active_tool_id: str | None = None
        self._properties_panel: Any | None = None
        self._symbol_registry: Any | None = None
        self._palette_symbol_adapter: PaletteSymbolAdapter | None = None

        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Search components…")
        self._search.setObjectName("EquipmentSearch")
        self._list = QListWidget(self)
        self._list.setViewMode(QListWidget.ViewMode.IconMode)
        self._list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self._list.setMovement(QListWidget.Movement.Static)
        self._list.setIconSize(QSize(72, 52))
        self._list.setObjectName("EquipmentPalette")
        self._list.setGridSize(QSize(112, 88))
        self._list.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(QLabel("Equipment Library", self))
        layout.addWidget(self._search)
        layout.addWidget(self._list, 1)
        self._search.textChanged.connect(self._filter_equipment)
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

    def bind_equipment_runtime(self, equipment_registry: Any, tool_manager: Any, properties_panel: Any | None = None, symbol_registry: Any | None = None) -> None:
        """Receive the canonical catalogue and live ToolManager from composition."""
        if equipment_registry is None or not callable(getattr(equipment_registry, "catalogue", None)):
            raise TypeError("equipment_registry must provide catalogue().")
        if tool_manager is None or not callable(getattr(tool_manager, "activate", None)):
            raise TypeError("tool_manager must provide activate().")
        if symbol_registry is None:
            raise TypeError("symbol_registry must be the canonical SymbolRegistry.")
        self._symbol_registry = symbol_registry
        self._palette_symbol_adapter = PaletteSymbolAdapter(symbol_registry)
        self._equipment_registry = equipment_registry
        self._tool_manager = tool_manager
        self._properties_panel = properties_panel
        self._definitions = tuple(equipment_registry.catalogue())
        self._rebuild_equipment_list()

    def _rebuild_equipment_list(self) -> None:
        query = self._search.text().strip().lower()
        self._visible_definitions = tuple(
            definition for definition in self._definitions
            if not query
            or query in str(definition.display_name).lower()
            or query in str(definition.category).lower()
            or query in str(definition.equipment_type).lower()
        )
        self._list.clear()
        last_category: str | None = None
        for definition in self._visible_definitions:
            category = str(definition.category)
            if category != last_category:
                self._list.addItem(f"— {category} —")
                header_item = self._list.item(self._list.count() - 1)
                header_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                header_item.setData(32, None)
                last_category = category
            self._list.addItem(definition.display_name)
            item = self._list.item(self._list.count() - 1)
            if self._palette_symbol_adapter is None:
                raise RuntimeError("Equipment palette symbol adapter is not configured.")
            item.setIcon(self._palette_symbol_adapter.icon_for(definition.symbol_id))
            item.setToolTip(
                f"{definition.display_name}\n"
                f"Category: {category}\n"
                f"Tool: {definition.tool_id}\n"
                f"Symbol: {definition.symbol_id}"
            )
            item.setData(32, definition.equipment_type)

    def _filter_equipment(self, _text: str) -> None:
        if self._equipment_registry is not None:
            self._rebuild_equipment_list()

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

        # Palette selection is an explicit user request to change equipment.
        # If another creation session is active, cancel that transient session
        # through ToolManager before requesting the new tool.  ToolManager
        # intentionally rejects implicit destruction of an active draft.
        active_tool_id = self._tool_manager.active_tool_id
        explicit_creation_switch = (
            active_tool_id is not None
            and active_tool_id != tool_id
        )

        tool = self._tool_manager.activate(
            tool_id,
            cancel_active_creation=explicit_creation_switch,
        )
        self._active_tool_id = self._tool_manager.active_tool_id
        if self._properties_panel is not None:
            setter = getattr(self._properties_panel, "set_creation_draft", None)
            if callable(setter):
                setter(self._tool_manager.creation_context.draft)
        return tool

    def configure_active_tool(self, **parameters: Any) -> None:
        """Compatibility adapter into the canonical CreationDraft."""
        if self._tool_manager is None:
            raise RuntimeError("Equipment Browser has not been composed with ToolManager.")
        if not parameters:
            raise ValueError("Creation parameters must not be empty.")
        self._tool_manager.creation_context.update_many(parameters)
        if self._properties_panel is not None:
            setter = getattr(self._properties_panel, "set_creation_draft", None)
            if callable(setter):
                setter(self._tool_manager.creation_context.draft)

    def _on_item_clicked(self, item: Any) -> None:
        equipment_type = item.data(32)
        if not equipment_type:
            return
        self.activate_equipment(str(equipment_type))


class PropertiesPanelWidget(QWidget):
    """Qt realization of the canonical PropertiesPanel projection."""

    _commit_future_completed = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GridForgePanel_properties")
        self.logical_panel = PropertiesPanel()
        self.logical_panel.on_create()
        self._engineering_editor: EngineeringParameterEditor | None = None
        self._application: Any | None = None
        self._parameter_controls: dict[str, QWidget] = {}
        self._parameter_states: dict[str, EngineeringParameterState] = {}
        self._apply_button: QPushButton | None = None
        self._validation_label: QLabel | None = None
        self._form_layout: QFormLayout | None = None
        self._creation_context: CreationContext | None = None
        self._creation_mode = False
        self._creation_controller: Any | None = None
        self._apply_changes_connected = True
        self._place_draft_connected = False
        self._commit_network_button: QPushButton | None = None
        self._commit_future_completed.connect(self._on_commit_future_completed)
        self._build_controls()

    def _build_controls(self) -> None:
        root = QVBoxLayout(self)
        self._form_layout = QFormLayout()
        root.addLayout(self._form_layout)
        self._annotation_layout = QFormLayout()
        root.addWidget(QLabel("SLD Data Annotations", self))
        root.addLayout(self._annotation_layout)
        self._sld_controller: Any | None = None
        self._sld_selection_ids: tuple[str, ...] = ()
        self._sld_annotations_cleared = False
        self._validation_label = QLabel("Select an element to inspect.", self)
        self._validation_label.setProperty("role", "validationInfo")
        self._validation_label.setWordWrap(True)
        root.addWidget(self._validation_label)
        self._apply_button = QPushButton("Apply / Commit", self)
        self._apply_button.setProperty("role", "primaryAction")
        self._apply_button.setEnabled(False)
        self._apply_button.clicked.connect(self._apply_changes)
        root.addWidget(self._apply_button)
        self._commit_network_button = QPushButton("Commit Network", self)
        self._commit_network_button.setProperty("role", "commitNetworkAction")
        self._commit_network_button.setEnabled(False)
        self._commit_network_button.clicked.connect(self._commit_network)
        root.addWidget(self._commit_network_button)

    def bind_configuration_runtime(self, application: Any, creation_context: CreationContext | None = None, controller: Any | None = None) -> None:
        self._application = application
        self._engineering_editor = EngineeringParameterEditor(application)
        self._creation_context = creation_context
        self._creation_controller = controller
        if controller is not None:
            signal = getattr(controller, "tool_changed", None)
            connect = getattr(signal, "connect", None)
            if callable(connect):
                connect(self._on_tool_changed)
            state_signal = getattr(controller, "state_changed", None)
            state_connect = getattr(state_signal, "connect", None)
            if callable(state_connect):
                state_connect(self._refresh_commit_network_action)
        self._refresh_commit_network_action()

    def bind_sld_annotation_runtime(self, *, controller: Any, selection_manager: Any) -> None:
        """Bind annotation editing to canonical SLD selection and Application commands."""
        if controller is None or not callable(getattr(controller, "set_annotation_blocks", None)):
            raise TypeError("controller must provide set_annotation_blocks().")
        if selection_manager is None or not callable(getattr(selection_manager, "select_single", None)):
            raise TypeError("selection_manager must be the canonical selection manager.")
        self._sld_controller = controller
        signal = getattr(selection_manager, "selection_changed", None)
        connect = getattr(signal, "connect", None)
        if not callable(connect):
            raise TypeError("selection_manager must expose selection_changed.connect().")
        connect(self._on_sld_selection_changed)
        self._refresh_sld_annotation_controls()

    def _on_sld_selection_changed(self, ids: Any) -> None:
        self._sld_selection_ids = tuple(str(value) for value in (ids or ()))
        if self._sld_annotations_cleared:
            self.clear_sld_annotation_controls()
            return
        self._refresh_sld_annotation_controls()

    def _selected_sld_node(self) -> Any | None:
        controller = self._sld_controller
        document = getattr(controller, "active_document", None) if controller is not None else None
        if document is None:
            return None
        if len(self._sld_selection_ids) != 1:
            return None
        selected_id = self._sld_selection_ids[0]
        node = document.model.get_node_optional(selected_id)
        if node is not None:
            return node
        return document.model.get_node_by_equipment_id_optional(selected_id)

    def refresh_sld_annotation_controls(self) -> None:
        """Refresh annotation controls while preserving the current selection."""
        self._sld_annotations_cleared = False
        self._refresh_sld_annotation_controls()

    def handle_sld_document_changed(self) -> None:
        """Drop selection IDs from the previous document before rebuilding controls."""
        self._sld_selection_ids = ()
        self._sld_annotations_cleared = False
        self._refresh_sld_annotation_controls()

    def clear_sld_annotation_controls(self) -> None:
        """Clear document-specific annotation controls when no SLD document is active."""
        self._sld_annotations_cleared = True
        self._sld_selection_ids = ()
        layout = getattr(self, "_annotation_layout", None)
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        layout.addRow(QLabel("No active SLD document.", self))

    def _refresh_sld_annotation_controls(self) -> None:
        layout = getattr(self, "_annotation_layout", None)
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        controller = self._sld_controller
        document = getattr(controller, "active_document", None) if controller is not None else None
        node = self._selected_sld_node()
        if document is None or node is None:
            layout.addRow(QLabel("Select one SLD node to configure its data annotation.", self))
            return

        blocks = [block.to_dict() for block in document.annotation_blocks if block.node_id == node.node_id]
        if not blocks:
            layout.addRow(QLabel(f"Node: {node.node_id} · no annotation block configured.", self))
        for block in blocks:
            block_id = str(block["block_id"])
            layout.addRow(QLabel(f"Block: {block_id}", self))
            fields_edit = QLineEdit(", ".join(block["fields"]), self)
            visible_check = QCheckBox("Visible", self)
            visible_check.setChecked(bool(block["visible"]))
            offset_x = QDoubleSpinBox(self)
            offset_y = QDoubleSpinBox(self)
            for control, key in ((offset_x, "offset_x"), (offset_y, "offset_y")):
                control.setRange(-1000000.0, 1000000.0)
                control.setDecimals(2)
                control.setValue(float(block[key]))
            layout.addRow("Fields", fields_edit)
            layout.addRow("Offset X", offset_x)
            layout.addRow("Offset Y", offset_y)
            layout.addRow(visible_check)
            save_button = QPushButton("Apply Annotation Changes", self)
            save_button.clicked.connect(
                lambda _checked=False, bid=block_id, fields=fields_edit, visible=visible_check,
                       ox=offset_x, oy=offset_y: self._save_sld_annotation(
                           bid, fields.text(), visible.isChecked(), ox.value(), oy.value()
                       )
            )
            remove_button = QPushButton("Remove Annotation", self)
            remove_button.clicked.connect(
                lambda _checked=False, bid=block_id: self._remove_sld_annotation(bid)
            )
            layout.addRow(save_button, remove_button)

        add_button = QPushButton("Add Data Annotation Block", self)
        add_button.clicked.connect(lambda _checked=False, nid=node.node_id: self._add_sld_annotation(nid))
        layout.addRow(add_button)

    def _save_sld_annotation(
        self, block_id: str, fields_text: str, visible: bool, offset_x: float, offset_y: float
    ) -> None:
        controller = self._sld_controller
        document = getattr(controller, "active_document", None) if controller is not None else None
        if document is None:
            return
        fields = [value.strip() for value in fields_text.split(",") if value.strip()]
        blocks = [block.to_dict() for block in document.annotation_blocks]
        found = False
        for block in blocks:
            if block["block_id"] == block_id:
                block.update(fields=fields, visible=visible, offset_x=offset_x, offset_y=offset_y)
                found = True
                break
        if not found:
            return
        try:
            controller.set_annotation_blocks(blocks)
        except (RuntimeError, TypeError, ValueError) as exc:
            if self._validation_label is not None:
                self._validation_label.setText(f"Annotation update rejected: {exc}")
            return
        self._refresh_sld_annotation_controls()

    def _add_sld_annotation(self, node_id: str) -> None:
        controller = self._sld_controller
        document = getattr(controller, "active_document", None) if controller is not None else None
        if document is None or document.model.get_node_optional(node_id) is None:
            return
        blocks = [block.to_dict() for block in document.annotation_blocks]
        blocks.append({
            "block_id": "annotation-" + uuid4().hex,
            "node_id": node_id,
            "visible": True,
            "fields": ["identity", "type"],
            "offset_x": 70.0,
            "offset_y": -20.0,
        })
        try:
            controller.set_annotation_blocks(blocks)
        except (RuntimeError, TypeError, ValueError) as exc:
            if self._validation_label is not None:
                self._validation_label.setText(f"Annotation creation rejected: {exc}")
            return
        self._refresh_sld_annotation_controls()

    def _remove_sld_annotation(self, block_id: str) -> None:
        controller = self._sld_controller
        document = getattr(controller, "active_document", None) if controller is not None else None
        if document is None:
            return
        blocks = [block.to_dict() for block in document.annotation_blocks if block.block_id != block_id]
        try:
            controller.set_annotation_blocks(blocks)
        except (RuntimeError, TypeError, ValueError) as exc:
            if self._validation_label is not None:
                self._validation_label.setText(f"Annotation removal rejected: {exc}")
            return
        self._refresh_sld_annotation_controls()

    def configure_parameter(self, parameter_id: str, value: Any) -> Any:
        if self._engineering_editor is None:
            raise RuntimeError("Properties configuration runtime is not bound.")
        target = self.logical_panel.target
        if target is None:
            raise RuntimeError("No projected element is selected.")
        intent = self._engineering_editor.intent_from_projection(target, {parameter_id: value})
        return self._engineering_editor.submit(intent)

    @property
    def target(self) -> Any | None:
        return self.logical_panel.target

    def set_target(self, target: Any | None) -> None:
        self._creation_mode = False
        self.logical_panel.set_target(target)
        self._render_projection(target)

    def set_creation_draft(self, draft: CreationDraft | None) -> None:
        if draft is None:
            self._creation_mode = False
            if self.logical_panel.target is None:
                self._render_projection(None)
            return
        self._creation_mode = True
        self.logical_panel.clear_target()
        self._render_creation_draft(draft)


    def clear_target(self) -> None:
        self.logical_panel.clear_target()
        if self._creation_context is not None and self._creation_context.draft is not None:
            self._creation_mode = True
            self._render_creation_draft(self._creation_context.draft)
        else:
            self._creation_mode = False
            self._render_projection(None)


    def _render_projection(self, target: ProjectionState | None) -> None:
        self._clear_parameter_controls()
        if target is None:
            if self._validation_label is not None:
                self._validation_label.setText("Select an element to inspect.")
                self._validation_label.setProperty("role", "validationInfo")
            if self._apply_button is not None:
                if not self._apply_changes_connected:
                    try:
                        self._apply_button.clicked.disconnect(self._place_draft)
                    except (RuntimeError, TypeError):
                        pass
                    self._place_draft_connected = False
                    self._apply_button.clicked.connect(self._apply_changes)
                    self._apply_changes_connected = True
                self._apply_button.setText("Apply / Commit")
                self._apply_button.setProperty("role", "primaryAction")
                self._apply_button.setEnabled(False)
            return
        self._parameter_states = {item.parameter_id: item for item in target.engineering_parameters}
        assert self._form_layout is not None
        self._form_layout.addRow(QLabel("Identity", self), QLabel(str(target.object_id), self))
        self._form_layout.addRow(QLabel("Type", self), QLabel(str(target.display_type), self))
        self._form_layout.addRow(
            QLabel("Status", self),
            QLabel("Draft" if target.identity_kind == "draft" else str(target.status or "Unknown"), self),
        )
        if target.identity_kind == "draft":
            self._form_layout.addRow(QLabel("Placement", self), QLabel(str(target.placement), self))
            self._form_layout.addRow(QLabel("Terminals", self), QLabel(", ".join(target.terminal_contract), self))
            if target.endpoint_references:
                self._form_layout.addRow(
                    QLabel("Acquired Endpoints", self),
                    QLabel(", ".join(f"{key}: {value}" for key, value in target.endpoint_references.items()), self),
                )
        if target.connectivity_refs:
            self._form_layout.addRow(QLabel("Connections", self), QLabel(", ".join(map(str, target.connectivity_refs)), self))
        self._form_layout.addRow(QLabel("Engineering Parameters", self), QLabel(
            f"{len(target.engineering_parameters)} projected parameter(s); Core validation remains authoritative.",
            self,
        ))
        for parameter in target.engineering_parameters:
            control = self._create_parameter_control(parameter)
            self._parameter_controls[parameter.parameter_id] = control
            assert self._form_layout is not None
            self._form_layout.addRow(self._parameter_label(parameter), control)
        if self._validation_label is not None:
            prefix = "Draft" if target.identity_kind == "draft" else target.display_type
            self._validation_label.setText(
                f"{prefix} {target.object_id} · "
                + ("DraftNetwork validation is authoritative until Commit Network." if target.identity_kind == "draft"
                   else "Core validation is authoritative on commit.")
            )
        if self._apply_button is not None:
            if self._place_draft_connected:
                try:
                    self._apply_button.clicked.disconnect(self._place_draft)
                except (RuntimeError, TypeError):
                    pass
                self._place_draft_connected = False
            if not self._apply_changes_connected:
                self._apply_button.clicked.connect(self._apply_changes)
                self._apply_changes_connected = True
            self._apply_button.setText("Apply Draft Changes" if target.identity_kind == "draft" else "Apply / Commit")
            self._apply_button.setProperty("role", "primaryAction")
            self._apply_button.setEnabled(
                any(item.editable and not item.derived for item in target.engineering_parameters)
            )

    def _refresh_commit_network_action(self, *args: Any) -> None:
        del args
        button = self._commit_network_button
        if button is None or self._engineering_editor is None:
            return
        application = self._application
        try:
            has_draft = bool(application is not None and application.read_draft_network())
        except (RuntimeError, TypeError, ValueError):
            has_draft = False
        button.setEnabled(has_draft)

    def _commit_network(self) -> None:
        controller = self._creation_controller
        commit = getattr(controller, "commit_network_async", None) if controller is not None else None
        if not callable(commit):
            if self._validation_label is not None:
                self._validation_label.setText("Non-blocking Commit Network action is not bound.")
                self._validation_label.setProperty("role", "validationError")
            return
        try:
            future = commit()
        except (RuntimeError, TypeError, ValueError) as exc:
            if self._validation_label is not None:
                self._validation_label.setText(str(exc))
                self._validation_label.setProperty("role", "validationError")
            return
        if self._commit_network_button is not None:
            self._commit_network_button.setEnabled(False)
            self._commit_network_button.setText("Committing Network…")
        if self._validation_label is not None:
            self._validation_label.setText("Validating and committing network in the background…")
            self._validation_label.setProperty("role", "validationInfo")
        future.add_done_callback(self._commit_future_completed.emit)

    def _on_commit_future_completed(self, future: Any) -> None:
        """Present worker completion on the Qt object's owning thread."""
        try:
            result = future.result()
        except ExecutionError as exc:
            self._abort_async_commit()
            cause = exc.cause or exc.__cause__
            reason = str(cause).strip() if cause is not None else ""
            normalized_reason = reason.lower()
            is_empty_draft_rejection = (
                exc.code == "COMMAND_EXECUTION_FAILED"
                and isinstance(cause, ValueError)
                and "empty" in normalized_reason
                and ("draft" in normalized_reason or "network" in normalized_reason)
            )
            if not is_empty_draft_rejection:
                logging.getLogger(__name__).error(
                    "Unexpected DraftNetwork commit execution failure",
                    exc_info=(type(exc), exc, exc.__traceback__),
                )
                message = str(exc)
            else:
                message = reason or "Draft network is empty. Add equipment or connections before committing."
            if self._validation_label is not None:
                self._validation_label.setText(message)
                self._validation_label.setProperty("role", "validationError")
        except (RuntimeError, TypeError, ValueError) as exc:
            self._abort_async_commit()
            if self._validation_label is not None:
                self._validation_label.setText(str(exc))
                self._validation_label.setProperty("role", "validationError")
        except BaseException as exc:
            self._abort_async_commit()
            logging.getLogger(__name__).exception("DraftNetwork background commit failed")
            if self._validation_label is not None:
                self._validation_label.setText(f"Network commit failed: {exc}")
                self._validation_label.setProperty("role", "validationError")
        else:
            controller = self._creation_controller
            complete = getattr(controller, "complete_network_commit", None) if controller is not None else None
            if callable(complete):
                try:
                    complete(result)
                except BaseException as exc:
                    self._abort_async_commit()
                    if self._validation_label is not None:
                        self._validation_label.setText(f"Network committed, but UI refresh failed: {exc}")
                        self._validation_label.setProperty("role", "validationError")
                    return
            if self._validation_label is not None:
                self._validation_label.setText(
                    getattr(result, "message", "Network commit completed.")
                )
                self._validation_label.setProperty("role", "validationSuccess")
        finally:
            if self._commit_network_button is not None:
                self._commit_network_button.setText("Commit Network")
            self._refresh_commit_network_action()

    def _abort_async_commit(self) -> None:
        controller = self._creation_controller
        abort = getattr(controller, "abort_network_commit", None) if controller is not None else None
        if callable(abort):
            try:
                abort()
            except Exception:
                logging.getLogger(__name__).exception("Failed to release asynchronous commit state")

    def _render_creation_draft(self, draft: CreationDraft) -> None:
        self._clear_parameter_controls()
        assert self._form_layout is not None
        for definition in draft.parameter_schema:
            control = self._create_creation_control(definition, draft.values.get(definition.parameter_id))
            self._parameter_controls[definition.parameter_id] = control
            self._form_layout.addRow(
                QLabel(
                    (f"{definition.display_name} *" if definition.required_before_create else definition.display_name) + (f" ({definition.unit})" if definition.unit else ""),
                    self,
                ),
                control,
            )
        errors = draft.validation_state.get("configuration", ())
        if self._validation_label is not None:
            self._validation_label.setText(
                f"Creating {draft.equipment_type}: " +
                ("Configuration complete." if draft.configuration_complete else "; ".join(errors))
            )
            self._validation_label.setProperty(
                "role",
                "validationSuccess" if draft.configuration_complete else "validationError",
            )
            try:
                self._validation_label.style().unpolish(self._validation_label)
                self._validation_label.style().polish(self._validation_label)
            except Exception:
                pass
        if self._apply_button is not None:
            self._apply_button.setText("Place Draft Equipment")
            self._apply_button.setProperty("role", "draftPlacementAction")
            # DraftNetwork accepts valid position-first authoring state.
            # Engineering completeness is validated at the explicit Commit
            # Network boundary, not as a prerequisite for draft placement.
            self._apply_button.setEnabled(draft.placement_position is not None)
            if self._apply_changes_connected:
                try:
                    self._apply_button.clicked.disconnect(self._apply_changes)
                except (RuntimeError, TypeError):
                    pass
                self._apply_changes_connected = False
            if not self._place_draft_connected:
                self._apply_button.clicked.connect(self._place_draft)
                self._place_draft_connected = True

    def _place_draft(self) -> None:
        if not self._creation_mode or self._creation_context is None:
            return
        controller = self._creation_controller
        commit = getattr(controller, "place_creation_draft", None) if controller is not None else None
        if not callable(commit):
            if self._validation_label is not None:
                self._validation_label.setText("Draft placement runtime is not bound.")
            return
        try:
            committed = bool(commit())
        except (RuntimeError, TypeError, ValueError) as exc:
            if self._validation_label is not None:
                self._validation_label.setText(str(exc))
            return
        if committed:
            self._creation_mode = False
            if self._apply_button is not None:
                if self._place_draft_connected:
                    try:
                        self._apply_button.clicked.disconnect(self._place_draft)
                    except (RuntimeError, TypeError):
                        pass
                    self._place_draft_connected = False
                if not self._apply_changes_connected:
                    self._apply_button.clicked.connect(self._apply_changes)
                    self._apply_changes_connected = True
                self._apply_button.setEnabled(False)
                self._apply_button.setText("Apply Draft Changes")
            target = self.logical_panel.target
            if target is not None:
                self._render_projection(target)

    def _create_creation_control(self, definition: Any, value: Any) -> QWidget:
        datatype = str(definition.datatype).strip().lower()
        if definition.derived or not definition.editable:
            return QLabel(self._display_value(value), self)
        if datatype in {"float", "number"}:
            control = QDoubleSpinBox(self)
            control.setDecimals(6)
            control.setRange(
                float(definition.minimum if definition.minimum is not None else -1.0e15),
                float(definition.maximum if definition.maximum is not None else 1.0e15),
            )
            if value is not None:
                control.setValue(float(value))
            control.valueChanged.connect(lambda new_value, pid=definition.parameter_id: self._update_creation_value(pid, float(new_value)))
            return control
        if datatype in {"bool", "boolean"}:
            control = QCheckBox(self)
            control.setChecked(bool(value))
            control.toggled.connect(lambda new_value, pid=definition.parameter_id: self._update_creation_value(pid, bool(new_value)))
            return control
        if datatype == "enum":
            control = QComboBox(self)
            choices = tuple(str(choice) for choice in definition.choices)
            control.addItems(choices)
            if value is not None and str(value) in choices:
                control.setCurrentText(str(value))
            control.currentTextChanged.connect(lambda new_value, pid=definition.parameter_id: self._update_creation_value(pid, str(new_value)))
            return control
        control = QLineEdit(self)
        control.setText("" if value is None else str(value))
        control.textChanged.connect(lambda new_value, pid=definition.parameter_id: self._update_creation_value(pid, new_value))
        return control

    def _update_creation_value(self, parameter_id: str, value: Any) -> None:
        if not self._creation_mode or self._creation_context is None:
            return
        try:
            draft = self._creation_context.update(parameter_id, value)
        except (TypeError, ValueError, KeyError):
            return
        errors = draft.validation_state.get("configuration", ())
        if self._validation_label is not None:
            self._validation_label.setText(
                f"Creating {draft.equipment_type}: " +
                ("Configuration complete." if draft.configuration_complete else "; ".join(errors))
            )

    def _on_tool_changed(self, current_tool_id: Any, previous_tool_id: Any) -> None:
        del current_tool_id, previous_tool_id
        if self._creation_context is None:
            return
        draft = self._creation_context.draft
        if draft is None:
            self._creation_mode = False
            if self.logical_panel.target is None:
                self._render_projection(None)
        else:
            self.set_creation_draft(draft)

    def _clear_parameter_controls(self) -> None:
        self._parameter_controls.clear()
        self._parameter_states.clear()
        if self._form_layout is None:
            return
        while self._form_layout.count():
            item = self._form_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _create_parameter_control(self, parameter: EngineeringParameterState) -> QWidget:
        value = parameter.value
        if parameter.derived or not parameter.editable:
            control = QLabel(self._display_value(value), self)
            control.setToolTip(self._validation_text(parameter))
            return control
        datatype = str(parameter.datatype).strip().lower()
        if datatype in {"float", "number"} and value is not None:
            control = QDoubleSpinBox(self)
            control.setDecimals(6)
            control.setRange(-1.0e15, 1.0e15)
            control.setValue(float(value))
            control.setToolTip(self._validation_text(parameter))
            return control
        if datatype in {"float", "number", "int", "integer"}:
            # Keep an unset numeric value visibly unset. A spin box would force
            # a fabricated zero into the editor and could submit it as a change.
            control = QLineEdit(self)
            control.setText("" if value is None else str(value))
            control.setToolTip(self._validation_text(parameter))
            return control
        if datatype in {"bool", "boolean"}:
            control = QCheckBox(self)
            control.setChecked(bool(value))
            control.setToolTip(self._validation_text(parameter))
            return control
        if datatype == "enum":
            control = QComboBox(self)
            choices = tuple(str(choice) for choice in parameter.choices)
            control.addItems(choices)
            if str(value) in choices:
                control.setCurrentText(str(value))
            control.setToolTip(self._validation_text(parameter))
            return control
        control = QLineEdit(self)
        control.setText("" if value is None else str(value))
        control.setToolTip(self._validation_text(parameter))
        return control

    def _parameter_label(self, parameter: EngineeringParameterState) -> QLabel:
        suffix: list[str] = []
        if parameter.unit:
            suffix.append(str(parameter.unit))
        if parameter.derived:
            suffix.append("derived / read-only")
        elif not parameter.editable:
            suffix.append("read-only")
        text = str(parameter.parameter_id)
        if suffix:
            text += " (" + ", ".join(suffix) + ")"
        return QLabel(text, self)

    @staticmethod
    def _display_value(value: Any) -> str:
        if isinstance(value, bool):
            return "True" if value else "False"
        return "" if value is None else str(value)

    @staticmethod
    def _validation_text(parameter: EngineeringParameterState) -> str:
        if parameter.validation.get("authoritative") == "Core":
            return "Core validation is authoritative."
        return "Presentation metadata only; Core remains authoritative."

    @staticmethod
    def _current_value(parameter: EngineeringParameterState, control: QWidget) -> Any:
        datatype = str(parameter.datatype).strip().lower()
        if datatype in {"float", "number"}:
            if isinstance(control, QLineEdit):
                text = control.text().strip()
                return None if not text else float(text)
            return float(control.value())  # type: ignore[attr-defined]
        if datatype in {"int", "integer"}:
            text = control.text().strip()  # type: ignore[attr-defined]
            return None if not text else int(text)
        if datatype in {"bool", "boolean"}:
            return bool(control.isChecked())  # type: ignore[attr-defined]
        if datatype == "enum":
            return str(control.currentText())  # type: ignore[attr-defined]
        return str(control.text())  # type: ignore[attr-defined]

    def _apply_changes(self) -> None:
        if self._engineering_editor is None:
            raise RuntimeError("Properties configuration runtime is not bound.")
        target = self.logical_panel.target
        if target is None:
            raise RuntimeError("No projected element is selected.")
        changes: dict[str, Any] = {}
        for parameter_id, parameter in self._parameter_states.items():
            if parameter.derived or not parameter.editable:
                continue
            value = self._current_value(parameter, self._parameter_controls[parameter_id])
            if value != parameter.value:
                changes[parameter_id] = value
        if not changes:
            if self._validation_label is not None:
                self._validation_label.setText("No engineering changes to commit.")
            return
        try:
            intent = self._engineering_editor.intent_from_projection(target, changes)
            result = self._engineering_editor.submit(intent)
        except (RuntimeError, TypeError, ValueError) as exc:
            if self._validation_label is not None:
                self._validation_label.setText(f"Engineering update rejected: {exc}")
            # Rebuild from the panel's current projection, not the target
            # captured before submission: selection may have changed while the
            # Application command was being handled.
            self._render_projection(self.logical_panel.target)
            return

        if not getattr(result, "success", False):
            message = getattr(result, "message", None) or "Engineering update was rejected."
            if self._validation_label is not None:
                self._validation_label.setText(f"Engineering update rejected: {message}")
            # The command failed, so DraftChanged is not authoritative evidence
            # of a mutation. Restore the currently selected projection; never
            # resurrect a previous target after a selection transition.
            self._render_projection(self.logical_panel.target)
            return

        if self._apply_button is not None:
            self._apply_button.setEnabled(False)
        if self._validation_label is not None:
            # Application events are published synchronously by execute(); the
            # projection coordinator may already have refreshed this panel.
            # Do not overwrite that completed refresh with a misleading
            # "waiting" status after control returns from the command path.
            self._validation_label.setText("Engineering update accepted.")



class IDMTTCCWorkspaceWidget(QWidget):
    """Read-only log-log overlay workspace for Application IDMT curve snapshots."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("IDMTTCCWorkspace")
        self._application: Any | None = None
        self._chart = QChart()
        self._chart.setTitle("Time–Current Characteristic (TCC)")
        self._chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)
        self._view = QChartView(self._chart, self)
        self._view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._status = QLabel(
            "No IDMT curves loaded. Configure ANSI 51/51N pickup, curve and TMS, then refresh.",
            self,
        )
        self._status.setWordWrap(True)
        self._refresh_button = QPushButton("Refresh Curves", self)
        self._refresh_button.setObjectName("RefreshIDMTTCC")
        self._primary_combo = QComboBox(self)
        self._backup_combo = QComboBox(self)
        self._scenario_source = QComboBox(self)
        self._scenario_source.addItem("Manual relay-input currents", "manual")
        self._scenario_source.addItem("Short-Circuit Study result", "short_circuit")
        self._short_circuit_result_combo = QComboBox(self)
        self._primary_branch_combo = QComboBox(self)
        self._backup_branch_combo = QComboBox(self)
        self._primary_branch_side = QComboBox(self)
        self._primary_branch_side.addItem("From bus", "from")
        self._primary_branch_side.addItem("To bus", "to")
        self._backup_branch_side = QComboBox(self)
        self._backup_branch_side.addItem("From bus", "from")
        self._backup_branch_side.addItem("To bus", "to")
        self._primary_current_scale = QLineEdit(self)
        self._primary_current_scale.setPlaceholderText("Required scale")
        self._backup_current_scale = QLineEdit(self)
        self._backup_current_scale.setPlaceholderText("Required scale")
        self._cti_input = QDoubleSpinBox(self)
        self._cti_input.setRange(0.0, 60.0)
        self._cti_input.setDecimals(4)
        self._cti_input.setSingleStep(0.05)
        self._cti_input.setValue(0.3)
        self._primary_currents = QLineEdit(self)
        self._primary_currents.setPlaceholderText("e.g. 800, 1200, 2500")
        self._backup_currents = QLineEdit(self)
        self._backup_currents.setPlaceholderText("e.g. 760, 1100, 2300")
        self._primary_unit = QLineEdit(self)
        self._primary_unit.setReadOnly(True)
        self._backup_unit = QLineEdit(self)
        self._backup_unit.setReadOnly(True)
        self._fault_location = QLineEdit(self)
        self._fault_location.setPlaceholderText("Optional fault bus / location ID")
        self._run_button = QPushButton("Run Coordination Study", self)
        self._run_button.setObjectName("RunIDMTCoordinationStudy")
        form = QFormLayout()
        form.addRow("Primary function", self._primary_combo)
        form.addRow("Backup function", self._backup_combo)
        form.addRow("Scenario source", self._scenario_source)
        form.addRow("Short-Circuit Study", self._short_circuit_result_combo)
        form.addRow("Primary branch", self._primary_branch_combo)
        form.addRow("Primary branch side", self._primary_branch_side)
        form.addRow("Primary scale (A primary → relay unit)", self._primary_current_scale)
        form.addRow("Backup branch", self._backup_branch_combo)
        form.addRow("Backup branch side", self._backup_branch_side)
        form.addRow("Backup scale (A primary → relay unit)", self._backup_current_scale)
        form.addRow("Required CTI (s)", self._cti_input)
        form.addRow("Primary relay-input currents (manual)", self._primary_currents)
        form.addRow("Backup relay-input currents", self._backup_currents)
        form.addRow("Primary unit (relay settings)", self._primary_unit)
        form.addRow("Backup unit (relay settings)", self._backup_unit)
        form.addRow("Fault location ID", self._fault_location)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self._refresh_button)
        layout.addLayout(form)
        layout.addWidget(self._run_button)
        layout.addWidget(self._status)
        layout.addWidget(self._view, 1)
        self._current_axis: QLogValueAxis | None = None
        self._time_axis: QLogValueAxis | None = None
        self._series: list[QLineSeries] = []
        self._curve_models: dict[str, Any] = {}
        self._short_circuit_results: dict[str, Any] = {}
        self._refresh_button.clicked.connect(self.refresh_curves)
        self._run_button.clicked.connect(self.run_coordination_study)
        self._primary_combo.currentIndexChanged.connect(self._sync_current_units)
        self._backup_combo.currentIndexChanged.connect(self._sync_current_units)
        self._short_circuit_result_combo.currentIndexChanged.connect(self._populate_branch_selectors)

    def bind_application(self, application: Any) -> None:
        """Bind the Application read boundary; no Core or Qt state crosses it."""
        if application is None or not callable(getattr(application, "read_idmt_curves", None)):
            raise TypeError("Application must expose read_idmt_curves().")
        self._application = application
        self.refresh_curves()

    def refresh_curves(self) -> None:
        """Refresh from the current immutable Application read snapshots."""
        if self._application is None:
            self._status.setText("TCC workspace is not bound to the active Application.")
            return
        try:
            models = self._application.read_idmt_curves()
            self._curve_models = {model.element_id: model for model in models}
            self.set_curve_read_models(models)
            self._populate_function_selectors(models)
            self._populate_short_circuit_results()
            self._sync_current_units()
        except (RuntimeError, TypeError, ValueError, KeyError) as exc:
            self._status.setText(f"Unable to load IDMT curves: {exc}")

    def _populate_function_selectors(self, models: Any) -> None:
        """Populate explicit primary/backup selectors from available ANSI 51 curves."""
        selected_primary = self._primary_combo.currentData()
        selected_backup = self._backup_combo.currentData()
        for combo in (self._primary_combo, self._backup_combo):
            combo.blockSignals(True)
            combo.clear()
            for model in models:
                combo.addItem(f"{model.display_name} [{model.function_code}] — {model.element_id}", model.element_id)
            combo.blockSignals(False)
        if selected_primary:
            index = self._primary_combo.findData(selected_primary)
            if index >= 0:
                self._primary_combo.setCurrentIndex(index)
        if selected_backup:
            index = self._backup_combo.findData(selected_backup)
            if index >= 0:
                self._backup_combo.setCurrentIndex(index)
        if self._backup_combo.count() > 1 and self._backup_combo.currentIndex() == 0:
            self._backup_combo.setCurrentIndex(1)

    def _populate_short_circuit_results(self) -> None:
        """List only current, completed Short-Circuit Study results."""
        from core.solver.short_circuit.result import ShortCircuitResult

        self._short_circuit_results = {}
        self._short_circuit_result_combo.blockSignals(True)
        self._short_circuit_result_combo.clear()
        for result in self._application.read_study_results():
            if (
                result.status != "completed"
                or not result.current
                or not isinstance(result.value, ShortCircuitResult)
            ):
                continue
            study_id = str(result.study_id)
            fault_bus_id = getattr(result.value, "fault_bus_id", "unknown bus")
            self._short_circuit_results[study_id] = result
            self._short_circuit_result_combo.addItem(
                f"{fault_bus_id} — {study_id}", study_id
            )
        self._short_circuit_result_combo.blockSignals(False)
        self._populate_branch_selectors()

    def _populate_branch_selectors(self, *_args: Any) -> None:
        """Populate explicit branch mappings from the selected Short-Circuit result."""
        study_id = self._short_circuit_result_combo.currentData()
        result_model = self._short_circuit_results.get(study_id)
        branch_ids = tuple(getattr(result_model.value, "branch_currents", {}).keys()) if result_model else ()
        for combo in (self._primary_branch_combo, self._backup_branch_combo):
            previous = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for branch_id in branch_ids:
                combo.addItem(str(branch_id), str(branch_id))
            if previous:
                index = combo.findData(previous)
                if index >= 0:
                    combo.setCurrentIndex(index)
            combo.blockSignals(False)
        if self._backup_branch_combo.count() > 1 and self._backup_branch_combo.currentIndex() == 0:
            self._backup_branch_combo.setCurrentIndex(1)

    def _sync_current_units(self, *_args: Any) -> None:
        """Display authoritative current-unit contracts from each selected relay."""
        primary = self._curve_models.get(self._primary_combo.currentData())
        backup = self._curve_models.get(self._backup_combo.currentData())
        self._primary_unit.setText(primary.current_unit or "" if primary is not None else "")
        self._backup_unit.setText(backup.current_unit or "" if backup is not None else "")

    @staticmethod
    def _parse_current_values(raw: str, field_name: str) -> tuple[float, ...]:
        values = []
        for index, token in enumerate(raw.split(",")):
            token = token.strip()
            if not token:
                raise ValueError(f"{field_name} contains an empty current at position {index + 1}.")
            value = float(token)
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{field_name} values must be finite and positive.")
            values.append(value)
        if not values:
            raise ValueError(f"{field_name} must contain at least one current.")
        return tuple(values)

    def run_coordination_study(self) -> None:
        """Create and execute one project-scoped coordination Study Case."""
        if self._application is None:
            self._status.setText("TCC workspace is not bound to the active Application.")
            return
        primary_id = self._primary_combo.currentData()
        backup_id = self._backup_combo.currentData()
        if not primary_id or not backup_id:
            self._status.setText("Select both a primary and a backup ANSI 51/51N function.")
            return
        if primary_id == backup_id:
            self._status.setText("Primary and backup functions must be different.")
            return
        try:
            from core.analysis.coordination_study import (
                CoordinationFaultScenario,
                CoordinationRelayCurrent,
                CoordinationStudyConfiguration,
                CoordinationStudyPair,
            )
            source = self._scenario_source.currentData()
            if source == "manual":
                primary_values = self._parse_current_values(
                    self._primary_currents.text(), "Primary relay-input currents"
                )
                backup_values = self._parse_current_values(
                    self._backup_currents.text(), "Backup relay-input currents"
                )
                if len(primary_values) != len(backup_values):
                    raise ValueError("Primary and backup current lists must contain the same number of scenarios.")
                primary_unit = self._primary_unit.text().strip()
                backup_unit = self._backup_unit.text().strip()
                if not primary_unit or not backup_unit:
                    raise ValueError(
                        "Both relay configurations must declare current_unit or pickup_unit. "
                        "No CT or base conversion is inferred."
                    )
                location = self._fault_location.text().strip()
                scenarios = tuple(
                    CoordinationFaultScenario(
                        scenario_id=f"SCENARIO-{index + 1:03d}",
                        currents_by_element_id={
                            str(primary_id): CoordinationRelayCurrent(primary_current, primary_unit),
                            str(backup_id): CoordinationRelayCurrent(backup_current, backup_unit),
                        },
                        fault_location_id=location,
                    )
                    for index, (primary_current, backup_current) in enumerate(zip(primary_values, backup_values))
                )
                pair = CoordinationStudyPair(str(primary_id), str(backup_id))
            elif source == "short_circuit":
                study_id = self._short_circuit_result_combo.currentData()
                result_model = self._short_circuit_results.get(study_id)
                primary_branch = self._primary_branch_combo.currentData()
                backup_branch = self._backup_branch_combo.currentData()
                if result_model is None or not primary_branch or not backup_branch:
                    raise ValueError("Select a completed Short-Circuit Study and both relay branch mappings.")
                try:
                    primary_scale = float(self._primary_current_scale.text())
                    backup_scale = float(self._backup_current_scale.text())
                except (TypeError, ValueError) as exc:
                    raise ValueError("Both current conversion scales are required and must be numeric.") from exc
                if not math.isfinite(primary_scale) or primary_scale <= 0.0:
                    raise ValueError("Primary current conversion scale must be finite and positive.")
                if not math.isfinite(backup_scale) or backup_scale <= 0.0:
                    raise ValueError("Backup current conversion scale must be finite and positive.")
                fault_location = str(result_model.value.fault_bus_id)
                scenarios = (
                    CoordinationFaultScenario(
                        scenario_id=f"SC-{str(study_id)[:8]}",
                        fault_location_id=fault_location,
                        short_circuit_study_id=str(study_id),
                    ),
                )
                pair = CoordinationStudyPair(
                    str(primary_id),
                    str(backup_id),
                    primary_branch_id=str(primary_branch),
                    backup_branch_id=str(backup_branch),
                    primary_branch_side=str(self._primary_branch_side.currentData()),
                    backup_branch_side=str(self._backup_branch_side.currentData()),
                    primary_current_scale=primary_scale,
                    backup_current_scale=backup_scale,
                )
            else:
                raise ValueError(f"Unsupported coordination scenario source: {source!r}.")
            configuration = CoordinationStudyConfiguration(
                pairs=(pair,),
                scenarios=scenarios,
                required_cti_s=self._cti_input.value(),
            )
            case = self._application.create_protection_coordination_study_case(configuration)
            execution = self._application.execute_study_case(case.study_id)
            result_model = self._application.read_study_result(case.study_id)
            if result_model is None or not result_model.current:
                self._status.setText("Coordination result is unavailable or stale for the active project revision.")
                return
            result = result_model.value
            if result is None:
                self._status.setText(f"Coordination study {execution.status.upper()} without a result payload.")
                return
            rows = [
                f"{point.scenario_id}: {point.status} | "
                f"source={point.source_study_id or 'manual'} | "
                f"Ip={point.primary_current:g} {point.primary_current_unit}, "
                f"Ib={point.backup_current:g} {point.backup_current_unit}, "
                f"tp={point.primary_time_s:.4g}s, tb={point.backup_time_s:.4g}s, "
                f"margin={point.margin_s:.4g}s, CTI={point.required_cti_s:.4g}s"
                for point in result.points
            ]
            self._status.setText(
                f"Study {execution.status.upper()} — {result.status}; "
                f"{result.pair_count} pair(s), {result.scenario_count} scenario(s).\n"
                + "\n".join(rows)
            )
        except (RuntimeError, TypeError, ValueError, KeyError) as exc:
            self._status.setText(f"Coordination study rejected: {exc}")


    def set_curve_read_models(self, models: Any) -> None:
        """Replace overlays from immutable IDMTCurveReadModel values only."""
        from core.application.read_models import IDMTCurveReadModel

        snapshots = tuple(models)
        if not all(isinstance(model, IDMTCurveReadModel) for model in snapshots):
            raise TypeError("TCC workspace accepts IDMTCurveReadModel values only.")
        if any(not model.points for model in snapshots):
            raise ValueError("Every displayed IDMT curve must contain plot points.")

        self._chart.removeAllSeries()
        for axis in (self._current_axis, self._time_axis):
            if axis is not None:
                self._chart.removeAxis(axis)
        self._series.clear()
        self._current_axis = None
        self._time_axis = None
        if not snapshots:
            self._status.setText("No ANSI 51/51N IDMT configurations are available.")
            return
        units = {model.current_unit for model in snapshots}
        if None in units or len(units) != 1:
            self._status.setText(
                "TCC overlay refused: every relay curve must declare the same current_unit. "
                "No CT/base conversion is inferred."
            )
            return
        current_unit = next(iter(units))

        currents = [point.current for model in snapshots for point in model.points]
        times = [point.operating_time_s for model in snapshots for point in model.points]
        if any(value <= 0.0 for value in currents + times):
            raise ValueError("Logarithmic TCC axes require positive current and time values.")

        current_axis = QLogValueAxis(self)
        current_axis.setBase(10.0)
        current_axis.setTitleText(f"Current ({current_unit})")
        current_axis.setLabelFormat("%.3g")
        current_axis.setRange(min(currents), max(currents))
        time_axis = QLogValueAxis(self)
        time_axis.setBase(10.0)
        time_axis.setTitleText("Operating time (s)")
        time_axis.setLabelFormat("%.3g")
        time_axis.setRange(min(times), max(times))
        self._chart.addAxis(current_axis, Qt.AlignmentFlag.AlignBottom)
        self._chart.addAxis(time_axis, Qt.AlignmentFlag.AlignLeft)
        self._current_axis = current_axis
        self._time_axis = time_axis

        for model in snapshots:
            series = QLineSeries(self._chart)
            unit_label = model.current_unit or "unit not declared"
            series.setName(
                f"{model.display_name} [{model.function_code} {model.curve}, "
                f"TMS={model.TMS:g}, {unit_label}]"
            )
            for point in model.points:
                series.append(point.current, point.operating_time_s)
            self._chart.addSeries(series)
            series.attachAxis(current_axis)
            series.attachAxis(time_axis)
            self._series.append(series)
        self._status.setText(f"Displaying {len(snapshots)} IDMT curve(s). Curves are read-only projections.")

PROJECT_PANEL = PanelSpec(panel_id="project", title="Project Explorer", metadata={"minimum_width": 230})
EQUIPMENT_PANEL = PanelSpec(panel_id="equipment", title="Equipment Browser", metadata={"minimum_width": 230})
PROPERTIES_PANEL = PanelSpec(panel_id="properties", title="Properties", metadata={"minimum_width": 300})
ELEMENT_LIST_PANEL = PanelSpec(panel_id="element_list", title="Element List", metadata={"minimum_height": 180})
MESSAGES_PANEL = PanelSpec(panel_id="messages", title="Messages / Events", metadata={"minimum_height": 150})
STUDY_CASES_PANEL = PanelSpec(panel_id="study_cases", title="Study Cases", metadata={"minimum_height": 150})
IDMT_TCC_PANEL = PanelSpec(panel_id="idmt_tcc", title="Protection TCC Coordination", metadata={"minimum_height": 260})

DEFAULT_PANEL_SPECS: tuple[PanelSpec, ...] = (
    PROJECT_PANEL,
    EQUIPMENT_PANEL,
    PROPERTIES_PANEL,
    ELEMENT_LIST_PANEL,
    MESSAGES_PANEL,
    STUDY_CASES_PANEL,
    IDMT_TCC_PANEL,
)

_PANEL_WIDGET_FACTORIES: dict[str, Callable[[QWidget | None], QWidget]] = {
    "project": ProjectPanelWidget,
    "equipment": EquipmentPanelWidget,
    "properties": PropertiesPanelWidget,
    "element_list": ElementListPanelWidget,
    "messages": MessagesPanelWidget,
    "study_cases": StudyCasesPanelWidget,
    "idmt_tcc": IDMTTCCWorkspaceWidget,
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
    if len(ids) != 7 or len(set(ids)) != 7:
        raise RuntimeError("Default panel IDs must be unique and complete.")
    return ids


__all__ = [
    "ProjectPanelWidget",
    "EquipmentPanelWidget",
    "PropertiesPanelWidget",
    "ElementListPanelWidget",
    "MessagesPanelWidget",
    "StudyCasesPanelWidget",
    "IDMTTCCWorkspaceWidget",
    "PROJECT_PANEL",
    "EQUIPMENT_PANEL",
    "PROPERTIES_PANEL",
    "ELEMENT_LIST_PANEL",
    "MESSAGES_PANEL",
    "STUDY_CASES_PANEL",
    "IDMT_TCC_PANEL",
    "DEFAULT_PANEL_SPECS",
    "create_panel_widget",
    "panel_spec_with_widget",
    "default_panel_specs",
    "default_panel_ids",
    "compose_default_panel_specs",
    "validate_default_panel_ids",
]
