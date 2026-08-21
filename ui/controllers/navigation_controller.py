# ============================================================
# File: ui/controllers/navigation_controller.py
# GridForge V2 — UI Navigation Controller
# ============================================================
"""
UI-level navigation controller for GridForge V2.

Architecture
------------

    MainWindow / UI
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
This class is a thin application/UI adapter around the
canonical canvas NavigationController.

The canvas NavigationController owns all navigation state and
behavior.

This class does not implement navigation mathematics and does
not maintain a second navigation state.

Responsibilities
----------------
    - expose the canvas navigation service;
    - delegate zoom operations;
    - delegate pan operations;
    - delegate wheel navigation;
    - delegate view reset;
    - delegate content fitting;
    - delegate coordinate conversion;
    - expose authoritative navigation state;
    - provide adapter lifecycle management.

This class does NOT:
    - calculate zoom transforms;
    - manipulate QGraphicsView directly;
    - maintain independent zoom state;
    - maintain independent pan state;
    - implement snapping;
    - implement selection;
    - implement tools;
    - render graphics;
    - modify Core/application state.

Authority
---------
The canvas NavigationController is the sole owner of actual
navigation state and behavior.

Qt Architecture
---------------
No direct Qt imports are used here.
"""

from __future__ import annotations

from typing import Any

from ui.canvas.navigation_controller import (
    NavigationController as CanvasNavigationController,
)


class NavigationController:
    """
    Thin UI adapter for the canonical canvas navigation service.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        canvas_navigation: CanvasNavigationController,
    ) -> None:
        """
        Initialize the UI navigation adapter.

        Parameters
        ----------
        canvas_navigation:
            Existing canvas-level NavigationController.

        The supplied controller is not copied or owned.
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
                "CanvasNavigationController."
            )

        self._canvas_navigation = canvas_navigation
        self._disposed = False

    # ========================================================
    # UNDERLYING SERVICE
    # ========================================================

    def get_canvas_navigation(
        self,
    ) -> CanvasNavigationController:
        """
        Return the authoritative canvas navigation controller.
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
        Delegate zoom-in to the canvas navigation controller.
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
        Delegate zoom-out to the canvas navigation controller.
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

        The position and factor are passed unchanged to the
        canonical canvas navigation implementation.
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
        Delegate wheel navigation.
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
        Start a canvas pan operation.
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
        Return whether the canvas is currently panning.
        """

        self._ensure_active()

        return bool(
            self._canvas_navigation.is_panning
        )

    # --------------------------------------------------------

    def pan_left(
        self,
    ) -> None:
        """
        Delegate leftward panning.
        """

        self._ensure_active()

        self._canvas_navigation.pan_left()

    # --------------------------------------------------------

    def pan_right(
        self,
    ) -> None:
        """
        Delegate rightward panning.
        """

        self._ensure_active()

        self._canvas_navigation.pan_right()

    # --------------------------------------------------------

    def pan_up(
        self,
    ) -> None:
        """
        Delegate upward panning.
        """

        self._ensure_active()

        self._canvas_navigation.pan_up()

    # --------------------------------------------------------

    def pan_down(
        self,
    ) -> None:
        """
        Delegate downward panning.
        """

        self._ensure_active()

        self._canvas_navigation.pan_down()

    # ========================================================
    # VIEW CONTROL
    # ========================================================

    def reset_view(
        self,
    ) -> None:
        """
        Delegate viewport reset.
        """

        self._ensure_active()

        self._canvas_navigation.reset_view()

    # --------------------------------------------------------

    def fit_content(
        self,
        margin: float = 50.0,
    ) -> None:
        """
        Delegate content fitting.
        """

        self._ensure_active()

        self._canvas_navigation.fit_content(
            margin
        )

    # ========================================================
    # COORDINATE CONVERSION
    # ========================================================

    def scene_position(
        self,
        viewport_position: Any,
    ) -> Any:
        """
        Convert a viewport position to scene coordinates.

        Coordinate conversion remains owned by the canvas
        navigation implementation.
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
    # NAVIGATION STATE
    # ========================================================

    @property
    def zoom_factor(
        self,
    ) -> float:
        """
        Return the authoritative canvas zoom factor.
        """

        self._ensure_active()

        return float(
            self._canvas_navigation.zoom_factor
        )

    # --------------------------------------------------------

    @property
    def min_zoom(
        self,
    ) -> float:
        """
        Return the minimum permitted zoom level.

        The value is read from the authoritative canvas
        navigation implementation.
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
        Return the maximum permitted zoom level.
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
        Return the configured zoom step.
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
        Return a lightweight navigation diagnostic state.

        The authoritative navigation values remain owned by the
        canvas NavigationController.
        """

        if self._disposed:
            return {
                "disposed": True,
            }

        return {
            "disposed": False,
            "zoom_factor": self.zoom_factor,
            "is_panning": self.is_panning,
            "min_zoom": self.min_zoom,
            "max_zoom": self.max_zoom,
            "zoom_step": self.zoom_step,
        }

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Dispose this adapter.

        The underlying canvas NavigationController is not
        disposed because this adapter does not own it.
        """

        if self._disposed:
            return

        self._disposed = True

    # ========================================================
    # INTERNAL
    # ========================================================

    def _ensure_active(
        self,
    ) -> None:
        """
        Ensure this adapter is active.
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
            f"zoom_factor={self.zoom_factor}, "
            f"is_panning={self.is_panning}"
            ")"
        )


__all__ = [
    "NavigationController",
]
