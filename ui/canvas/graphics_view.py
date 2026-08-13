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
    - forwarding input to InteractionManager;
    - enabling mouse tracking;
    - receiving keyboard focus;
    - exposing the scene through a stable accessor;
    - providing the future boundary for navigation behavior.

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

    Qt input
        │
        ▼
    GraphicsView
        │
        ▼
    InteractionManager
        │
        ▼
    ToolManager / Active Tool
        │
        ▼
    Controller
        │
        ▼
    Core Model

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


class GraphicsView(QGraphicsView):
    """
    GridForge canvas viewport.

    GraphicsView is intentionally thin.

    Raw Qt events enter here and are delegated to the
    InteractionManager. Canvas interaction policy remains outside
    the Qt viewport itself.
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
        #
        # GraphicsView owns the Qt scene container.
        #
        # The scene contains UI graphics only. It is not the
        # authoritative electrical model.
        # ----------------------------------------------------

        self._scene = QGraphicsScene(self)

        self.setScene(self._scene)

        # ----------------------------------------------------
        # Interaction system
        # ----------------------------------------------------
        #
        # InteractionManager owns transient interaction state,
        # PreviewLayer, SnapSystem and ToolManager.
        # ----------------------------------------------------

        self.interaction_manager = InteractionManager(
            self,
            controller,
        )

        # ----------------------------------------------------
        # Mouse tracking
        # ----------------------------------------------------
        #
        # Required for:
        #
        #     - cursor tracking
        #     - snapping
        #     - placement previews
        #     - line previews
        #
        # MouseMove events must therefore arrive even when no
        # mouse button is pressed.
        # ----------------------------------------------------

        self.setMouseTracking(True)

        # ----------------------------------------------------
        # Keyboard focus
        # ----------------------------------------------------
        #
        # InteractionManager centrally handles keyboard input,
        # including ESC cancellation.
        #
        # The view must therefore be capable of receiving
        # keyboard focus.
        # ----------------------------------------------------

        self.setFocusPolicy(
            Qt.StrongFocus
        )

        # ----------------------------------------------------
        # Scrollbars
        # ----------------------------------------------------
        #
        # Canvas navigation is a separate architectural concern.
        # Visible scrollbars are therefore disabled.
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
        Forward mouse-press events to InteractionManager.

        The active GridForge tool owns interpretation of the
        interaction. Qt's default scene interaction is therefore
        not invoked here.
        """

        # Ensure the canvas receives subsequent keyboard input.
        self.setFocus(
            Qt.MouseFocusReason
        )

        self.interaction_manager.mouse_press(
            event
        )

    # --------------------------------------------------------

    def mouseMoveEvent(
        self,
        event: Any,
    ) -> None:
        """
        Forward mouse-move events to InteractionManager.
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
        Forward mouse-release events to InteractionManager.
        """

        self.interaction_manager.mouse_release(
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
        Forward keyboard-press events to InteractionManager.

        If the interaction layer does not consume the event,
        normal QGraphicsView keyboard handling is allowed.
        """

        handled = self.interaction_manager.key_press(
            event
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

        If the interaction layer does not consume the event,
        normal QGraphicsView keyboard handling is allowed.
        """

        handled = self.interaction_manager.key_release(
            event
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

        GraphicsView remains the owner of the scene container.
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
            "mouse_tracking": self.hasMouseTracking(),
            "focus_policy": self.focusPolicy(),
            "interaction_manager": (
                self.interaction_manager is not None
            ),
        }

    # ========================================================
    # CLEANUP
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Release transient interaction resources.

        GraphicsView does not own the Controller or Core model,
        so neither is modified or destroyed here.
        """

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
            f"{self.hasMouseTracking()}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "GraphicsView",
]
