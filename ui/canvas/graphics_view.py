# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/canvas/graphics_view.py
#
# Purpose:
#     Canonical Qt viewport for the GridForge SLD canvas.
#
# Architectural Role:
#     GraphicsView is the Qt/input boundary of the canvas.
#
#     It receives native Qt input events and delegates them to
#     the appropriate canvas service:
#
#         Mouse / Keyboard
#               |
#               v
#        GraphicsView
#          /       \
#         v         v
#   Interaction   Navigation
#     Manager     Controller
#         |         |
#         v         v
#       Tools    View Transform
#
# Responsibilities:
#     - own the QGraphicsScene used by the canvas;
#     - receive Qt mouse events;
#     - receive Qt keyboard events;
#     - route interaction events;
#     - route navigation events;
#     - maintain keyboard focus;
#     - expose canvas services;
#     - provide diagnostic state;
#     - release transient canvas services during disposal.
#
# Does NOT:
#     - implement tool logic;
#     - own concrete tools;
#     - perform snapping;
#     - perform selection;
#     - render SLD equipment;
#     - render electrical connections;
#     - perform coordinate conversion;
#     - implement navigation algorithms;
#     - modify Core state directly;
#     - perform electrical calculations.
#
# SLD Boundary:
#
#     The GraphicsView is the viewport through which the current
#     first-class GridForge SLD workflow is presented.
#
#     SLD equipment, terminals, connections, topology projection,
#     symbols and renderers remain owned by their respective
#     canvas/model/rendering subsystems.
#
# Event Routing:
#
#     Left / Right / Other Mouse
#             |
#             v
#     InteractionManager
#             |
#             v
#         ToolManager
#             |
#             v
#           Tool
#
#     Middle Mouse
#             |
#             v
#     NavigationController
#
#     Wheel
#             |
#             v
#     NavigationController
#
#     Keyboard
#             |
#             v
#     InteractionManager
#
# Ownership:
#
#     GraphicsView OWNS:
#         - QGraphicsScene
#         - InteractionManager
#         - NavigationController
#
#     GraphicsView DOES NOT OWN:
#         - Controller
#         - Core model
#         - concrete tools
#         - selection state
#         - renderers
#         - SLD equipment definitions
#         - persistent document state
#
# Important Boundary:
#
#     GraphicsView is an adapter, not an orchestration layer.
#
#     It must translate Qt events into calls to the appropriate
#     service and must not reproduce service logic internally.
#
# Qt Boundary:
#
#     All Qt dependencies pass through:
#
#         ui.core.qt
#
#     No direct PySide6/PyQt imports are permitted here.
#
# ============================================================

"""
GridForge V2 — Canvas Graphics View.

Thin Qt viewport boundary for the SLD canvas.
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

    GraphicsView translates raw Qt input into calls to the
    InteractionManager and NavigationController.

    No application or electrical-domain logic belongs here.
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
        Create the canvas viewport.

        Parameters
        ----------
        controller:
            Application/UI controller supplied to the
            interaction layer.

        parent:
            Optional Qt parent widget.

        Raises
        ------
        ValueError
            If controller is None.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        super().__init__(parent)

        # ----------------------------------------------------
        # External application dependency
        # ----------------------------------------------------
        #
        # GraphicsView references Controller but does not own
        # or dispose it.
        # ----------------------------------------------------

        self.controller = controller

        # ----------------------------------------------------
        # Canvas scene
        # ----------------------------------------------------
        #
        # The scene is owned by this viewport.
        #
        # GraphicsView itself does not populate the scene with
        # SLD equipment or connections. Those responsibilities
        # remain with the appropriate canvas/rendering layers.
        # ----------------------------------------------------

        self._scene = QGraphicsScene(self)

        self.setScene(
            self._scene
        )

        # ----------------------------------------------------
        # Interaction service
        # ----------------------------------------------------
        #
        # InteractionManager owns the interaction pipeline.
        # GraphicsView only forwards Qt events to it.
        # ----------------------------------------------------

        self.interaction_manager = (
            InteractionManager(
                view=self,
                controller=controller,
            )
        )

        # ----------------------------------------------------
        # Navigation service
        # ----------------------------------------------------
        #
        # NavigationController owns zoom/pan behavior.
        # GraphicsView only provides the Qt event boundary.
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

        # Navigation is handled explicitly by
        # NavigationController.
        #
        # Scrollbars therefore remain hidden from the user.
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

        Middle mouse belongs exclusively to navigation.

        All other mouse buttons are delegated to
        InteractionManager.

        Unhandled events are passed to QGraphicsView.
        """

        if event is None:
            return

        # The canvas must receive keyboard input after mouse
        # interaction begins.
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
            return

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
        interaction processing.
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
            return

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

        Middle mouse terminates navigation panning.

        Other buttons are delegated to InteractionManager.
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
            return

        super().mouseReleaseEvent(
            event
        )

    # ========================================================
    # WHEEL INPUT
    # ========================================================

    def wheelEvent(
        self,
        event: Any,
    ) -> None:
        """
        Delegate wheel navigation to NavigationController.

        Wheel behavior is deliberately not implemented here.
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
        Delegate keyboard interaction to InteractionManager.

        Unhandled events continue through the normal Qt
        QGraphicsView event chain.
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
        Delegate keyboard-release interaction to
        InteractionManager.

        Unhandled events continue through Qt.
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
    # SCENE ACCESS
    # ========================================================

    def get_scene(
        self,
    ) -> QGraphicsScene:
        """
        Return the QGraphicsScene owned by GraphicsView.
        """

        return self._scene

    # --------------------------------------------------------

    def scene(
        self,
    ) -> QGraphicsScene:
        """
        Return the canvas scene.

        This semantic wrapper intentionally returns the same
        scene instance owned by this GraphicsView.
        """

        return self._scene

    # ========================================================
    # INTERACTION ACCESS
    # ========================================================

    def get_interaction_manager(
        self,
    ) -> InteractionManager:
        """
        Return the InteractionManager owned by this viewport.
        """

        return self.interaction_manager

    # ========================================================
    # NAVIGATION ACCESS
    # ========================================================

    def get_navigation_controller(
        self,
    ) -> NavigationController:
        """
        Return the NavigationController owned by this viewport.
        """

        return self.navigation_controller

    # --------------------------------------------------------

    def zoom_in(
        self,
        steps: int = 1,
    ) -> None:
        """
        Delegate zoom-in behavior.
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
        Delegate zoom-out behavior.
        """

        self.navigation_controller.zoom_out(
            steps
        )

    # --------------------------------------------------------

    def reset_view(
        self,
    ) -> None:
        """
        Delegate navigation reset.
        """

        self.navigation_controller.reset_view()

    # --------------------------------------------------------

    def fit_content(
        self,
        margin: float = 50.0,
    ) -> None:
        """
        Delegate content fitting to NavigationController.
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
        Reset transient canvas interaction state.

        This does not:

            - modify Core state;
            - replace the scene;
            - clear persistent SLD objects;
            - change application state.

        Interaction state is reset by InteractionManager.

        Active navigation panning is terminated by
        NavigationController.
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
        Return diagnostic viewport state.

        The returned state contains only canvas diagnostics and
        does not expose or duplicate application/Core state.
        """

        return {
            "scene": (
                self._scene is not None
            ),
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
                self.interaction_manager
                is not None
            ),
            "navigation_controller": (
                self.navigation_controller
                is not None
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
        Release transient services owned by GraphicsView.

        Controller and Core are intentionally not disposed because
        GraphicsView does not own either object.

        The operation is safe to call repeatedly.
        """

        if (
            self.navigation_controller
            is not None
        ):
            self.navigation_controller.end_pan()

        if (
            self.interaction_manager
            is not None
        ):
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
