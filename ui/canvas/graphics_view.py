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
GraphicsView owns the Qt viewport and QGraphicsScene.

It does not:
    - create Presentation controllers;
    - create ToolManager;
    - own tool lifecycle;
    - perform electrical calculations;
    - modify Core state;
    - construct domain objects.

UI interaction dependencies are injected into the viewport and
forwarded to Presentation interaction services.

The Application layer is the future explicit Core↔UI integration
boundary. GraphicsView does not bypass that boundary.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import (
    QGraphicsScene,
    QGraphicsView,
    Qt,
)

from ui.canvas.interaction_manager import InteractionManager
from ui.canvas.navigation_controller import NavigationController


class GraphicsView(QGraphicsView):
    """Canonical GridForge Canvas viewport.

    GraphicsView translates raw Qt input into calls to
    ``InteractionManager`` and ``NavigationController``.

    Presentation/UI services are supplied by composition. The view
    itself does not own Application or Core state.
    """

    def __init__(
        self,
        controller: Any,
        tool_manager: Any,
        parent: Optional[Any] = None,
    ) -> None:
        """Create the Canvas viewport.

        ``controller`` is a Presentation/UI controller reference.
        ``tool_manager`` is an existing UI ToolManager supplied by
        the composition boundary.
        """
        if controller is None:
            raise ValueError("controller must not be None.")

        if tool_manager is None:
            raise ValueError("tool_manager must not be None.")

        super().__init__(parent)

        self.controller = controller
        self.tool_manager = tool_manager

        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self.interaction_manager = InteractionManager(
            view=self,
            controller=controller,
            tool_manager=tool_manager,
        )

        self.navigation_controller = NavigationController(view=self)

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    @property
    def graphics_scene(self) -> QGraphicsScene:
        """Return the Canvas-owned QGraphicsScene."""
        return self._scene

    def mousePressEvent(self, event: Any) -> None:
        if not self.interaction_manager.mouse_press(event):
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Any) -> None:
        if not self.interaction_manager.mouse_move(event):
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: Any) -> None:
        if not self.interaction_manager.mouse_release(event):
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event: Any) -> None:
        if not self.navigation_controller.wheel_event(event):
            super().wheelEvent(event)

    def keyPressEvent(self, event: Any) -> None:
        if not self.interaction_manager.key_press(event):
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: Any) -> None:
        if not self.interaction_manager.key_release(event):
            super().keyReleaseEvent(event)

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)

    def dispose(self) -> None:
        """Dispose Presentation interaction services owned by the view."""
        interaction_manager = self.interaction_manager
        if interaction_manager is not None:
            interaction_manager.dispose()

        navigation_controller = self.navigation_controller
        if navigation_controller is not None:
            navigation_controller.dispose()


__all__ = ["GraphicsView"]
