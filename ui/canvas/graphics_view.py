# ============================================================
# File: ui/canvas/graphics_view.py
# GridForge V2 — Graphics View
# ============================================================
"""
GridForge V2 canvas viewport.

GraphicsView is the Qt boundary of the canvas.

Responsibilities
----------------
GraphicsView:

    - owns the canvas QGraphicsScene;
    - receives raw Qt mouse/keyboard/wheel events;
    - routes interaction events to InteractionManager;
    - routes navigation events to NavigationController;
    - provides stable scene/service access;
    - manages viewport-level Qt configuration;
    - maintains keyboard focus for canvas interaction.

GraphicsView does NOT:

    - implement tool logic;
    - own tool instances;
    - own application selection;
    - modify Core objects directly;
    - perform electrical calculations;
    - perform snapping;
    - implement rendering logic;
    - implement navigation algorithms;
    - implement persistent interaction state.

Architecture
------------

                         Qt Input
                            │
                            ▼
                    ┌──────────────┐
                    │ GraphicsView │
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
     InteractionManager       NavigationController
              │                         │
              ▼                         ▼
          ToolManager              View transform
              │
              ▼
             Tool
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
    - renderers.

Qt Boundary
-----------

All Qt imports must pass through:

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
    Thin Qt viewport adapter for the GridForge canvas.

    Event ownership is deliberately separated:

        Middle mouse
            → NavigationController

        Wheel
            → NavigationController

        Other mouse input
            → InteractionManager

        Keyboard input
            → InteractionManager

    The class contains no application or electrical-domain
    behavior.
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
        Initialize the GridForge canvas viewport.

        Parameters
        ----------
        controller:
            Application/UI Controller.

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
        #
        # GraphicsView owns the scene used by this canvas.
        # Permanent graphical projection is managed by the
        # render system; this class only owns the scene object.
        # ----------------------------------------------------

        self._scene = QGraphicsScene(self)

        self.setScene(
            self._scene
        )

        # ----------------------------------------------------
        # Interaction
        # ----------------------------------------------------

        self.interaction_manager = (
            InteractionManager(
                view=self,
                controller=controller,
            )
        )

        # ----------------------------------------------------
        # Navigation
        # ----------------------------------------------------

        self.navigation_controller = (
            NavigationController(
                view=self,
            )
        )

        # ----------------------------------------------------
        # Viewport behavior
        # ----------------------------------------------------

        self.setMouseTracking(
            True
        )

        self.setFocusPolicy(
            Qt.StrongFocus
        )

        # Navigation uses explicit pan/zoom behavior.
        #
        # Scrollbars remain available internally for the
        # NavigationController's panning implementation but
        # are not presented as part of the canvas UI.
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

    # ========================================================
    # MOUSE INPUT
    # ========================================================

    def mousePressEvent(
        self,
        event: Any,
    ) -> None:
        """
        Route a mouse-press event.

        Middle mouse starts canvas panning.

        All other buttons are routed to InteractionManager.
        """

        if event is None:
            return

        self.setFocus(
            Qt.MouseFocusReason
        )

        if (
            event.button()
            == Qt.MiddleButton
        ):
            self.navigation_controller.start_pan(
                event.position().toPoint()
            )

            event.accept()
            return

        handled = (
            self.interaction_manager.mouse_press(
                event
            )
        )

        if handled:
            event.accept()
        else:
            super().mousePressEvent(
                event
            )

    # --------------------------------------------------------

    def mouseMoveEvent(
        self,
        event: Any,
    ) -> None:
        """
        Route a mouse-move event.

        Active middle-button panning has priority over normal
        tool interaction.
        """

        if event is None:
            return

        if self.navigation_controller.is_panning:

            self.navigation_controller.update_pan(
                event.position().toPoint()
            )

            event.accept()
            return

        handled = (
            self.interaction_manager.mouse_move(
                event
            )
        )

        if handled:
            event.accept()
        else:
            super().mouseMoveEvent(
                event
            )

    # --------------------------------------------------------

    def mouseReleaseEvent(
        self,
        event: Any,
    ) -> None:
        """
        Route a mouse-release event.

        Middle mouse terminates panning.

        Other buttons are routed to InteractionManager.
        """

        if event is None:
            return

        if (
            event.button()
            == Qt.MiddleButton
        ):
            self.navigation_controller.end_pan()

            event.accept()
            return

        handled = (
            self.interaction_manager.mouse_release(
                event
            )
        )

        if handled:
            event.accept()
        else:
            super().mouseReleaseEvent(
                event
            )

    # ========================================================
    # WHEEL / NAVIGATION
    # ========================================================

    def wheelEvent(
        self,
        event: Any,
    ) -> None:
        """
        Forward wheel navigation to NavigationController.
        """

        if event is None:
            return

        self.navigation_controller.handle_wheel(
            event
        )

    # ========================================================
    # KEYBOARD INPUT
    # ========================================================

    def keyPressEvent(
        self,
        event: Any,
    ) -> None:
        """
        Route keyboard input to InteractionManager.

        If the interaction layer does not consume the event,
        normal QGraphicsView processing is allowed.
        """

        if event is None:
            return

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
        Route keyboard-release input to InteractionManager.
        """

        if event is None:
            return

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
    # SCENE ACCESS
    # ========================================================

    def get_scene(
        self,
    ) -> QGraphicsScene:
        """
        Return the QGraphicsScene owned by this canvas.
        """

        return self._scene

    # --------------------------------------------------------

    def scene(
        self,
    ) -> QGraphicsScene:
        """
        Return the canvas scene.

        This is a semantic convenience wrapper around the
        QGraphicsView scene accessor.
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
    # RESET
    # ========================================================

    def reset_canvas(
        self,
    ) -> None:
        """
        Reset transient canvas state.

        This operation does not modify Core state and does not
        replace the QGraphicsScene.
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
        Return a diagnostic snapshot of the canvas viewport.
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
        Release canvas-owned transient services.

        The Controller and Core model are not owned here and are
        therefore not disposed.
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

        zoom = getattr(
            self.navigation_controller,
            "zoom_factor",
            None,
        )

        return (
            "GraphicsView("
            f"items={len(self._scene.items())}, "
            f"mouse_tracking="
            f"{self.hasMouseTracking()}, "
            f"zoom={zoom}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "GraphicsView",
]
