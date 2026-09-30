"""Protection engineering workstation over Application read models.

Author: Subhendu Mishra

The Protection surface is a presentation projection. ProtectionDecision and
all electrical/protection truth remain Core/Application authority.
"""
from __future__ import annotations

from typing import Any

from core.application.events import ElementCreated, ElementRemoved, ElementUpdated, NetworkChanged, ProjectClosed, ProjectLoaded
from ui.canvas.canvas_framework import CanvasStateMachine
from ui.canvas.engineering_canvas_contract import CanvasInteractionAdapter
from ui.core.qt import (
    QGraphicsLineItem, QGraphicsRectItem, QGraphicsScene, QGraphicsTextItem,
    QGraphicsView, QGroupBox, QLabel, QListWidget, QPen, QSplitter, QToolBar,
    QVBoxLayout, QWidget,
)
from ui.core.selection_manager import SelectionManager


class ProtectionGraphicsNode(QGraphicsRectItem):
    """Selectable presentation node carrying one canonical object identity."""

    def __init__(self, object_id: str, title: str, x: float, y: float, width: float = 150.0) -> None:
        super().__init__(x, y, width, 52.0)
        self.object_id = str(object_id)
        self.title = str(title)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setToolTip(f"{self.title}\nID: {self.object_id}")


class ProtectionGraphicsSurface(QGraphicsView):
    """Actual graphical protection-scheme canvas backed only by read models."""

    def __init__(self, *, application: Any, selection_manager: SelectionManager,
                 adapter: CanvasInteractionAdapter, parent: QWidget | None = None) -> None:
        self._scene = QGraphicsScene()
        super().__init__(self._scene, parent)
        self.setObjectName("ProtectionEngineeringCanvas")
        self._application = application
        self._selection_manager = selection_manager
        self._adapter = adapter
        self._nodes: dict[str, ProtectionGraphicsNode] = {}
        self._scene.selectionChanged.connect(self._on_scene_selection)
        selection_manager.selection_changed.connect(self._on_canonical_selection)
        self.setMinimumHeight(360)

    def refresh(self) -> None:
        self._scene.clear()
        self._nodes.clear()
        try:
            protection = self._application.read_protection()
            network = self._application.read_network()
        except RuntimeError:
            self._draw_message("Protection read boundary unavailable.")
            return

        network_by_id = {str(e.object_id): e for e in network.elements}
        for relay_index, relay in enumerate(protection.relays):
            base_y = 30.0 + relay_index * 190.0
            input_nodes = []
            for index, binding in enumerate(relay.input_channel_bindings):
                channel_id = str(binding.channel_id or binding.input_name)
                source = network_by_id.get(channel_id)
                source_type = str(source.element_type).upper() if source is not None else "MEASUREMENT CHANNEL"
                input_nodes.append(self._add_node(
                    channel_id, f"{source_type}\n{binding.input_name}",
                    30.0, base_y + index * 62.0,
                ))
            relay_node = self._add_node(str(relay.object_id), f"RELAY\n{relay.name}\n{relay.function_type}", 270.0, base_y + 42.0, 170.0)
            function_node = self._add_node(f"{relay.object_id}:function", f"PROTECTION FUNCTION\n{relay.function_type}", 530.0, base_y + 42.0, 185.0)
            decision_node = self._add_node(f"{relay.object_id}:decision", f"DECISION\n{self._decision_text(relay)}", 805.0, base_y + 42.0, 150.0)
            trip_node = self._add_node(f"{relay.object_id}:trip", "TRIP OUTPUT", 1030.0, base_y + 42.0, 135.0)
            for node in input_nodes:
                self._link(node, relay_node)
            self._link(relay_node, function_node)
            self._link(function_node, decision_node)
            self._link(decision_node, trip_node)
        if self._scene.items():
            self.fitInView(self._scene.itemsBoundingRect().adjusted(-30, -30, 30, 30))

    def _add_node(self, object_id: str, title: str, x: float, y: float, width: float = 150.0) -> ProtectionGraphicsNode:
        node = ProtectionGraphicsNode(object_id, title.replace("\n", " | "), x, y, width)
        self._scene.addItem(node)
        self._nodes[object_id] = node
        text = QGraphicsTextItem(title, node)
        text.setPos(x + 8.0, y + 7.0)
        return node

    def _link(self, source: ProtectionGraphicsNode, target: ProtectionGraphicsNode) -> None:
        a = source.rect().center() + source.pos()
        b = target.rect().center() + target.pos()
        line = QGraphicsLineItem(a.x(), a.y(), b.x(), b.y())
        line.setPen(QPen())
        line.setZValue(-1)
        self._scene.addItem(line)

    def _on_scene_selection(self) -> None:
        selected = [item for item in self._scene.selectedItems() if isinstance(item, ProtectionGraphicsNode)]
        if selected:
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
        settings = dict(getattr(relay, "settings", {}) or {})
        if bool(settings.get("trip_request") or settings.get("tripped")):
            return "TRIP"
        if bool(settings.get("operate") or settings.get("operating")):
            return "OPERATING"
        if bool(settings.get("pickup") or settings.get("picked_up")):
            return "PICKUP"
        if bool(getattr(relay, "blocked", False)):
            return "BLOCKED"
        return "NO OPERATION"


class ProtectionExplorer(QListWidget):
    """Read-side relay explorer synchronized with canonical selection."""

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

    def _selection_changed(self, row: int) -> None:
        try:
            protection = self._application.read_protection()
        except RuntimeError:
            return
        if 0 <= row < len(protection.relays):
            self._selection_manager.select_single(protection.relays[row].object_id)

    def _selection_changed_from_manager(self, ids: object) -> None:
        selected = {str(value) for value in (ids or ())}
        if not selected:
            return
        try:
            protection = self._application.read_protection()
        except RuntimeError:
            return
        for row, relay in enumerate(protection.relays):
            if str(relay.object_id) in selected:
                self.blockSignals(True)
                self.setCurrentRow(row)
                self.blockSignals(False)
                return


class ProtectionInspector(QGroupBox):
    """Engineering-contextual protection inspector over immutable read data."""

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
        except RuntimeError:
            self._label.setText("Protection read boundary unavailable.")
            return
        relay_id = object_id.split(":", 1)[0]
        relay = next((item for item in protection.relays if str(item.object_id) == relay_id), None)
        if relay is None:
            self._label.setText(f"Protection presentation object: {object_id}")
            return
        settings = dict(relay.settings or {})
        self._label.setText("\n".join((
            "Identity", f"  {relay.object_id}",
            "Relay", f"  {relay.name} ({relay.relay_type})",
            "Function", f"  {relay.function_type}",
            "Measurement Inputs", f"  {len(relay.input_channel_bindings)}",
            "State", f"  {ProtectionGraphicsSurface._decision_text(relay)}",
            "In Service", f"  {relay.in_service}",
            "Enabled", f"  {relay.enabled}",
            "Blocked", f"  {relay.blocked}",
            "Pickup", f"  {settings.get('pickup', settings.get('picked_up', 'n/a'))}",
            "Operate", f"  {settings.get('operate', settings.get('operating', 'n/a'))}",
            "Trip Request", f"  {settings.get('trip_request', settings.get('tripped', 'n/a'))}",
            "Decision Reason", f"  {settings.get('decision_reason', settings.get('reason', 'n/a'))}",
            "Operating Time", f"  {settings.get('operating_time', 'n/a')}",
        )))


class ProtectionToolbar(QToolBar):
    """Protection actions are presentation controls; no Core mutation occurs here."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Protection Engineering", parent)
        for text in ("Select", "Connect Measurement", "Inspect", "Fit", "Diagnostics"):
            self.addAction(text)


class ProtectionWorkspace(QWidget):
    workspace_id = "protection"
    _EVENT_TYPES = (ElementCreated, ElementRemoved, ElementUpdated, NetworkChanged, ProjectLoaded, ProjectClosed)

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
        self._explorer = ProtectionExplorer(application, selection_manager, self)
        self._canvas = ProtectionGraphicsSurface(application=application, selection_manager=selection_manager, adapter=self._adapter, parent=self)
        self._inspector = ProtectionInspector(application=application, selection_manager=selection_manager, parent=self)
        self._toolbar = ProtectionToolbar(self)
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

    def refresh(self) -> None:
        self._explorer.refresh()
        self._canvas.refresh()
        self._inspector.refresh()

    def _on_application_event(self, _event: Any) -> None:
        self.refresh()

    def dispose(self) -> None:
        for event_type, handler in tuple(self._subscriptions):
            self._application.event_bus.unsubscribe(event_type, handler)
        self._subscriptions.clear()
        self._state_machine.cancel()


__all__ = ["ProtectionWorkspace", "ProtectionExplorer", "ProtectionGraphicsSurface", "ProtectionInspector", "ProtectionToolbar"]
