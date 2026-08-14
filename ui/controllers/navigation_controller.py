# ============================================================
# File: ui/controllers/navigation_controller.py
# GridForge V2 — UI Navigation Controller
# ============================================================
"""
UI-level navigation controller for GridForge V2.

Architecture
------------

    MainWindow / Plugin
            │
            ▼
    UI NavigationController
            │
            ▼
    Canvas NavigationController
            │
            ▼
       GraphicsView
            │
            ▼
         QGraphicsScene

Purpose
-------
This controller provides the application/UI composition boundary
for canvas navigation.

The actual navigation implementation remains in:

    ui.canvas.navigation_controller.NavigationController

This class is deliberately a thin adapter.

It does NOT:

    - implement zoom mathematics;
    - implement panning mathematics;
    - manipulate QGraphicsView transforms directly;
    - modify Core/application model state;
    - implement tools;
    - implement selection;
    - perform snapping;
    - render graphics;
    - calculate electrical quantities;
    - own navigation state independently.

Authority
---------
The canvas NavigationController remains the single owner of
navigation state and behavior.

This class only delegates to it.

Qt Architecture
---------------
This module contains no direct Qt imports.

All Qt-specific navigation behavior remains inside the canvas
navigation implementation.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.canvas.navigation_controller import (
    NavigationController as CanvasNavigationController,
)


class NavigationController:
    """
    Thin UI orchestration adapter for canvas navigation.

    The underlying CanvasNavigationController owns all actual
    navigation state.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        canvas_navigation: CanvasNavigationController,
    ) -> None:
        """
        Initialize the UI navigation controller.

        Parameters
        ----------
        canvas_navigation:
            Existing canvas-level NavigationController.

        The supplied controller is not copied or duplicated.
        """

        if canvas_navigation is None:
            raise ValueError(
                "canvas_navigation must not be None."
            )

        if not isinstance(
            canvas_navigation,
            CanvasNavigationController,
        ):
            raise TypeError(
                "canvas_navigation must be a "
                "canvas NavigationController."
            )

        self._canvas_navigation = (
            canvas_navigation
        )

        self._disposed = False

    # ========================================================
    # UNDERLYING CONTROLLER
    # ========================================================

    def get_canvas_navigation(
        self,
    ) -> CanvasNavigationController:
        """
        Return the underlying canvas navigation controller.
        """

        self._ensure_active()

        return self._canvas_navigation

    # ========================================================
    # ZOOM
    # ========================================================

    def zoom_in(
        self,
        steps: int = 1,
    ) -> None:
        """
        Zoom into the canvas.
        """

        self._ensure_active()

        self._canvas_navigation.zoom_in(
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

        self._ensure_active()

        self._canvas_navigation.zoom_out(
            steps
        )

    # --------------------------------------------------------

    def zoom_at(
        self,
        viewport_position: Any,
        factor: float,
    ) -> None:
        """
        Zoom around a viewport position.

        The viewport position is forwarded unchanged to the
        canvas navigation implementation.
        """

        self._ensure_active()

        if viewport_position is None:
            raise ValueError(
                "viewport_position must not be None."
            )

        self._canvas_navigation.zoom_at(
            viewport_position,
            factor,
        )

    # ========================================================
    # WHEEL NAVIGATION
    # ========================================================

    def handle_wheel(
        self,
        event: Any,
    ) -> None:
        """
        Forward a wheel event to the canvas navigation system.
        """

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        self._canvas_navigation.handle_wheel(
            event
        )

    # ========================================================
    # PAN
    # ========================================================

    def start_pan(
        self,
        viewport_position: Any,
    ) -> None:
        """
        Start middle-mouse or programmatic canvas panning.
        """

        self._ensure_active()

        if viewport_position is None:
            raise ValueError(
                "viewport_position must not be None."
            )

        self._canvas_navigation.start_pan(
            viewport_position
        )

    # --------------------------------------------------------

    def update_pan(
        self,
        viewport_position: Any,
    ) -> None:
        """
        Update an active canvas pan operation.
        """

        self._ensure_active()

        if viewport_position is None:
            raise ValueError(
                "viewport_position must not be None."
            )

        self._canvas_navigation.update_pan(
            viewport_position
        )

    # --------------------------------------------------------

    def end_pan(
        self,
    ) -> None:
        """
        End the active canvas pan operation.
        """

        self._ensure_active()

        self._canvas_navigation.end_pan()

    # --------------------------------------------------------

    @property
    def is_panning(
        self,
    ) -> bool:
        """
        Return True while canvas panning is active.
        """

        self._ensure_active()

        return bool(
            self._canvas_navigation.is_panning
        )

    # ========================================================
    # KEYBOARD / PROGRAMMATIC PAN
    # ========================================================

    def pan_left(
        self,
    ) -> None:
        """
        Pan the canvas left.
        """

        self._ensure_active()

        self._canvas_navigation.pan_left()

    # --------------------------------------------------------

    def pan_right(
        self,
    ) -> None:
        """
        Pan the canvas right.
        """

        self._ensure_active()

        self._canvas_navigation.pan_right()

    # --------------------------------------------------------

    def pan_up(
        self,
    ) -> None:
        """
        Pan the canvas upward.
        """

        self._ensure_active()

        self._canvas_navigation.pan_up()

    # --------------------------------------------------------

    def pan_down(
        self,
    ) -> None:
        """
        Pan the canvas downward.
        """

        self._ensure_active()

        self._canvas_navigation.pan_down()

    # ========================================================
    # VIEW RESET
    # ========================================================

    def reset_view(
        self,
    ) -> None:
        """
        Reset canvas transformation and view position.
        """

        self._ensure_active()

        self._canvas_navigation.reset_view()

    # ========================================================
    # FIT CONTENT
    # ========================================================

    def fit_content(
        self,
        margin: float = 50.0,
    ) -> None:
        """
        Fit the complete graphical scene content into the view.
        """

        self._ensure_active()

        self._canvas_navigation.fit_content(
            margin
        )

    # ========================================================
    # SCENE POSITION
    # ========================================================

    def scene_position(
        self,
        viewport_position: Any,
    ) -> Any:
        """
        Convert a viewport position to scene coordinates.

        The actual coordinate mapping remains owned by the
        canvas navigation implementation.
        """

        self._ensure_active()

        if viewport_position is None:
            raise ValueError(
                "viewport_position must not be None."
            )

        return self._canvas_navigation.scene_position(
            viewport_position
        )

    # ========================================================
    # ZOOM STATE
    # ========================================================

    @property
    def zoom_factor(
        self,
    ) -> float:
        """
        Return the authoritative logical canvas zoom factor.
        """

        self._ensure_active()

        return float(
            self._canvas_navigation.zoom_factor
        )

    # --------------------------------------------------------

    def get_zoom_factor(
        self,
    ) -> float:
        """
        Return the current canvas zoom factor.
        """

        return self.zoom_factor

    # ========================================================
    # ZOOM LIMITS
    # ========================================================

    @property
    def min_zoom(
        self,
    ) -> float:
        """
        Return the minimum permitted canvas zoom.
        """

        self._ensure_active()

        return float(
            self._canvas_navigation.MIN_ZOOM
        )

    # --------------------------------------------------------

    @property
    def max_zoom(
        self,
    ) -> float:
        """
        Return the maximum permitted canvas zoom.
        """

        self._ensure_active()

        return float(
            self._canvas_navigation.MAX_ZOOM
        )

    # --------------------------------------------------------

    @property
    def zoom_step(
        self,
    ) -> float:
        """
        Return the configured zoom multiplier.
        """

        self._ensure_active()

        return float(
            self._canvas_navigation.ZOOM_STEP
        )

    # ========================================================
    # STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a navigation diagnostic snapshot.

        The underlying canvas controller remains authoritative.
        """

        if self._disposed:
            return {
                "disposed": True,
            }

        state: Optional[dict[str, Any]] = None

        getter = getattr(
            self._canvas_navigation,
            "get_state",
            None,
        )

        if callable(getter):
            state = getter()

        return {
            "disposed": False,
            "zoom_factor": self.zoom_factor,
            "is_panning": self.is_panning,
            "canvas_navigation": state,
        }

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Dispose this UI adapter.

        The underlying canvas NavigationController is not
        disposed because this adapter does not own it.
        """

        if self._disposed:
            return

        self._disposed = True

    # ========================================================
    # ACTIVE STATE
    # ========================================================

    def _ensure_active(
        self,
    ) -> None:
        """
        Ensure this adapter has not been disposed.
        """

        if self._disposed:
            raise RuntimeError(
                "NavigationController has been disposed."
            )

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
                "NavigationController("
                "disposed=True"
                ")"
            )

        return (
            "NavigationController("
            f"zoom={self.zoom_factor}, "
            f"panning={self.is_panning}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "NavigationController",
]
