# ============================================================
# File: ui/canvas/graphics_view.py
# GridForge V2 — Graphics View
# ============================================================
"""
Custom QGraphicsView for the GridForge canvas.

GraphicsView is the Qt viewport boundary of the canvas.

Responsibilities
----------------
GraphicsView:

    - owns the QGraphicsScene used by the canvas;
    - receives raw Qt input events;
    - routes tool interaction to InteractionManager;
    - routes navigation input to NavigationController;
    - enables mouse tracking;
    - receives keyboard focus;
    - exposes the scene through a stable accessor;
    - exposes canvas navigation operations;
    - manages the Qt-side lifetime of canvas services.

GraphicsView does NOT:

    - modify the Core model;
    - implement tool logic;
    - perform snapping;
    - perform selection logic;
    - create electrical model objects;
    - calculate electrical quantities;
    - own tool instances or tool lifecycle;
    - render permanent model objects;
    - implement coordinate conversion;
    - decide application-level tool selection.

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
             ToolManager          View navigation
                │
                ▼
              Tools
                │
                ▼
            Controller
                │
                ▼
              Core

Ownership
---------
GraphicsView owns:

    - its QGraphicsScene;
    - its InteractionManager;
    - its NavigationController.

GraphicsView does not own:

    - Controller;
    - Core model;
    - concrete tools;
    - persistent selection;
    - rendering/model projection systems.

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

    GraphicsView is intentionally a thin Qt event boundary.

    It owns the canvas scene and routes raw Qt input to the
    appropriate canvas subsystem.

    It does not implement application interaction semantics.
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
            GridForge application/UI Controller.

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
        # Lifecycle state
        # ----------------------------------------------------

        self._disposed = False

        # ----------------------------------------------------
        # Scene
        # ----------------------------------------------------
        #
        # GraphicsView owns the scene used by the canvas.
        # The scene is a UI projection container only.
        # ----------------------------------------------------

        self._scene = QGraphicsScene(self)

        self.setScene(
            self._scene
        )

        # ----------------------------------------------------
        # Interaction system
        # ----------------------------------------------------
        #
        # InteractionManager owns transient interaction
        # services such as:
        #
        #   - CoordinateSystem
        #   - PreviewLayer
        #   - SnapSystem
        #   - ToolManager
        #
        # GraphicsView only routes input to it.
        # ----------------------------------------------------

        self.interaction_manager = (
            InteractionManager(
                view=self,
                controller=controller,
            )
        )

        # ----------------------------------------------------
        # Navigation system
        # ----------------------------------------------------
        #
        # NavigationController owns:
        #
        #   - zoom;
        #   - pan;
        #   - fit;
        #   - navigation state.
        #
        # GraphicsView only routes navigation events.
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
        # Canvas navigation is explicitly controlled by
        # NavigationController.
        #
        # Scrollbars are therefore disabled as visible
        # navigation controls.
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
        Route a mouse-press event.

        Middle mouse belongs exclusively to canvas
        navigation.

        Other mouse buttons are routed to
        InteractionManager.
        """

        if event is None:
            return

        self.setFocus(
            Qt.MouseFocusReason
        )

        # ----------------------------------------------------
        # Middle mouse → navigation
        # ----------------------------------------------------

        if event.button() == Qt.MiddleButton:

            self.navigation_controller.start_pan(
                event.position().toPoint()
            )

            event.accept()

            return

        # ----------------------------------------------------
        # Tool / interaction input
        # ----------------------------------------------------

        handled = (
            self.interaction_manager.mouse_press(
                event
            )
        )

        if handled:
            event.accept()
        else:
            event.ignore()

    # --------------------------------------------------------

    def mouseMoveEvent(
        self,
        event: Any,
    ) -> None:
        """
        Route mouse-move events.

        Active middle-button panning has priority over normal
        interaction input.
        """

        if event is None:
            return

        # ----------------------------------------------------
        # Navigation
        # ----------------------------------------------------

        if self.navigation_controller.is_panning:

            self.navigation_controller.update_pan(
                event.position().toPoint()
            )

            event.accept()

            return

        # ----------------------------------------------------
        # Tool / interaction input
        # ----------------------------------------------------

        handled = (
            self.interaction_manager.mouse_move(
                event
            )
        )

        if handled:
            event.accept()
        else:
            event.ignore()

    # --------------------------------------------------------

    def mouseReleaseEvent(
        self,
        event: Any,
    ) -> None:
        """
        Route a mouse-release event.

        Middle mouse terminates navigation.

        Other mouse buttons are routed to InteractionManager.
        """

        if event is None:
            return

        # ----------------------------------------------------
        # Navigation
        # ----------------------------------------------------

        if event.button() == Qt.MiddleButton:

            self.navigation_controller.end_pan()

            event.accept()

            return

        # ----------------------------------------------------
        # Tool / interaction input
        # ----------------------------------------------------

        handled = (
            self.interaction_manager.mouse_release(
                event
            )
        )

        if handled:
            event.accept()
        else:
            event.ignore()

    # ========================================================
    # WHEEL / ZOOM
    # ========================================================

    def wheelEvent(
        self,
        event: Any,
    ) -> None:
        """
        Forward wheel navigation to NavigationController.

        NavigationController owns the zoom policy and cursor
        anchoring behavior.
        """

        if event is None:
            return

        self.navigation_controller.handle_wheel(
            event
        )

        event.accept()

    # ========================================================
    # KEY EVENTS
    # ========================================================

    def keyPressEvent(
        self,
        event: Any,
    ) -> None:
        """
        Forward keyboard input to InteractionManager.

        If InteractionManager does not consume the event,
        normal QGraphicsView handling is preserved.
        """

        if event is None:
            return

        handled = (
            self.interaction_manager.key_press(
                event
            )
        )

        if handled:
            event.accept()
            return

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

        Unhandled events are passed to QGraphicsView.
        """

        if event is None:
            return

        handled = (
            self.interaction_manager.key_release(
                event
            )
        )

        if handled:
            event.accept()
            return

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
        Request zoom-in through NavigationController.
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
        Request zoom-out through NavigationController.
        """

        self.navigation_controller.zoom_out(
            steps
        )

    # --------------------------------------------------------

    def reset_view(
        self,
    ) -> None:
        """
        Reset canvas navigation through
        NavigationController.
        """

        self.navigation_controller.reset_view()

    # --------------------------------------------------------

    def fit_content(
        self,
        margin: float = 50.0,
    ) -> None:
        """
        Fit visible scene content through
        NavigationController.
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

        The scene is owned by this GraphicsView.
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
        Reset transient canvas state.

        This operation:

            - terminates active navigation;
            - resets InteractionManager state;
            - preserves the QGraphicsScene;
            - does not modify the Core model;
            - does not replace application selection state.
        """

        self.navigation_controller.end_pan()

        self.interaction_manager.reset()

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
            "disposed": self._disposed,
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
        Release transient canvas services.

        GraphicsView does not own the Controller or Core model.

        Disposal is idempotent.
        """

        if self._disposed:
            return

        # ----------------------------------------------------
        # Stop navigation first.
        # ----------------------------------------------------

        self.navigation_controller.end_pan()

        # ----------------------------------------------------
        # Release interaction subsystem.
        # ----------------------------------------------------

        self.interaction_manager.dispose()

        self._disposed = True

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        if self._disposed:
            return (
                "GraphicsView("
                "disposed=True"
                ")"
            )

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
