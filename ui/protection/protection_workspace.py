# ============================================================
# File: ui/protection/protection_workspace.py
# GridForge V2 — Protection Engineering Workspace
# Author: Subhendu Mishra
# ============================================================
"""Protection engineering workstation over Application read models."""

from __future__ import annotations

from typing import Any

from core.application.events import (
    ElementCreated, ElementRemoved, ElementUpdated, NetworkChanged,
    ProtectionChanged, ProjectClosed, ProjectLoaded,
)
from ui.canvas.canvas_framework import CanvasStateMachine
from ui.canvas.engineering_canvas_contract import CanvasFeedback, CanvasInteractionAdapter
from ui.core.qt import (
    QAction, QGraphicsLineItem, QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem,
    QGraphicsView, QGroupBox, QLabel, QListWidget, QPen, QSplitter, QToolBar,
    QVBoxLayout, QWidget,
)
from ui.core.selection_manager import SelectionManager
from .protection_presentation import ProtectionPresentationDocument
from .protection_tools import ProtectionInteractionController


class ProtectionGraphicsNode(QGraphicsRectItem):
    """Selectable presentation node carrying canonical identity plus presentation role."""

    def __init__(self, object_id: str, title: str, x: float, y: float,
                 width: float = 150.0, *, kind: str = "object",
                 relay_id: str | None = None, input_name: str | None = None,
                 channel_id: str | None = None) -> None:
        super().__init__(0.0, 0.0, width, 52.0)
        self.setPos(float(x), float(y))
        self.object_id = str(object_id)
        self.title = str(title)
        self.kind = str(kind)
        self.relay_id = relay_id
        self.input_name = input_name
        self.channel_id = channel_id
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setToolTip(f"{self.title}\nID: {self.object_id}")


class ProtectionGraphicsSurface(QGraphicsView):
    """Projection-only Protection canvas; no Core mutation or persistence authority."""

    def __init__(self, *, application: Any, selection_manager: SelectionManager,
                 adapter: CanvasInteractionAdapter, interaction: ProtectionInteractionController,
                 presentation: ProtectionPresentationDocument, parent: QWidget | None = None) -> None:
        self._scene = QGraphicsScene()
        super().__init__(self._scene, parent)
        self.setObjectName("ProtectionEngineeringCanvas")
        self._application = application
        self._selection_manager = selection_manager
        self._adapter = adapter
        self._interaction = interaction
        self._presentation = presentation
        self._nodes: dict[str, ProtectionGraphicsNode] = {}
        self._scene.selectionChanged.connect(self._on_scene_selection)
        selection_manager.selection_changed.connect(self._on_canonical_selection)
        self.setMinimumHeight(360)

    @property
    def presentation(self) -> ProtectionPresentationDocument:
        return self._presentation

    def refresh(self) -> None:
        self._scene.clear()
        self._nodes.clear()
        try:
            protection = self._application.read_protection()
            configurations = self._application.read_protection_configuration()
        except RuntimeError:
            self._draw_message("Protection read boundary unavailable.")
            return

        configuration_by_relay: dict[str, list[Any]] = {}
        for configuration in configurations:
            configuration_by_relay.setdefault(str(configuration.relay_id), []).append(configuration)

        for relay_index, relay in enumerate(protection.relays):
            base_y = 30.0 + relay_index * 210.0
            relay_configs = configuration_by_relay.get(str(relay.object_id), ())
            input_names: list[str] = []
            for configuration in relay_configs:
                for input_name in configuration.input_channel_ids:
                    if input_name not in input_names:
                        input_names.append(str(input_name))

            input_nodes: list[ProtectionGraphicsNode] = []
            for index, input_name in enumerate(input_names):
                channel_id = None
                for configuration in relay_configs:
                    channel_id = configuration.input_channel_ids.get(input_name)
                    if channel_id:
                        break
                input_node = self._add_node(
                    f"{relay.object_id}:input:{input_name}",
                    f"RELAY INPUT\n{input_name}\n{channel_id or 'UNBOUND'}",
                    285.0, base_y + index * 62.0,
                    170.0,
                    kind="relay_input",
                    relay_id=str(relay.object_id),
                    input_name=input_name,
                    channel_id=str(channel_id) if channel_id else None,
                )
                input_nodes.append(input_node)
                if channel_id:
                    source_node = self._nodes.get(str(channel_id))
                    if source_node is None:
                        source_node = self._add_node(
                            str(channel_id),
                            f"MEASUREMENT CHANNEL\n{channel_id}",
                            30.0, base_y + index * 62.0,
                            190.0,
                            kind="measurement_channel",
                            channel_id=str(channel_id),
                        )
                    self._link(source_node, input_node, connection_id=f"{channel_id}->{relay.object_id}:{input_name}")

            relay_node = self._add_node(
                str(relay.object_id),
                f"RELAY\n{relay.name}\n{relay.function_type}",
                510.0, base_y + 30.0, 175.0,
                kind="relay",
            )
            for input_node in input_nodes:
                self._link(input_node, relay_node, connection_id=f"{input_node.object_id}->{relay.object_id}")

            function_node = self._add_node(
                f"{relay.object_id}:function",
                f"PROTECTION FUNCTION\n{relay.function_type}",
                735.0, base_y + 30.0, 190.0,
                kind="function",
            )
            decision_node = self._add_node(
                f"{relay.object_id}:decision",
                f"DECISION\n{self._decision_text(relay)}",
                980.0, base_y + 30.0, 165.0,
                kind="decision",
            )
            trip_node = self._add_node(
                f"{relay.object_id}:trip",
                "TRIP OUTPUT\nAPPLICATION BOUNDARY",
                1210.0, base_y + 30.0, 190.0,
                kind="trip_output",
            )
            self._link(relay_node, function_node, connection_id=f"{relay.object_id}->function")
            self._link(function_node, decision_node, connection_id=f"{relay.object_id}->decision")
            self._link(decision_node, trip_node, connection_id=f"{relay.object_id}->trip")

        if self._scene.items():
            self.fitInView(self._scene.itemsBoundingRect().adjusted(-30, -30, 30, 30))

    def _add_node(self, object_id: str, title: str, x: float, y: float, width: float = 150.0,
                  **metadata: Any) -> ProtectionGraphicsNode:
        stored = self._presentation.node(object_id, default_x=x, default_y=y)
        node = ProtectionGraphicsNode(
            object_id, title.replace("\n", " | "),
            float(stored.get("x", x)), float(stored.get("y", y)), width, **metadata,
        )
        self._scene.addItem(node)
        self._nodes[object_id] = node
        text = QGraphicsTextItem(title, node)
        text.setPos(8.0, 7.0)
        return node

    def _link(self, source: ProtectionGraphicsNode, target: ProtectionGraphicsNode, *, connection_id: str) -> None:
        stored = self._presentation.connections.get(connection_id)
        route = stored.get("route", ()) if isinstance(stored, dict) else ()
        if len(route) >= 2:
            start, end = route[0], route[-1]
            line = QGraphicsLineItem(float(start[0]), float(start[1]), float(end[0]), float(end[1]))
        else:
            a = source.sceneBoundingRect().center()
            b = target.sceneBoundingRect().center()
            line = QGraphicsLineItem(a.x(), a.y(), b.x(), b.y())
            self._presentation.set_connection_route(connection_id, [(a.x(), a.y()), (b.x(), b.y())])
        line.setPen(QPen())
        line.setZValue(-1)
        self._scene.addItem(line)

    def fit_to_content(self) -> None:
        items = self._scene.itemsBoundingRect()
        if not items.isNull():
            self.fitInView(items.adjusted(-30, -30, 30, 30))

    def show_diagnostics(self) -> None:
        self._adapter.feedback(CanvasFeedback.NONE, "Protection diagnostics are read-side only.")

    def mousePressEvent(self, event: Any) -> None:        item = self.itemAt(event.position().toPoint())
        if isinstance(item, QGraphicsTextItem):
            item = item.parentItem()
        if isinstance(item, ProtectionGraphicsNode):
            result = self._interaction.click_node(item)
            if result == "fit":
                self.fitInView(self._scene.itemsBoundingRect().adjusted(-30, -30, 30, 30))
            elif result == "diagnostics":
                self._adapter.feedback(CanvasFeedback.NONE, "Protection diagnostics are read-side only.")
            event.accept()
            return
        if self._interaction.active_tool == "select":
            self._selection_manager.clear()
        super().mousePressEvent(event)

    def _on_scene_selection(self) -> None:
        selected = [item for item in self._scene.selectedItems() if isinstance(item, ProtectionGraphicsNode)]
        if selected and self._interaction.active_tool == "select":
            self._selection_manager.select_single(selected[0].object_id)

    def _on_canonical_selection(self, ids: object) -> None:
        selected = {str(value) for value in (ids or ())}
        for object_id, node in self._nodes.items():
            node.setSelected(object_id in selected)

    def _draw_message(self, message: str) -> None:
        text = QGraphicsTextItem(message)
        self._scene.addItem(text)
        text.setPos(20.0, 20.0)

    @staticmethod
    def _decision_text(relay: Any) -> str:
        decision = getattr(relay, "decision", None)
        if decision is not None:
            if decision.blocked: return "BLOCKED"
            if not decision.valid: return "INVALID"
            if decision.trip_request: return "TRIP REQUEST"
            if decision.operate: return "OPERATING"
            if decision.pickup: return "PICKUP"
            return "NO OPERATION"
        if bool(getattr(relay, "tripped", False)): return "TRIP REQUEST"
        if bool(getattr(relay, "picked_up", False)): return "PICKUP"
        if bool(getattr(relay, "blocked", False)): return "BLOCKED"
        if not bool(getattr(relay, "enabled", True)): return "INVALID / DISABLED"
        return "NO OPERATION"


class ProtectionExplorer(QListWidget):
    """Read-side relay explorer synchronized with the canonical SelectionManager."""

    def __init__(self, application: Any, selection_manager: SelectionManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._application = application
        self._selection_manager = selection_manager
        self.currentRowChanged.connect(self._selection_changed)
        selection_manager.selection_changed.connect(self._selection_changed_from_manager)

    def refresh(self) -> None:
        self.clear()
        try:
            protection = self._application.read_protection()
        except RuntimeError:
            self.addItem("No active protection project")
            return
        for relay in protection.relays:
            self.addItem(f"{relay.name}  |  {relay.function_type}")
            self.item(self.count() - 1).setData(256, str(relay.object_id))

    def _selection_changed(self, row: int) -> None:
        if row < 0:
            return
        object_id = self.item(row).data(256) if self.item(row) is not None else None
        if object_id:
            self._selection_manager.select_single(object_id)

    def _selection_changed_from_manager(self, ids: object) -> None:
        selected = {str(value) for value in (ids or ())}
        if not selected:
            return
        for row in range(self.count()):
            if str(self.item(row).data(256)) in selected:
                self.blockSignals(True)
                self.setCurrentRow(row)
                self.blockSignals(False)
                return


class ProtectionInspector(QGroupBox):
    """Read-side engineering inspector; edits must use Application commands."""

    def __init__(self, *, application: Any, selection_manager: SelectionManager, parent: QWidget | None = None) -> None:
        super().__init__("Protection Inspector", parent)
        self._application = application
        self._selection_manager = selection_manager
        self._label = QLabel("Select a protection object.", self)
        self._label.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self._label)
        selection_manager.selection_changed.connect(lambda _ids: self.refresh())
        self.refresh()

    def refresh(self) -> None:
        selected = self._selection_manager.selected_ids
        if not selected:
            self._label.setText("Select a relay, measurement input, function or trip output.")
            return
        object_id = str(selected[0])
        try:
            protection = self._application.read_protection()
            configurations = self._application.read_protection_configuration()
        except RuntimeError:
            self._label.setText("Protection read boundary unavailable.")
            return
        relay_id = object_id.split(":", 1)[0]
        relay = next((item for item in protection.relays if str(item.object_id) == relay_id), None)
        if relay is None:
            self._label.setText(f"Protection presentation object: {object_id}")
            return
        settings = dict(relay.settings or {})
        configuration = next((item for item in configurations if str(item.relay_id) == relay_id), None)
        lines = [
            "Identity", f"  {relay.object_id}",
            "Relay", f"  {relay.name} ({relay.relay_type})",
            "Function", f"  {relay.function_type}",
            "Inputs", f"  {len(relay.input_channel_bindings)}",
            "State", f"  {ProtectionGraphicsSurface._decision_text(relay)}",
            "In Service", f"  {relay.in_service}",
            "Enabled", f"  {relay.enabled}",
            "Blocked", f"  {relay.blocked}",
        ]
        if configuration is not None:
            lines.extend([
                "Configuration", f"  {configuration.element_id}",
                "Configured Inputs", f"  {dict(configuration.input_channel_ids)}",
            ])
        decision = getattr(relay, "decision", None)
        if decision is not None:
            lines.extend([
                "ProtectionDecision", f"  {type(decision).__name__}",
                "Pickup", f"  {decision.pickup}",
                "Operate", f"  {decision.operate}",
                "Trip Request", f"  {decision.trip_request}",
                "Blocked", f"  {decision.blocked}",
                "Valid", f"  {decision.valid}",
                "Reason", f"  {decision.reason or 'n/a'}",
                "Operating Time", f"  {decision.operating_time if decision.operating_time is not None else 'n/a'}",
            ])
        else:
            lines.extend([
                "Pickup", f"  {settings.get('pickup', settings.get('picked_up', 'n/a'))}",
                "Operate", f"  {settings.get('operate', settings.get('operating', 'n/a'))}",
                "Trip Request", f"  {settings.get('trip_request', settings.get('tripped', 'n/a'))}",
                "Decision Reason", f"  {settings.get('decision_reason', settings.get('reason', 'n/a'))}",
                "Operating Time", f"  {settings.get('operating_time', 'n/a')}",
            ])
        self._label.setText("\n".join(lines))


class ProtectionToolbar(QToolBar):
    """Canonical Protection tool activation surface."""

    def __init__(self, interaction: ProtectionInteractionController, *, on_fit: Any = None, on_diagnostics: Any = None, parent: QWidget | None = None) -> None:
        super().__init__("Protection Engineering", parent)
        self._actions: dict[str, QAction] = {}
        self._on_fit = on_fit
        self._on_diagnostics = on_diagnostics
        for tool_id, text in (
            ("select", "Select"),
            ("connect_measurement", "Connect Measurement"),
            ("inspect", "Inspect"),
            ("fit", "Fit"),
            ("diagnostics", "Diagnostics"),
        ):
            action = self.addAction(text)
            action.setCheckable(tool_id in {"select", "connect_measurement", "inspect"})
            if tool_id in {"select", "connect_measurement", "inspect"}:
                action.triggered.connect(lambda _checked=False, value=tool_id: interaction.activate(value))
            elif tool_id == "fit" and callable(on_fit):
                action.triggered.connect(lambda _checked=False: on_fit())
            elif tool_id == "diagnostics" and callable(on_diagnostics):
                action.triggered.connect(lambda _checked=False: on_diagnostics())
            self._actions[tool_id] = action
        self._actions["select"].setChecked(True)

    def set_active(self, tool_id: str) -> None:
        for key, action in self._actions.items():
            action.setChecked(key == tool_id)


class ProtectionWorkspace(QWidget):
    workspace_id = "protection"
    _EVENT_TYPES = (
        ElementCreated, ElementRemoved, ElementUpdated, NetworkChanged,
        ProtectionChanged, ProjectLoaded, ProjectClosed,
    )

    def __init__(self, *, application: Any, selection_manager: SelectionManager | None = None,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if application is None:
            raise ValueError("application is required.")
        if selection_manager is None:
            raise ValueError("ProtectionWorkspace requires the canonical SelectionManager.")
        self._application = application
        self._selection_manager = selection_manager
        self._state_machine = CanvasStateMachine(workspace_id=self.workspace_id)
        self._adapter = CanvasInteractionAdapter(workspace_id=self.workspace_id, discipline=self.workspace_id)
        self._interaction = ProtectionInteractionController(
            application=application,
            selection_manager=selection_manager,
            adapter=self._adapter,
        )
        existing = getattr(application, "protection_presentation", None)
        self._presentation = (
            existing if isinstance(existing, ProtectionPresentationDocument)
            else ProtectionPresentationDocument.from_dict(existing)
            if isinstance(existing, dict) else ProtectionPresentationDocument()
        )        application.protection_presentation = self._presentation
        self._explorer = ProtectionExplorer(application, selection_manager, self)
        self._canvas = ProtectionGraphicsSurface(
            application=application,
            selection_manager=selection_manager,
            adapter=self._adapter,
            interaction=self._interaction,
            presentation=self._presentation,
            parent=self,
        )
        self._inspector = ProtectionInspector(application=application, selection_manager=selection_manager, parent=self)
        self._toolbar = ProtectionToolbar(
            self._interaction,
            on_fit=self._canvas.fit_to_content,
            on_diagnostics=self._canvas.show_diagnostics,
            parent=self,
        )
        self._subscriptions: list[tuple[Any, Any]] = []
        for event_type in self._EVENT_TYPES:
            application.event_bus.subscribe(event_type, self._on_application_event)
            self._subscriptions.append((event_type, self._on_application_event))
        splitter = QSplitter(parent=self)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._explorer)
        splitter.addWidget(self._canvas)
        splitter.addWidget(self._inspector)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.addWidget(self._toolbar)
        layout.addWidget(splitter, 1)
        self.refresh()

    @property
    def selection_manager(self) -> SelectionManager:
        return self._selection_manager

    @property
    def canvas_state(self):
        return self._state_machine.state

    @property
    def presentation(self) -> ProtectionPresentationDocument:
        return self._presentation

    def refresh(self) -> None:
        self._explorer.refresh()
        self._canvas.refresh()
        self._inspector.refresh()
        self._toolbar.set_active(self._interaction.active_tool)

    def _on_application_event(self, event: Any) -> None:
        if isinstance(event, ProjectClosed):
            self._interaction.cancel()
            self._presentation.clear()
            self._selection_manager.clear()
        elif isinstance(event, ProjectLoaded):
            loaded = getattr(self._application, "protection_presentation", None)
            if isinstance(loaded, dict):
                restored = ProtectionPresentationDocument.from_dict(loaded)
                self._presentation.clear()
                self._presentation.nodes.update(restored.nodes)
                self._presentation.connections.update(restored.connections)
                self._application.protection_presentation = self._presentation        self.refresh()
    def dispose(self) -> None:
        for event_type, handler in tuple(self._subscriptions):
            self._application.event_bus.unsubscribe(event_type, handler)
        self._subscriptions.clear()
        self._interaction.dispose()
        self._state_machine.cancel()


__all__ = [
    "ProtectionWorkspace", "ProtectionExplorer", "ProtectionGraphicsSurface",
    "ProtectionInspector", "ProtectionToolbar",
]
