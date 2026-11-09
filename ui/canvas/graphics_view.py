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
from ui.canvas.mouse_event_adapter import CanvasMouseEvent
from ui.canvas.canvas_hit import CanvasHitTarget


class GraphicsView(QGraphicsView):
    """Canonical GridForge Canvas viewport."""

    cursor_scene_position = Signal(object)
    PALETTE_EQUIPMENT_MIME = "application/x-gridforge-equipment-type"

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
        self._palette_drag_equipment_type: str | None = None
        self._palette_drag_previous_tool_id: str | None = None
        self._palette_drag_insertion_started = False
        self._palette_drag_preview_started = False
        self._space_pan_active = False
        self._navigation_pan_button: int | None = None

        if self._scene.parent() is None:
            self._scene.setParent(self)
        self.setScene(self._scene)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
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
            ("↶", "Rotate selected symbol 90° counter-clockwise (Q)", "rotate_ccw"),
            ("↷", "Rotate selected symbol 90° clockwise (E)", "rotate_cw"),
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
        self._annotation_quadrant_button.setText("Label ↻")
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
        updated = []
        for block in blocks:
            payload = block.to_dict()
            if block.node_id == node.node_id:
                current = block.quadrant
                payload["quadrant"] = (
                    quadrants[(quadrants.index(current) + 1) % len(quadrants)]
                    if current in quadrants else "top_right"
                )
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

    def _palette_type_from_event(self, event: Any) -> str | None:
        mime = event.mimeData()
        if mime is None or not mime.hasFormat(self.PALETTE_EQUIPMENT_MIME):
            return None
        try:
            value = bytes(mime.data(self.PALETTE_EQUIPMENT_MIME)).decode("utf-8").strip()
        except (TypeError, UnicodeDecodeError):
            return None
        return value or None

    def _begin_palette_drag(self, equipment_type: str) -> bool:
        if self.interaction_manager is None:
            return False
        registry = getattr(self.tool_manager, "equipment_registry", None)
        creation_context = getattr(self.tool_manager, "creation_context", None)
        if registry is None or creation_context is None or creation_context.active:
            return False
        try:
            definition = registry.require(equipment_type)
            previous_tool_id = self.tool_manager.active_tool_id
            self.tool_manager.activate(definition.tool_id, cancel_active_creation=False)
        except (KeyError, TypeError, ValueError, RuntimeError):
            return False
        self._palette_drag_equipment_type = definition.equipment_type
        self._palette_drag_previous_tool_id = previous_tool_id
        self._palette_drag_insertion_started = False
        self._palette_drag_preview_started = False
        return True

    def _palette_event_without_hit(self, event: Any) -> CanvasMouseEvent:
        position = event.position()
        viewport_point = QPointF(float(position.x()), float(position.y()))
        scene_point = self.mapToScene(viewport_point.toPoint())
        modifiers = int(event.modifiers())
        return CanvasMouseEvent(
            position=viewport_point,
            scene_position=QPointF(scene_point),
            presentation_hit=CanvasHitTarget.none(),
            button=int(Qt.MouseButton.LeftButton.value),
            buttons=int(Qt.MouseButton.LeftButton.value),
            modifiers=modifiers,
            insertion_intent=False,
        )

    def _adapt_palette_event(self, event: Any) -> CanvasMouseEvent | None:
        adapter = getattr(self.interaction_manager, "input_adapter", None)
        if adapter is None:
            return None
        try:
            return adapter.adapt(event)
        except (AttributeError, TypeError, ValueError, RuntimeError):
            return None

    def _begin_palette_insertion(self, event: Any) -> bool:
        semantic = self._adapt_palette_event(event)
        if semantic is None:
            return False
        hit = semantic.hit_target
        if (
            getattr(getattr(hit, "kind", None), "value", None) != "simple_wire_segment"
            or not isinstance(hit.core_connection_id, str)
            or not hit.core_connection_id
            or hit.draft_connection_id is not None
        ):
            return False
        creation_context = self.tool_manager.creation_context
        if not creation_context.active:
            return False
        draft = creation_context.require_draft()
        insertion_tool = self.tool_manager.get_tool("electrical-insertion")
        parameters = dict(draft.snapshot_values())
        orientation = float(draft.preview_state.get("rotation", 0.0))
        try:
            insertion_tool.begin(
                self._palette_drag_equipment_type,
                creation_parameters=parameters,
                orientation=orientation,
            )
            candidate = insertion_tool.insertion_target(semantic)
            if (
                candidate is None
                or str(candidate.get("connection_id", "")) != hit.core_connection_id
            ):
                return False
            return bool(
                self.tool_manager.begin_equipment_insertion(
                    self._palette_drag_equipment_type,
                    creation_parameters=parameters,
                    orientation=orientation,
                    equipment_id=None,
                    initial_event=semantic,
                )
            )
        except (KeyError, TypeError, ValueError, RuntimeError):
            return False

    def _finish_palette_drag(self, *, restore_previous_tool: bool) -> None:
        previous_tool_id = self._palette_drag_previous_tool_id
        try:
            if restore_previous_tool:
                self.tool_manager.cancel()
                if self.tool_manager.active_tool_id != previous_tool_id:
                    self.tool_manager.activate(previous_tool_id)
        finally:
            self._palette_drag_equipment_type = None
            self._palette_drag_previous_tool_id = None
            self._palette_drag_insertion_started = False
            self._palette_drag_preview_started = False

    def dragEnterEvent(self, event: Any) -> None:
        equipment_type = self._palette_type_from_event(event)
        if equipment_type is None:
            event.ignore()
            return
        if self._palette_drag_equipment_type is None and not self._begin_palette_drag(equipment_type):
            event.ignore()
            return
        if self._palette_drag_equipment_type != equipment_type:
            event.ignore()
            return
        event.acceptProposedAction()

    def dragMoveEvent(self, event: Any) -> None:
        if self._palette_drag_equipment_type is None or self.interaction_manager is None:
            event.ignore()
            return
        shift_mask = int(Qt.KeyboardModifier.ShiftModifier.value)
        insertion_requested = bool(int(event.modifiers()) & shift_mask)
        if not self._palette_drag_preview_started:
            preview_event = self._palette_event_without_hit(event)
            self.interaction_manager.mouse_move(preview_event)
            self._palette_drag_preview_started = True
        if insertion_requested and not self._palette_drag_insertion_started:
            if not self._begin_palette_insertion(event):
                # Keep the drag session alive while the engineer moves away
                # from an ambiguous crossing or onto a valid canonical wire.
                event.acceptProposedAction()
                return
            self._palette_drag_insertion_started = True
        elif self._palette_drag_insertion_started:
            self.interaction_manager.mouse_move(event)
        elif not insertion_requested:
            self.interaction_manager.mouse_move(self._palette_event_without_hit(event))
        event.acceptProposedAction()

    def dropEvent(self, event: Any) -> None:
        if self._palette_drag_equipment_type is None or self.interaction_manager is None:
            event.ignore()
            return
        shift_mask = int(Qt.KeyboardModifier.ShiftModifier.value)
        insertion_requested = bool(int(event.modifiers()) & shift_mask)
        if not self._palette_drag_preview_started:
            self.interaction_manager.mouse_move(self._palette_event_without_hit(event))
            self._palette_drag_preview_started = True
        if insertion_requested:
            if not self._palette_drag_insertion_started:
                if not self._begin_palette_insertion(event):
                    self._finish_palette_drag(restore_previous_tool=True)
                    event.ignore()
                    return
                self._palette_drag_insertion_started = True
            semantic = self._adapt_palette_event(event)
            if semantic is None or not self._palette_drag_insertion_started:
                self._finish_palette_drag(restore_previous_tool=True)
                event.ignore()
                return
            hit = semantic.hit_target
            if (
                getattr(getattr(hit, "kind", None), "value", None) != "simple_wire_segment"
                or not isinstance(hit.core_connection_id, str)
                or hit.draft_connection_id is not None
            ):
                self._finish_palette_drag(restore_previous_tool=True)
                event.ignore()
                return
            try:
                insertion_tool = self.tool_manager.get_tool("electrical-insertion")
                candidate = insertion_tool.insertion_target(semantic)
            except (KeyError, TypeError, ValueError, RuntimeError):
                candidate = None
            if candidate is None or str(candidate.get("connection_id", "")) != hit.core_connection_id:
                self._finish_palette_drag(restore_previous_tool=True)
                event.ignore()
                return
            handled = self.interaction_manager.mouse_release(event)
        else:
            if self._palette_drag_insertion_started:
                self._finish_palette_drag(restore_previous_tool=True)
                event.ignore()
                return
            semantic = self._palette_event_without_hit(event)
            pressed = self.interaction_manager.mouse_press(semantic)
            handled = self.interaction_manager.mouse_release(semantic) if pressed else False
        if handled:
            self._finish_palette_drag(restore_previous_tool=False)
            event.acceptProposedAction()
        else:
            self._finish_palette_drag(restore_previous_tool=True)
            event.ignore()

    def dragLeaveEvent(self, event: Any) -> None:
        if self._palette_drag_equipment_type is not None:
            self._finish_palette_drag(restore_previous_tool=True)
        super().dragLeaveEvent(event)

    @staticmethod
    def _event_flag_value(event: Any, name: str) -> int:
        value = getattr(event, name, None)
        value = value() if callable(value) else value
        raw = getattr(value, "value", value)
        try:
            return int(raw)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _event_viewport_position(event: Any) -> QPointF:
        position = getattr(event, "position", None)
        if callable(position):
            value = position()
            return QPointF(float(value.x()), float(value.y()))
        point = event.pos()
        return QPointF(float(point.x()), float(point.y()))

    def mousePressEvent(self, event: Any) -> None:
        navigation = self.navigation_controller
        button = self._event_flag_value(event, "button")
        middle_button = int(Qt.MouseButton.MiddleButton.value)
        left_button = int(Qt.MouseButton.LeftButton.value)
        if navigation is not None and (
            button == middle_button
            or (self._space_pan_active and button == left_button)
        ):
            navigation.start_pan(self._event_viewport_position(event))
            self._navigation_pan_button = button
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        if self.interaction_manager is not None and self.interaction_manager.mouse_press(event):
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Any) -> None:
        navigation = self.navigation_controller
        if navigation is not None and navigation.is_panning:
            navigation.update_pan(self._event_viewport_position(event))
            event.accept()
            self._refresh_contextual_tool_strip()
            return
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
        navigation = self.navigation_controller
        button = self._event_flag_value(event, "button")
        if (
            navigation is not None
            and navigation.is_panning
            and button == self._navigation_pan_button
        ):
            navigation.end_pan()
            self._navigation_pan_button = None
            self.unsetCursor()
            event.accept()
            self._refresh_contextual_tool_strip()
            return
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
        key = event.key()
        modifiers = self._event_flag_value(event, "modifiers")
        no_modifiers = modifiers == 0
        navigation = self.navigation_controller

        if key == Qt.Key.Key_Space:
            self._space_pan_active = True
            event.accept()
            return
        if navigation is not None:
            zoom_in_key = (
                (key == Qt.Key.Key_Plus and modifiers in (0, shift))
                or (key == Qt.Key.Key_Equal and no_modifiers)
            )
            if zoom_in_key:
                navigation.zoom_in()
                event.accept()
                self._refresh_contextual_tool_strip()
                return
            if no_modifiers and key == Qt.Key.Key_Minus:
                navigation.zoom_out()
                event.accept()
                self._refresh_contextual_tool_strip()
                return
            if no_modifiers and key == Qt.Key.Key_0:
                navigation.fit_content()
                event.accept()
                self._refresh_contextual_tool_strip()
                return
            if no_modifiers and key == Qt.Key.Key_Home:
                navigation.reset_view()
                event.accept()
                self._refresh_contextual_tool_strip()
                return
        if no_modifiers and key == Qt.Key.Key_E:
            self._apply_contextual_symbol_action("rotate_cw")
            event.accept()
            return
        if no_modifiers and key == Qt.Key.Key_Q:
            self._apply_contextual_symbol_action("rotate_ccw")
            event.accept()
            return
        if self.interaction_manager is not None and self.interaction_manager.key_press(event):
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: Any) -> None:
        if event.key() == Qt.Key.Key_Space:
            self._space_pan_active = False
            event.accept()
            return
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
