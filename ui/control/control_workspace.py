"""First-class Control/Ladder engineering workspace.

Author: Subhendu Mishra

The workspace owns UI selection/tool state only. Persistent Control state is
projected from the Application read model and mutated only by Application
commands.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from ui.core.qt import QGraphicsView, QHBoxLayout, QVBoxLayout, QWidget, QSplitter, Qt
from ui.canvas.control_canvas import ControlCanvas
from .control_tool_palette import ControlToolDescriptor, ControlToolPalette
from .control_inspector import ControlInspector
from .control_toolbar import ControlToolbar
from .control_status_bar import ControlStatusBar
from .ladder.ladder_interaction import LadderInteraction
from ui.events.control_update_coordinator import ControlUpdateCoordinator
from ui.core.selection_manager import SelectionManager


class _LadderView(QGraphicsView):
    def __init__(self, *, interaction: LadderInteraction, scene: ControlCanvas, parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self.setObjectName("ControlLadderView")
        self._interaction = interaction
        self.setMouseTracking(True)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def mouseMoveEvent(self, event) -> None:
        point = self.mapToScene(event.position().toPoint())
        self._interaction.preview(point.x(), point.y())
        super().mouseMoveEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        scene = self.scene()
        if scene is not None and scene.items():
            self.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)

    def mousePressEvent(self, event) -> None:
        if event.button() == 1:
            point = self.mapToScene(event.position().toPoint())
            if self._interaction.active_tool is not None:
                self._interaction.place(point.x(), point.y())
            else:
                self._interaction.select_at(point.x(), point.y())
            return
        super().mousePressEvent(event)


class ControlWorkspace(QWidget):
    """Engineer-facing Control workspace assembled from one Application boundary."""

    workspace_id = "control"

    def __init__(self, *, application: Any, controller: Any = None, selection_manager: SelectionManager | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if application is None:
            raise ValueError("application is required.")
        self._application = application
        self._controller = controller
        if selection_manager is None:
            raise ValueError("ControlWorkspace requires the canonical SelectionManager.")
        self._selection_manager = selection_manager
        self._canvas = ControlCanvas()
        self._inspector = ControlInspector(application=application)
        self._status = ControlStatusBar()
        self._interaction = LadderInteraction(
            application=application,
            canvas=self._canvas,
            on_rung_selected=self._on_rung_selected,
            on_component_selected=self._on_component_selected,
            on_connection_selected=self._on_connection_selected,
            on_status=self._status.set_status,
            selection_manager=selection_manager,
        )
        self._palette = ControlToolPalette(application=application, on_selected=self._tool_selected)
        self._toolbar = ControlToolbar(
            application=application,
            on_add_rung=self._add_rung,
            on_remove_rung=self._remove_rung,
            on_toggle_rung=self._toggle_rung,
            on_move_rung_up=self._move_rung_up,
            on_cancel_tool=self._interaction.cancel,
            on_execute_cycle=self._execute_cycle,
        )
        self._view = _LadderView(interaction=self._interaction, scene=self._canvas)
        self._selection_manager.selection_changed.connect(self._on_canonical_selection)
        self._coordinator = ControlUpdateCoordinator(
            application=application,
            canvas=self._canvas,
            canvas_refresh=self._presentation_refresh,
        )
        self._subscriptions: list[tuple[type, Any]] = []
        for event_type in self._coordinator.event_types:
            application.event_bus.subscribe(event_type, self._coordinator.refresh)
            self._subscriptions.append((event_type, self._coordinator.refresh))

        self._palette.setMinimumWidth(180)
        self._palette.setMaximumWidth(300)
        self._inspector.setMinimumWidth(280)
        self._inspector.setMaximumWidth(420)
        self._view.setMinimumWidth(500)
        root = QVBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(4)
        root.addWidget(self._toolbar)
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._palette)
        splitter.addWidget(self._view)
        splitter.addWidget(self._inspector)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([210, 800, 320])
        self._workspace_splitter = splitter
        root.addWidget(splitter, 1)
        root.addWidget(self._status)

        self.refresh()

    @property
    def canvas(self) -> ControlCanvas:
        return self._canvas

    @property
    def selected_rung_id(self) -> str | None:
        return self._interaction.selected_rung_id

    def refresh(self) -> None:
        self._coordinator.refresh_current()

    def _presentation_refresh(self) -> None:
        try:
            model = self._application.read_control()
            self._reconcile_selection(model)
            self._status.set_status(
                f"Control: {len(model.rungs)} rung(s), {len(model.components)} component(s)"
            )
            self._set_editing_enabled(True)
        except RuntimeError:
            self._interaction.clear_project_state()
            self._canvas.reset_scene()
            self._inspector.show_rung(
                type("_Empty", (), {"rungs": ()})(),
                None,
            )
            self._status.set_status("Control: no active project")
            self._set_editing_enabled(False)

    def _reconcile_selection(self, read_model: Any) -> None:
        rung_ids = {r.rung_id for r in read_model.rungs}
        if self._interaction.selected_rung_id not in rung_ids:
            self._interaction._select_rung(None)
        component_ids = {c.component_id for c in read_model.components}
        if self._interaction.selected_component_id not in component_ids:
            self._interaction._select_component(None)

    def _tool_selected(self, descriptor: ControlToolDescriptor) -> None:
        if descriptor.tool_id == "action_binding":
            self._interaction.cancel()
            try:
                model = self._application.read_control()
            except RuntimeError:
                self._status.set_status("Action Binding requires an active project.")
                return
            self._inspector.enter_action_binding_mode(model, self._interaction.selected_component_id)
            self._status.set_status("Action Binding mode: configure the selected logic output in the Inspector.")
            return
        if descriptor.tool_id == "control.interlock":
            self._interaction.cancel()
            self._status.set_status("Control Interlock mode: configure gating in the Inspector.")
            try:
                model = self._application.read_control()
                self._inspector.enter_control_interlock_mode(model, self._interaction.selected_component_id)
            except RuntimeError:
                return
            return
        self._interaction.activate(descriptor)

    def _on_canonical_selection(self, ids: object) -> None:
        """Project canonical selection into the Control presentation when mapped."""
        selected = {str(value) for value in (ids or ())}
        try:
            model = self._application.read_control()
        except RuntimeError:
            return
        component_ids = {str(component.component_id) for component in model.components}
        component_id = next((value for value in selected if value in component_ids), None)
        if component_id is None:
            return
        self._interaction._selected_component_id = component_id
        component = next((item for item in model.components if str(item.component_id) == component_id), None)
        self._canvas.clear_graphical_selection()
        item = self._canvas.find_item_by_object_id(component_id)
        if item is not None:
            item.setSelected(True)
        self._inspector.show_read_model(model, component_id)
        if component is not None and component.rung_id is not None:
            self._interaction._selected_rung_id = str(component.rung_id)

    def _on_rung_selected(self, rung_id: str | None) -> None:
        try:
            model = self._application.read_control()
        except RuntimeError:
            return
        if rung_id is None:
            self._inspector.show_rung(model, None)
            return
        self._inspector.show_rung(model, rung_id)
        self._status.set_status(f"Selected rung: {rung_id}")

    def _on_component_selected(self, component_id: str | None) -> None:
        self._canvas.clear_graphical_selection()
        if component_id is not None:
            item = self._canvas.find_item_by_object_id(component_id)
            if item is not None:
                item.setSelected(True)
        try:
            model = self._application.read_control()
        except RuntimeError:
            return
        self._inspector.show_read_model(model, component_id)

    def _on_connection_selected(self, identity: tuple[str, str, str, str] | None) -> None:
        if identity is not None:
            self._status.set_status(
                f"Selected connection: {identity[0]}.{identity[1]} -> {identity[2]}.{identity[3]}"
            )

    def _add_rung(self) -> None:
        try:
            model = self._application.read_control()
        except RuntimeError:
            return
        order = max((r.order for r in model.rungs), default=-1) + 1
        rung_id = f"rung-{order + 1:03d}-{uuid4().hex[:6]}"
        from core.application.commands.control_commands import AddLadderRung
        self._application.execute(AddLadderRung(rung_id=rung_id, order=order))
        self._interaction._select_rung(rung_id)

    def _selected_rung(self):
        try:
            model = self._application.read_control()
        except RuntimeError:
            return None
        return next(
            (r for r in model.rungs if r.rung_id == self._interaction.selected_rung_id),
            None,
        )

    def _toggle_rung(self) -> None:
        rung = self._selected_rung()
        if rung is None:
            self._status.set_status("Select a rung first.")
            return
        from core.application.commands.control_commands import SetLadderRungEnabled
        self._application.execute(SetLadderRungEnabled(rung_id=rung.rung_id, enabled=not rung.enabled))

    def _move_rung_up(self) -> None:
        rung = self._selected_rung()
        if rung is None:
            self._status.set_status("Select a rung first.")
            return
        from core.application.commands.control_commands import MoveLadderRung
        self._application.execute(MoveLadderRung(rung_id=rung.rung_id, order=max(0, rung.order - 1)))

    def _remove_rung(self) -> None:
        rung = self._selected_rung()
        if rung is None:
            self._status.set_status("Select a rung first.")
            return
        from core.application.commands.control_commands import RemoveLadderRung
        self._application.execute(RemoveLadderRung(rung_id=rung.rung_id))

    def _execute_cycle(self) -> None:
        try:
            result = self._application.execute_control_cycle()
        except Exception as exc:
            self._status.set_status(f"Control execution failed: {exc}")
            return
        simulation_time = getattr(result, "simulation_time", None)
        self._status.set_status("Control cycle completed" if simulation_time is None else f"Control cycle completed at t={simulation_time:g}")

    def _set_editing_enabled(self, enabled: bool) -> None:
        self._toolbar.set_editing_enabled(enabled)
        self._palette.setEnabled(bool(enabled))

    def dispose(self) -> None:
        self._interaction.clear_project_state()
        for event_type, handler in tuple(self._subscriptions):
            self._application.event_bus.unsubscribe(event_type, handler)
        self._subscriptions.clear()
        try:
            self._selection_manager.selection_changed.disconnect(self._on_canonical_selection)
        except (RuntimeError, TypeError):
            pass
        self._coordinator.dispose()


__all__ = ["ControlWorkspace"]
