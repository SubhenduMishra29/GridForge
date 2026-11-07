"""
GridForge V2 — Canvas Graphics View
===================================

File:
    ui/canvas/graphics_view.py

Purpose
-------
Thin Qt viewport boundary for the GridForge SLD canvas.

Architectural role
------------------
GraphicsView is a Qt viewport boundary. Canvas services are composed
outside the view and injected into it.

It does not:
    - create Presentation controllers;
    - create ToolManager;
    - create InteractionManager;
    - create NavigationController;
    - own tool lifecycle;
    - perform electrical calculations;
    - modify Core state;
    - construct domain objects.

The Application layer is the explicit Core↔UI integration boundary.
GraphicsView does not bypass that boundary.

Author:
    Subhendu Mishra
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QBrush, QGraphicsScene, QGraphicsView, QPainter, QPointF, Qt, Signal, QHBoxLayout, QToolButton, QWidget
from ui.styling.presentation_style import token_color
from ui.canvas.interaction_manager import InteractionManager
from ui.canvas.navigation_controller import NavigationController


class GraphicsView(QGraphicsView):
    """Canonical GridForge Canvas viewport."""

    cursor_scene_position = Signal(object)

    def __init__(
        self,
        controller: Any,
        tool_manager: Any,
        *,
        scene: QGraphicsScene,
        interaction_manager: Optional[InteractionManager] = None,
        navigation_controller: Optional[NavigationController] = None,
        parent: Optional[Any] = None,
    ) -> None:
        if controller is None:
            raise ValueError("controller must not be None.")
        if tool_manager is None:
            raise ValueError("tool_manager must not be None.")
        if scene is None:
            raise ValueError("scene must not be None.")

        super().__init__(parent)
        self.controller = controller
        self.tool_manager = tool_manager
        self._scene = scene
        self._last_cursor_scene_position: tuple[float, float] | None = None
        self.interaction_manager = interaction_manager
        self.navigation_controller = navigation_controller

        if self._scene.parent() is None:
            self._scene.setParent(self)
        self.setScene(self._scene)
        self.setObjectName("SLDCanvasView")
        self.setBackgroundBrush(QBrush(token_color("canvas_background")))
        # Electrical symbols and connection routes are vector geometry. Enable
        # predictable edge/text quality while keeping the view's update policy
        # incremental for interactive edits.
        self.setRenderHints(
            self.renderHints()
            | QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
        )
        self.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate
        )
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Transient, selection-aware presentation controls. This overlay is a
        # viewport child and never becomes part of the persistent SLD scene.
        self._contextual_strip = QWidget(self.viewport())
        self._contextual_strip.setObjectName("SLDContextualToolStrip")
        self._contextual_strip.setStyleSheet(
            "QWidget#SLDContextualToolStrip { background: #263442; "
            "border: 1px solid #526579; border-radius: 5px; } "
            "QToolButton { color: #f2f5f8; padding: 4px 7px; border: 0; } "
            "QToolButton:hover { background: #40566b; }"
        )
        strip_layout = QHBoxLayout(self._contextual_strip)
        strip_layout.setContentsMargins(4, 3, 4, 3)
        strip_layout.setSpacing(2)
        for label, tooltip, operation in (
            ("↶", "Rotate selected symbol 90° counter-clockwise", "rotate_ccw"),
            ("↷", "Rotate selected symbol 90° clockwise", "rotate_cw"),
            ("Flip H", "Mirror selected symbol horizontally", "flip_h"),
            ("Flip V", "Mirror selected symbol vertically", "flip_v"),
        ):
            button = QToolButton(self._contextual_strip)
            button.setText(label)
            button.setToolTip(tooltip)
            button.setAccessibleName(tooltip)
            button.clicked.connect(
                lambda _checked=False, op=operation: self._apply_contextual_symbol_action(op)
            )
            strip_layout.addWidget(button)
        self._annotation_quadrant_button = QToolButton(self._contextual_strip)
        self._annotation_quadrant_button.setToolTip(
            "Cycle selected equipment annotations through top-right, top-left, bottom-right, and bottom-left quadrants"
        )
        self._annotation_quadrant_button.setAccessibleName("Change annotation quadrant")
        self._annotation_quadrant_button.clicked.connect(self._cycle_contextual_annotation_quadrant)
        strip_layout.addWidget(self._annotation_quadrant_button)
        self._contextual_strip.hide()
        self._scene.selectionChanged.connect(self._refresh_contextual_tool_strip)
        self.horizontalScrollBar().valueChanged.connect(self._refresh_contextual_tool_strip)
        self.verticalScrollBar().valueChanged.connect(self._refresh_contextual_tool_strip)

    def bind_services(
        self,
        *,
        interaction_manager: InteractionManager,
        navigation_controller: NavigationController,
    ) -> None:
        if interaction_manager is None:
            raise ValueError("interaction_manager must not be None.")
        if navigation_controller is None:
            raise ValueError("navigation_controller must not be None.")
        if self.interaction_manager is not None:
            raise RuntimeError("interaction_manager is already bound.")
        if self.navigation_controller is not None:
            raise RuntimeError("navigation_controller is already bound.")
        self.interaction_manager = interaction_manager
        self.navigation_controller = navigation_controller

    @property
    def graphics_scene(self) -> QGraphicsScene:
        return self._scene

    @property
    def last_cursor_scene_position(self) -> tuple[float, float] | None:
        return self._last_cursor_scene_position

    def _selected_presentation_node(self):
        """Return the sole selected SLD node and its symbol graphics item."""
        document = getattr(self.controller, "active_document", None)
        if document is None:
            return None, None
        selected = tuple(
            item for item in self._scene.selectedItems()
            if getattr(item, "object_id", None) is not None
            and getattr(item, "symbol_instance", None) is not None
        )
        if len(selected) != 1:
            return None, None
        item = selected[0]
        node_id = str(item.object_id)
        model = getattr(document, "model", None)
        if model is None or not model.has_node(node_id):
            return None, None
        node = model.get_node(node_id)
        if node.presentation is None and getattr(item, "symbol_instance", None) is None:
            return None, None
        return node, item

    def _refresh_contextual_tool_strip(self, *_args) -> None:
        """Anchor the transient strip to the selected symbol in viewport space."""
        node, item = self._selected_presentation_node()
        if node is None or item is None:
            self._contextual_strip.hide()
            return
        document = getattr(self.controller, "active_document", None)
        annotation_blocks = tuple(
            block for block in getattr(document, "annotation_blocks", ())
            if block.node_id == node.node_id
        )
        self._annotation_quadrant_button.setEnabled(bool(annotation_blocks))
        quadrants = ("top_right", "top_left", "bottom_right", "bottom_left")
        current = {block.quadrant for block in annotation_blocks}
        next_quadrant = "top_right"
        if len(current) == 1:
            value = next(iter(current))
            if value in quadrants:
                next_quadrant = quadrants[(quadrants.index(value) + 1) % len(quadrants)]
        arrow = {"top_right": "↗", "top_left": "↖", "bottom_right": "↘", "bottom_left": "↙"}[next_quadrant]
        self._annotation_quadrant_button.setText("Label " + arrow)
        bounds = item.mapRectToScene(item.boundingRect())
        anchor = self.mapFromScene(bounds.topRight())
        self._contextual_strip.adjustSize()
        width = self._contextual_strip.sizeHint().width()
        height = self._contextual_strip.sizeHint().height()
        x = min(max(4, anchor.x() + 8), max(4, self.viewport().width() - width - 4))
        y = min(max(4, anchor.y() - height - 8), max(4, self.viewport().height() - height - 4))
        self._contextual_strip.move(x, y)
        self._contextual_strip.show()
        self._contextual_strip.raise_()

    def _cycle_contextual_annotation_quadrant(self) -> None:
        """Persist annotation placement through the existing Application command path."""
        node, _item = self._selected_presentation_node()
        document = getattr(self.controller, "active_document", None)
        if node is None or document is None:
            return
        blocks = tuple(getattr(document, "annotation_blocks", ()))
        selected_blocks = tuple(block for block in blocks if block.node_id == node.node_id)
        if not selected_blocks:
            return
        quadrants = ("top_right", "top_left", "bottom_right", "bottom_left")
        current = {block.quadrant for block in selected_blocks}
        next_quadrant = "top_right"
        if len(current) == 1:
            value = next(iter(current))
            if value in quadrants:
                next_quadrant = quadrants[(quadrants.index(value) + 1) % len(quadrants)]
        updated = []
        for block in blocks:
            payload = block.to_dict()
            if block.node_id == node.node_id:
                payload["quadrant"] = next_quadrant
            updated.append(payload)
        self.controller.set_annotation_blocks(updated)
        self._refresh_contextual_tool_strip()

    def _apply_contextual_symbol_action(self, operation: str) -> None:
        """Persist a symbol-only transform through the SLD Application command."""
        from ui.equipment.symbol.symbol_base import SymbolBase

        node, item = self._selected_presentation_node()
        if node is None:
            return
        source = node.presentation or item.symbol_instance
        presentation = SymbolBase.from_dict(source.to_dict())
        if operation == "rotate_ccw":
            presentation.rotation = (presentation.rotation - 90.0) % 360.0
        elif operation == "rotate_cw":
            presentation.rotation = (presentation.rotation + 90.0) % 360.0
        elif operation == "flip_h":
            presentation.set_property("mirror_x", not bool(presentation.get_property("mirror_x", False)))
        elif operation == "flip_v":
            presentation.set_property("mirror_y", not bool(presentation.get_property("mirror_y", False)))
        else:
            raise ValueError(f"Unsupported contextual symbol action: {operation}")
        self.controller.set_node_presentation(node.node_id, presentation)
        self._refresh_contextual_tool_strip()

    def mousePressEvent(self, event: Any) -> None:
        if self.interaction_manager is not None and self.interaction_manager.mouse_press(event):
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Any) -> None:
        # mapToScene(QPoint) rounds/truncates QPointF mouse positions to
        # integer viewport coordinates. Invert the current viewport transform
        # instead so cursor feedback remains aligned during pan and placement.
        viewport_position = (
            event.position()
            if callable(getattr(event, "position", None))
            else QPointF(float(event.pos().x()), float(event.pos().y()))
        )
        inverse, invertible = self.viewportTransform().inverted()
        if invertible:
            point = inverse.map(
                QPointF(float(viewport_position.x()), float(viewport_position.y()))
            )
        else:
            integer_position = (
                viewport_position.toPoint()
                if callable(getattr(viewport_position, "toPoint", None))
                else event.pos()
            )
            point = self.mapToScene(integer_position)
        self._last_cursor_scene_position = (float(point.x()), float(point.y()))
        self.cursor_scene_position.emit(self._last_cursor_scene_position)
        if self.interaction_manager is not None and self.interaction_manager.mouse_move(event):
            self._refresh_contextual_tool_strip()
            return
        super().mouseMoveEvent(event)
        self._refresh_contextual_tool_strip()

    def mouseReleaseEvent(self, event: Any) -> None:
        if self.interaction_manager is not None and self.interaction_manager.mouse_release(event):
            self._refresh_contextual_tool_strip()
            return
        super().mouseReleaseEvent(event)
        self._refresh_contextual_tool_strip()

    def mouseDoubleClickEvent(self, event: Any) -> None:
        if self.interaction_manager is not None and self.interaction_manager.mouse_double_click(event):
            return
        super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event: Any) -> None:
        if self.navigation_controller is not None and self.navigation_controller.handle_wheel(event):
            self._refresh_contextual_tool_strip()
            return
        super().wheelEvent(event)
        self._refresh_contextual_tool_strip()

    def keyPressEvent(self, event: Any) -> None:
        if self.interaction_manager is not None and self.interaction_manager.key_press(event):
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: Any) -> None:
        if self.interaction_manager is not None and self.interaction_manager.key_release(event):
            return
        super().keyReleaseEvent(event)

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        self._refresh_contextual_tool_strip()

    def dispose(self) -> None:
        self.interaction_manager = None
        self.navigation_controller = None
        self._contextual_strip.hide()
        self.controller = None
        self.tool_manager = None


__all__ = ["GraphicsView"]
