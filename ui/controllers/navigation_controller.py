# ============================================================
# File: ui/controllers/navigation_controller.py
# GridForge V2 — UI Navigation Controller
# ============================================================
"""
UI-level navigation adapter for GridForge V2.

The canonical navigation state and behavior remain owned by
ui.canvas.navigation_controller.NavigationController.

This class provides a thin application/UI boundary only.
It does not implement navigation mathematics or maintain a
second navigation state.
"""

from __future__ import annotations

from typing import Any

from ui.canvas.navigation_controller import (
    NavigationController as CanvasNavigationController,
)


class NavigationController:
    """Thin UI adapter around the canvas navigation controller."""

    def __init__(
        self,
        canvas_navigation: CanvasNavigationController,
    ) -> None:
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
    # SERVICE
    # ========================================================

    def get_canvas_navigation(
        self,
    ) -> CanvasNavigationController:
        """Return the authoritative canvas navigation service."""

        self._ensure_active()
        return self._canvas_navigation

    # ========================================================
    # ZOOM
    # ========================================================

    def zoom_in(
        self,
        steps: int = 1,
    ) -> None:
        """Delegate zoom-in."""

        self._ensure_active()
        self._canvas_navigation.zoom_in(steps)

    def zoom_out(
        self,
        steps: int = 1,
    ) -> None:
        """Delegate zoom-out."""

        self._ensure_active()
        self._canvas_navigation.zoom_out(steps)

    def zoom_at(
        self,
        viewport_position: Any,
        factor: float,
    ) -> None:
        """Delegate zoom around a viewport position."""

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
    # WHEEL
    # ========================================================

    def handle_wheel(
        self,
        event: Any,
    ) -> None:
        """Delegate wheel navigation."""

        self._ensure_active()

        if event is None:
            raise ValueError(
                "event must not be None."
            )

        self._canvas_navigation.handle_wheel(event)

    # ========================================================
    # PAN
    # ========================================================

    def start_pan(
        self,
        viewport_position: Any,
    ) -> None:
        """Start panning."""

        self._ensure_active()

        if viewport_position is None:
            raise ValueError(
                "viewport_position must not be None."
            )

        self._canvas_navigation.start_pan(
            viewport_position
        )

    def update_pan(
        self,
        viewport_position: Any,
    ) -> None:
        """Update panning."""

        self._ensure_active()

        if viewport_position is None:
            raise ValueError(
                "viewport_position must not be None."
            )

        self._canvas_navigation.update_pan(
            viewport_position
        )

    def end_pan(self) -> None:
        """End panning."""

        self._ensure_active()
        self._canvas_navigation.end_pan()

    @property
    def is_panning(self) -> bool:
        """Return whether panning is active."""

        self._ensure_active()
        return bool(
            self._canvas_navigation.is_panning
        )

    def pan_left(self) -> None:
        """Pan left."""

        self._ensure_active()
        self._canvas_navigation.pan_left()

    def pan_right(self) -> None:
        """Pan right."""

        self._ensure_active()
        self._canvas_navigation.pan_right()

    def pan_up(self) -> None:
        """Pan up."""

        self._ensure_active()
        self._canvas_navigation.pan_up()

    def pan_down(self) -> None:
        """Pan down."""

        self._ensure_active()
        self._canvas_navigation.pan_down()

    # ========================================================
    # VIEW
    # ========================================================

    def reset_view(self) -> None:
        """Reset the view."""

        self._ensure_active()
        self._canvas_navigation.reset_view()

    def fit_content(
        self,
        margin: float = 50.0,
    ) -> None:
        """Fit canvas content."""

        self._ensure_active()
        self._canvas_navigation.fit_content(margin)

    # ========================================================
    # COORDINATES
    # ========================================================

    def scene_position(
        self,
        viewport_position: Any,
    ) -> Any:
        """Convert viewport coordinates to scene coordinates."""

        self._ensure_active()

        if viewport_position is None:
            raise ValueError(
                "viewport_position must not be None."
            )

        return self._canvas_navigation.scene_position(
            viewport_position
        )

    # ========================================================
    # STATE
    # ========================================================

    @property
    def zoom_factor(self) -> float:
        """Return authoritative zoom factor."""

        self._ensure_active()
        return float(
            self._canvas_navigation.zoom_factor
        )

    @property
    def min_zoom(self) -> float:
        """Return minimum zoom."""

        self._ensure_active()
        return float(
            self._canvas_navigation.MIN_ZOOM
        )

    @property
    def max_zoom(self) -> float:
        """Return maximum zoom."""

        self._ensure_active()
        return float(
            self._canvas_navigation.MAX_ZOOM
        )

    @property
    def zoom_step(self) -> float:
        """Return configured zoom step."""

        self._ensure_active()
        return float(
            self._canvas_navigation.ZOOM_STEP
        )

    def get_state(self) -> dict[str, Any]:
        """Return adapter-level diagnostic state."""

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

    def dispose(self) -> None:
        """
        Dispose this adapter.

        The underlying canvas navigation controller is not
        disposed because ownership remains external.
        """

        self._disposed = True

    # ========================================================
    # INTERNAL
    # ========================================================

    def _ensure_active(self) -> None:
        """Reject operations after disposal."""

        if self._disposed:
            raise RuntimeError(
                "NavigationController has been disposed."
            )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
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
