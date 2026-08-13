# ============================================================
# File: ui/canvas/graphics_view.py
# GridForge Canvas Graphics View
# ============================================================
#
# PURPOSE
# -------
# Qt boundary for the GridForge graphical canvas.
#
# GraphicsView owns:
#
#     - QGraphicsScene
#     - viewport configuration
#     - raw Qt input events
#     - CoordinateSystem
#     - GridSystem
#     - InteractionManager
#
#
# ARCHITECTURE
# ------------
#
#              Qt
#               │
#               ▼
#        ┌───────────────┐
#        │ GraphicsView  │
#        └───────┬───────┘
#                │
#                ▼
#       InteractionManager
#                │
#                ▼
#           ToolManager
#                │
#                ▼
#              Tool
#                │
#                ▼
#           Controller
#                │
#                ▼
#             Core Model
#
#
# IMPORTANT RULES
# ---------------
#
# GraphicsView:
#
#     DOES
#         - receive raw Qt events
#         - convert them into the canvas interaction boundary
#         - forward events to InteractionManager
#         - own the QGraphicsScene
#         - configure viewport behavior
#
#     DOES NOT
#         - implement tool logic
#         - modify the model
#         - create permanent model graphics
#         - perform electrical calculations
#         - own tool lifecycle
#         - perform selection logic
#         - implement snapping logic
#         - implement rendering logic
#
#
# QT RULE
# -------
#
# All Qt imports MUST come through:
#
#     ui.core.qt
#
# No direct PySide6 / PyQt imports are permitted.
#
# ============================================================

from __future__ import annotations

from typing import Any

from ui.core.qt import (
    QGraphicsScene,
    QGraphicsView,
    Qt,
)

from ui.canvas.coordinate_system import CoordinateSystem
from ui.canvas.grid_system import GridSystem
from ui.canvas.interaction_manager import InteractionManager


class GraphicsView(QGraphicsView):
    """
    Main graphical canvas view for GridForge.

    GraphicsView is deliberately a thin Qt adapter.

    Raw Qt input enters here and is forwarded to the
    InteractionManager. Application behavior is implemented
    outside this class.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        parent: Any = None,
    ) -> None:
        """
        Initialize the GridForge canvas.

        Parameters
        ----------
        controller:
            GridForge UI Controller.

        parent:
            Optional Qt parent widget.
        """

        super().__init__(parent)

        # ----------------------------------------------------
        # Controller
        # ----------------------------------------------------

        self.controller = controller

        # ----------------------------------------------------
        # Scene
        # ----------------------------------------------------
        #
        # GraphicsView owns the canvas scene.
        #
        # The scene is a UI representation container only.
        # The authoritative application state remains in Core.
        # ----------------------------------------------------

        self._scene = QGraphicsScene(self)

        self.setScene(self._scene)

        # ----------------------------------------------------
        # Grid system
        # ----------------------------------------------------
        #
        # GridSystem provides visual/grid-coordinate services.
        #
        # It does not own snapping decisions.
        # ----------------------------------------------------

        self.grid_system = GridSystem(
            self._scene
        )

        # ----------------------------------------------------
        # Coordinate system
        # ----------------------------------------------------
        #
        # CoordinateSystem depends on the view and GridSystem.
        # ----------------------------------------------------

        self.coordinate_system = CoordinateSystem(
            view=self,
            grid_system=self.grid_system,
        )

        # ----------------------------------------------------
        # Interaction manager
        # ----------------------------------------------------
        #
        # InteractionManager owns transient interaction state,
        # PreviewLayer, SnapSystem and ToolManager.
        # ----------------------------------------------------

        self.interaction_manager = (
            InteractionManager(
                view=self,
                controller=controller,
            )
        )

        # ----------------------------------------------------
        # View configuration
        # ----------------------------------------------------

        self._configure_viewport()

    # ========================================================
    # VIEW CONFIGURATION
    # ========================================================

    def _configure_viewport(self) -> None:
        """
        Configure the basic canvas viewport.

        This method contains only presentation/input
        configuration. It does not implement application logic.
        """

        # ----------------------------------------------------
        # Receive mouse-move events even when no button is
        # pressed.
        #
        # Required for:
        #
        #     - tool previews
        #     - hover feedback
        #     - snapping feedback
        #     - coordinate display
        # ----------------------------------------------------

        self.setMouseTracking(True)

        # ----------------------------------------------------
        # Keyboard focus
        #
        # Required for:
        #
        #     - ESC cancellation
        #     - tool keyboard shortcuts
        #     - future canvas commands
        # ----------------------------------------------------

        self.setFocusPolicy(
            Qt.StrongFocus
        )

        # ----------------------------------------------------
        # Scroll bars
        #
        # Canvas navigation is expected to be handled by the
        # future NavigationController rather than relying on
        # standard scroll-bar interaction.
        # ----------------------------------------------------

        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        # ----------------------------------------------------
        # View interaction defaults
        #
        # Individual tools own application interaction.
        # Disable built-in drag behavior so QGraphicsView does
        # not compete with GridForge tools.
        # ----------------------------------------------------

        self.setDragMode(
            QGraphicsView.NoDrag
        )

    # ========================================================
    # MOUSE EVENTS
    # ========================================================

    def mousePressEvent(
        self,
        event: Any,
    ) -> None:
        """
        Receive a raw Qt mouse-press event.

        The event is routed exclusively through
        InteractionManager.

        GraphicsView does not execute tool logic itself.
        """

        self.setFocus()

        self.interaction_manager.mouse_press(
            event
        )

    # --------------------------------------------------------

    def mouseMoveEvent(
        self,
        event: Any,
    ) -> None:
        """
        Receive a raw Qt mouse-move event.

        The event is routed to InteractionManager.
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
        Receive a raw Qt mouse-release event.

        The event is routed exclusively through
        InteractionManager.
        """

        self.interaction_manager.mouse_release(
            event
        )

    # ========================================================
    # KEYBOARD EVENTS
    # ========================================================

    def keyPressEvent(
        self,
        event: Any,
    ) -> None:
        """
        Receive a raw Qt keyboard-press event.

        InteractionManager decides whether the active tool
        consumes the event.

        Unhandled events are passed to QGraphicsView so normal
        Qt behavior remains available where appropriate.
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
        Receive a raw Qt keyboard-release event.
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
    # SCENE ACCESS
    # ========================================================

    def get_scene(
        self,
    ) -> QGraphicsScene:
        """
        Return the canvas QGraphicsScene.

        The explicit accessor keeps scene ownership inside
        GraphicsView while allowing other UI systems to obtain
        the scene when necessary.
        """

        return self._scene

    # --------------------------------------------------------

    @property
    def scene_object(
        self,
    ) -> QGraphicsScene:
        """
        Return the canvas scene.

        This property exists as a convenient read-only access
        path for UI infrastructure.
        """

        return self._scene

    # ========================================================
    # CANVAS SYSTEM ACCESS
    # ========================================================

    def get_interaction_manager(
        self,
    ) -> InteractionManager:
        """
        Return the InteractionManager.
        """

        return self.interaction_manager

    # --------------------------------------------------------

    def get_coordinate_system(
        self,
    ) -> CoordinateSystem:
        """
        Return the CoordinateSystem.
        """

        return self.coordinate_system

    # --------------------------------------------------------

    def get_grid_system(
        self,
    ) -> GridSystem:
        """
        Return the GridSystem.
        """

        return self.grid_system

    # ========================================================
    # RESET
    # ========================================================

    def reset_canvas(
        self,
    ) -> None:
        """
        Reset transient canvas interaction state.

        This does NOT modify the domain model and does NOT
        destroy the authoritative application state.
        """

        self.interaction_manager.reset()

    # ========================================================
    # DEBUG / STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict:
        """
        Return diagnostic canvas state.
        """

        return {
            "scene": self._scene,
            "interaction_manager": (
                self.interaction_manager.get_state()
            ),
            "grid": (
                self.grid_system.get_grid_info()
            ),
            "coordinates": (
                self.coordinate_system.get_state()
            ),
        }

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "GraphicsView("
            f"scene_items={len(self._scene.items())}, "
            f"grid_visible={self.grid_system.visible}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "GraphicsView",
]
