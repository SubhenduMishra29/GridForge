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
    - create application controllers;
    - create ToolManager;
    - own tool lifecycle;
    - perform electrical calculations;
    - modify Core state;
    - construct domain objects.

Application-owned interaction dependencies are injected into the
viewport and forwarded to InteractionManager.
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
    """
    Canonical GridForge canvas viewport.

    GraphicsView translates raw Qt input into calls to:

        InteractionManager
        NavigationController

    The application Controller and ToolManager are supplied by the
    application composition layer.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        tool_manager: Any,
        parent: Optional[Any] = None,
    ) -> None:
        """
        Create the canvas viewport.

        Parameters
        ----------
        controller:
            Application/UI controller.

        tool_manager:
            Existing application-owned ToolManager.

            GraphicsView does not create or own this object.

        parent:
            Optional Qt parent widget.

        Raises
        ------
        ValueError
            If controller or tool_manager is None.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        if tool_manager is None:
            raise ValueError(
                "tool_manager must not be None."
            )

        super().__init__(parent)

        # ----------------------------------------------------
        # External application dependencies
        # ----------------------------------------------------

        self.controller = controller
        self.tool_manager = tool_manager

        # ----------------------------------------------------
        # Canvas scene
        # ----------------------------------------------------

        self._scene = QGraphicsScene(self)

        self.setScene(
            self._scene
        )

        # ----------------------------------------------------
        # Interaction service
        #
        # InteractionManager receives the authoritative
        # application-owned ToolManager.
        # ----------------------------------------------------

        self.interaction_manager = (
            InteractionManager(
                view=self,
                controller=controller,
                tool_manager=tool_manager,
            )
        )

        # ----------------------------------------------------
        # Navigation service
        # ----------------------------------------------------

        self.navigation_controller = (
            NavigationController(
                view=self,
            )
        )

        # ----------------------------------------------------
        # Viewport configuration
        # ----------------------------------------------------

        self.setMouseTracking(
            True
        )

        self.setFocusPolicy(
            Qt.StrongFocus
        )

        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

    # ========================================================
    # SCENE ACCESS
    # ========================================================

    @property
    def graphics_scene(self) -> QGraphicsScene:
        """
        Return the authoritative QGraphicsScene.
        """

        return self._scene

    # ========================================================
    # EVENT FORWARDING
    # ========================================================

    def mousePressEvent(
        self,
        event: Any,
    ) -> None:
        """
        Forward mouse press events to InteractionManager.
        """

        self.interaction_manager.mouse_press(
            event
        )

    # --------------------------------------------------------

    def mouseMoveEvent(
        self,
        event: Any,
    ) -> None:
        """
        Forward mouse move events to InteractionManager.
        """

        self.interaction_manager.mouse_move(
            event
        )

    # --------------------------------------------------------

    def mouseReleaseEvent(
        self,
        event: Any,
    ) -> None:
        """
        Forward mouse release events to InteractionManager.
        """

        self.interaction_manager.mouse_release(
            event
        )

    # --------------------------------------------------------

    def wheelEvent(
        self,
        event: Any,
    ) -> None:
        """
        Forward wheel events to NavigationController.
        """

        self.navigation_controller.wheel_event(
            event
        )

    # --------------------------------------------------------

    def keyPressEvent(
        self,
        event: Any,
    ) -> None:
        """
        Forward keyboard events to InteractionManager.
        """

        self.interaction_manager.key_press(
            event
        )

    # --------------------------------------------------------

    def keyReleaseEvent(
        self,
        event: Any,
    ) -> None:
        """
        Forward keyboard release events to InteractionManager.
        """

        self.interaction_manager.key_release(
            event
        )


__all__ = [
    "GraphicsView",
]
