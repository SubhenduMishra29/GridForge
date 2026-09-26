"""First-class Control/Ladder engineering workspace.

The workspace owns presentation composition only. Application/Core state is
always obtained from the injected Application read/command boundaries.
"""

from __future__ import annotations

from typing import Any

from ui.core.qt import QGraphicsView, QHBoxLayout, QVBoxLayout, QWidget, QLabel
from ui.canvas.control_canvas import ControlCanvas
from .control_tool_palette import ControlToolPalette
from .control_inspector import ControlInspector
from .control_toolbar import ControlToolbar
from .control_status_bar import ControlStatusBar
from .ladder.ladder_interaction import LadderInteraction
from .ladder.ladder_projection import LadderProjection


class _LadderView(QGraphicsView):
    def __init__(self, *, interaction: LadderInteraction, scene: ControlCanvas, parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self._interaction = interaction
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event) -> None:
        point = self.mapToScene(event.position().toPoint())
        self._interaction.preview(point.x(), point.y())
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event) -> None:
        if self._interaction.active_tool is not None and event.button() == 1:
            point = self.mapToScene(event.position().toPoint())
            self._interaction.place(point.x(), point.y())
            return
        super().mousePressEvent(event)


class ControlWorkspace(QWidget):
    """Engineer-facing Control workspace assembled from one Application boundary."""

    workspace_id = "control"

    def __init__(self, *, application: Any, controller: Any = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if application is None:
            raise ValueError("application is required.")
        self._application = application
        self._controller = controller
        self._canvas = ControlCanvas()
        self._projection = LadderProjection(self._canvas)
        self._interaction = LadderInteraction(application=application, canvas=self._canvas)
        self._palette = ControlToolPalette(application=application, on_selected=self._interaction.activate)
        self._inspector = ControlInspector(application=application)
        self._status = ControlStatusBar()
        self._toolbar = ControlToolbar(
            application=application,
            on_add_rung=self._add_rung,
            on_remove_rung=self._remove_rung,
            on_toggle_rung=self._toggle_rung,
            on_move_rung_up=self._move_rung_up,
            on_cancel_tool=self._interaction.cancel,
        )
        self._view = _LadderView(interaction=self._interaction, scene=self._canvas)
        self._canvas.selectionChanged.connect(self._selection_changed)

        root = QVBoxLayout(self)
        root.addWidget(self._toolbar)
        body = QHBoxLayout()
        body.addWidget(self._palette)
        body.addWidget(self._view, 1)
        body.addWidget(self._inspector)
        root.addLayout(body, 1)
        root.addWidget(self._status)

        self.refresh()
    
    @property
    def canvas(self) -> ControlCanvas:
        return self._canvas

    def refresh(self) -> None:
        try:
            read_model = self._application.read_control()
        except RuntimeError:
            return
        self._projection.project(read_model)
        self._status.set_status(f"Control: {len(read_model.rungs)} rung(s), {len(read_model.components)} component(s)")

    def _selection_changed(self) -> None:
        selected = self._canvas.selectedItems()
        component_id = selected[0].object_id if selected else None
        read_model = self._application.read_control()
        self._inspector.show_read_model(read_model, str(component_id) if component_id is not None else None)

    def _add_rung(self) -> None:
        from core.application.commands.control_commands import AddLadderRung
        count = len(self._application.read_control().rungs)
        self._application.execute(AddLadderRung(rung_id=f"rung-{count + 1:03d}", order=count))

    def _toggle_rung(self) -> None:
        from core.application.commands.control_commands import SetLadderRungEnabled
        model = self._application.read_control()
        if not model.rungs:
            return
        rung = model.rungs[-1]
        self._application.execute(SetLadderRungEnabled(rung_id=rung.rung_id, enabled=not rung.enabled))

    def _move_rung_up(self) -> None:
        from core.application.commands.control_commands import MoveLadderRung
        model = self._application.read_control()
        if not model.rungs:
            return
        rung = model.rungs[-1]
        self._application.execute(MoveLadderRung(rung_id=rung.rung_id, order=max(0, rung.order - 1)))

    def _remove_rung(self) -> None:
        model = self._application.read_control()
        if not model.rungs:
            return
        self._application.execute(__import__("core.application.commands.control_commands", fromlist=["RemoveLadderRung"]).RemoveLadderRung(rung_id=model.rungs[-1].rung_id))

    def dispose(self) -> None:
        self._interaction.cancel()


__all__ = ["ControlWorkspace"]
