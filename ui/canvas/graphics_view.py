# ============================================================
# File: ui/canvas/graphics_view.py
# GridForge V2 — Graphics View
# ============================================================
"""
Custom QGraphicsView for the GridForge canvas.

Responsibilities
----------------
GraphicsView is the Qt viewport boundary for the canvas.

It is responsible for:

    - owning the QGraphicsScene used by the canvas;
    - receiving raw Qt input events;
    - forwarding tool interaction to InteractionManager;
    - forwarding navigation input to NavigationController;
    - enabling mouse tracking;
    - receiving keyboard focus;
    - exposing the scene through a stable accessor;
    - exposing canvas navigation operations.

GraphicsView does NOT:

    - modify the Core model;
    - implement tool logic;
    - perform snapping;
    - perform selection logic;
    - create electrical model objects;
    - calculate electrical quantities;
    - own tool lifecycle;
    - render permanent model objects.

Architecture
------------

                         Qt Input
                            │
                            ▼
                     ┌─────────────┐
                     │ GraphicsView│
                     └──────┬──────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
      InteractionManager       NavigationController
                │                       │
                ▼                       ▼
             Tools                 View navigation
                │
                ▼
           Controller
                │
                ▼
              Core

Qt rule
-------
All Qt classes must be imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
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
    GridForge canvas viewport.

    GraphicsView is the thin Qt event boundary.

    Tool interaction is delegated to InteractionManager.

    View navigation is delegated to NavigationController.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        parent: Optional[Any] = None,
    ) -> None:
        """
        Initialize the GridForge graphics view.

        Parameters
        ----------
        controller:
            GridForge UI/Core controller.

        parent:
            Optional Qt parent widget.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        super().__init__(parent)

        self.controller = controller

        # ----------------------------------------------------
        # Scene
        # ----------------------------------------------------

        self._scene = QGraphicsScene(self)

        self.setScene(
            self._scene
        )

        # ----------------------------------------------------
        # Interaction system
        # ----------------------------------------------------

        self.interaction_manager = (
            InteractionManager(
                self,
                controller,
            )
        )

        # ----------------------------------------------------
        # Navigation system
        # ----------------------------------------------------
        #
        # NavigationController owns zoom/pan/fit behavior.
        # GraphicsView only routes the relevant Qt events.
        # ----------------------------------------------------

        self.navigation_controller = (
            NavigationController(
                self,
            )
        )

        # ----------------------------------------------------
        # Mouse tracking
        # ----------------------------------------------------

        self.setMouseTracking(
            True
        )

        # ----------------------------------------------------
        # Keyboard focus
        # ----------------------------------------------------

        self.setFocusPolicy(
            Qt.StrongFocus
        )

        # ----------------------------------------------------
        # Scrollbars
        # ----------------------------------------------------
        #
        # Navigation is handled by NavigationController.
        # Scrollbars are therefore not part of the visible
        # GridForge canvas UI.
        # ----------------------------------------------------

        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

    # ========================================================
    # MOUSE EVENTS
    # ========================================================

    def mousePressEvent(
        self,
        event: Any,
    ) -> None:
        """
        Route mouse-press events.

        Middle mouse belongs to canvas navigation.

        Other mouse buttons belong to the interaction/tool
        system.
        """

        self.setFocus(
            Qt.MouseFocusReason
        )

        # ----------------------------------------------------
        # Middle mouse → navigation
        # ----------------------------------------------------

        if (
            event.button()
            == Qt.MiddleButton
        ):
            self.navigation_controller.start_pan(
                event.position().toPoint()
            )

            event.accept()

            return

        # ----------------------------------------------------
        # Tool interaction
        # ----------------------------------------------------

        self.interaction_manager.mouse_press(
            event
        )

    # --------------------------------------------------------

    def mouseMoveEvent(
        self,
        event: Any,
    ) -> None:
        """
        Route mouse-move events.

        An active middle-button pan takes precedence over
        normal tool interaction.
        """

        if self.navigation_controller.is_panning:

            self.navigation_controller.update_pan(
                event.position().toPoint()
            )

            event.accept()

            return

        self.interaction_manager.mouse_move(
            event
        )

    # --------------------------------------------------------

    def mouseReleaseEvent(
        self,
        event: Any,
    ) -> None:
        """
        Route mouse-release events.

        Middle mouse terminates navigation.

        Other mouse buttons are delegated to the active tool.
        """

        if (
            event.button()
            == Qt.MiddleButton
        ):
            self.navigation_controller.end_pan()

            event.accept()

            return

        self.interaction_manager.mouse_release(
            event
        )

    # ========================================================
    # WHEEL / ZOOM
    # ========================================================

    def wheelEvent(
        self,
        event: Any,
    ) -> None:
        """
        Forward mouse-wheel navigation to
        NavigationController.

        Zoom is centered on the cursor position.
        """

        self.navigation_controller.handle_wheel(
            event
        )

    # ========================================================
    # KEY EVENTS
    # ========================================================

    def keyPressEvent(
        self,
        event: Any,
    ) -> None:
        """
        Forward keyboard input to InteractionManager.

        If the interaction system does not consume the event,
        normal QGraphicsView handling is allowed.
        """

        handled = (
            self.interaction_manager.key_press(
                event
            )
        )

        if not handled:
            super().keyPressEvent(
                event
            )

    # --------------------------------------------------------

    def keyReleaseEvent(
        self,
        event: Any,
    ) -> None:
        """
        Forward keyboard-release events to InteractionManager.
        """

        handled = (
            self.interaction_manager.key_release(
                event
            )
        )

        if not handled:
            super().keyReleaseEvent(
                event
            )

    # ========================================================
    # NAVIGATION ACCESS
    # ========================================================

    def get_navigation_controller(
        self,
    ) -> NavigationController:
        """
        Return the canvas NavigationController.
        """

        return self.navigation_controller

    # --------------------------------------------------------

    def zoom_in(
        self,
        steps: int = 1,
    ) -> None:
        """
        Zoom into the canvas.
        """

        self.navigation_controller.zoom_in(
            steps
        )

    # --------------------------------------------------------

    def zoom_out(
        self,
        steps: int = 1,
    ) -> None:
        """
        Zoom out of the canvas.
        """

        self.navigation_controller.zoom_out(
            steps
        )

    # --------------------------------------------------------

    def reset_view(
        self,
    ) -> None:
        """
        Reset canvas navigation.
        """

        self.navigation_controller.reset_view()

    # --------------------------------------------------------

    def fit_content(
        self,
        margin: float = 50.0,
    ) -> None:
        """
        Fit visible scene content into the viewport.
        """

        self.navigation_controller.fit_content(
            margin
        )

    # ========================================================
    # SCENE ACCESS
    # ========================================================

    def get_scene(
        self,
    ) -> QGraphicsScene:
        """
        Return the canvas QGraphicsScene.
        """

        return self._scene

    # ========================================================
    # INTERACTION ACCESS
    # ========================================================

    def get_interaction_manager(
        self,
    ) -> InteractionManager:
        """
        Return the canvas InteractionManager.
        """

        return self.interaction_manager

    # ========================================================
    # RESET
    # ========================================================

    def reset_canvas(
        self,
    ) -> None:
        """
        Reset transient canvas interaction state.

        This does not modify the Core model and does not replace
        the QGraphicsScene.
        """

        self.interaction_manager.reset()

        self.navigation_controller.end_pan()

    # ========================================================
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic canvas state.
        """

        return {
            "scene": self._scene is not None,
            "scene_item_count": len(
                self._scene.items()
            ),
            "mouse_tracking": (
                self.hasMouseTracking()
            ),
            "focus_policy": (
                self.focusPolicy()
            ),
            "interaction_manager": (
                self.interaction_manager is not None
            ),
            "navigation_controller": (
                self.navigation_controller is not None
            ),
            "navigation": (
                self.navigation_controller.get_state()
            ),
        }

    # ========================================================
    # CLEANUP
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Release transient canvas resources.

        GraphicsView does not own the Controller or Core model.
        """

        if self.navigation_controller is not None:
            self.navigation_controller.end_pan()

        if self.interaction_manager is not None:
            self.interaction_manager.dispose()

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "GraphicsView("
            f"items={len(self._scene.items())}, "
            f"mouse_tracking="
            f"{self.hasMouseTracking()}, "
            f"zoom="
            f"{self.navigation_controller.zoom_factor}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "GraphicsView",
]
