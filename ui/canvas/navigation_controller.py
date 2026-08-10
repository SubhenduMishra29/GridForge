# ============================================================
# File: ui/canvas/navigation_controller.py
# GridForge Canvas Navigation Controller
# ============================================================
#
# PURPOSE
# -------
# Provides centralized navigation behavior for the GridForge
# canvas.
#
# This class is responsible for:
#
#     - Zooming
#     - Mouse-wheel zoom
#     - Zoom around cursor position
#     - Panning
#     - Middle-mouse navigation
#     - Zoom limits
#     - Resetting the view
#     - Fitting the complete scene into the viewport
#
#
# ARCHITECTURE
# ------------
#
#                    GraphicsView
#                         │
#                         │ navigation events
#                         ▼
#                NavigationController
#                         │
#                         ▼
#                    QGraphicsView
#
#
# IMPORTANT
# ---------
#
# NavigationController does NOT:
#
#     - create model objects
#     - modify the Core model
#     - handle electrical topology
#     - handle tools
#     - handle selection
#     - render graphics
#
# Navigation is purely a canvas/view concern.
#
#
# QT RULE
# -------
#
# This project uses PySide6 exclusively.
#
# However, individual UI modules must NOT import PySide6
# directly.
#
# All Qt dependencies come through:
#
#     ui.core.qt
#
#
# DESIGN GOAL
# -----------
#
# GraphicsView should remain a thin adapter.
#
# Instead of putting zoom/pan logic directly inside
# GraphicsView, it delegates navigation behavior here.
#
# This allows navigation to evolve independently and prevents
# GraphicsView from becoming a monolithic class.
#
# ============================================================

from __future__ import annotations

from typing import Any


from ui.core.qt import (
    QPoint,
    QRectF,
    Qt,
)


class NavigationController:
    """
    Central controller for GridForge canvas navigation.

    The class operates on a QGraphicsView supplied during
    construction.

    No application model is required because navigation does
    not modify electrical data.
    """

    # ========================================================
    # ZOOM CONFIGURATION
    # ========================================================

    # Minimum allowed zoom factor.
    #
    # Prevents the user from zooming so far out that the
    # complete canvas becomes unusably small.
    MIN_ZOOM = 0.10

    # Maximum allowed zoom factor.
    #
    # Prevents excessive magnification.
    MAX_ZOOM = 20.0

    # Default zoom factor.
    DEFAULT_ZOOM = 1.0

    # Zoom multiplier used for each zoom step.
    ZOOM_STEP = 1.15

    # Number of pixels used to translate one pan movement.
    PAN_STEP = 20

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        view: Any,
    ) -> None:
        """
        Initialize the navigation controller.

        Parameters
        ----------
        view:
            GridForge QGraphicsView instance.

        The controller does not take ownership of the view.
        """

        self.view = view

        # ----------------------------------------------------
        # Track accumulated zoom.
        #
        # QGraphicsView internally stores its transformation,
        # but maintaining a logical zoom factor makes it much
        # easier to enforce project-wide zoom limits.
        # ----------------------------------------------------

        self.zoom_factor = self.DEFAULT_ZOOM

        # ----------------------------------------------------
        # Pan state.
        # ----------------------------------------------------

        self._panning = False

        self._pan_start = QPoint()

    # ========================================================
    # ZOOM
    # ========================================================

    def zoom_in(
        self,
        steps: int = 1,
    ) -> None:
        """
        Zoom into the canvas.

        Parameters
        ----------
        steps:
            Number of zoom increments.
        """

        if steps <= 0:
            return

        for _ in range(steps):
            self._apply_zoom(
                self.ZOOM_STEP
            )

    # --------------------------------------------------------

    def zoom_out(
        self,
        steps: int = 1,
    ) -> None:
        """
        Zoom out of the canvas.

        Parameters
        ----------
        steps:
            Number of zoom increments.
        """

        if steps <= 0:
            return

        for _ in range(steps):
            self._apply_zoom(
                1.0 / self.ZOOM_STEP
            )

    # --------------------------------------------------------

    def _apply_zoom(
        self,
        factor: float,
    ) -> None:
        """
        Apply a single zoom operation.

        Zoom is clamped between MIN_ZOOM and MAX_ZOOM.
        """

        if factor <= 0:
            return

        new_zoom = (
            self.zoom_factor * factor
        )

        # ----------------------------------------------------
        # Enforce zoom limits.
        # ----------------------------------------------------

        new_zoom = max(
            self.MIN_ZOOM,
            min(
                self.MAX_ZOOM,
                new_zoom,
            ),
        )

        # ----------------------------------------------------
        # Calculate actual transformation factor.
        #
        # If the requested zoom is already outside the limits,
        # the actual transformation must be based on the
        # clamped value rather than the requested value.
        # ----------------------------------------------------

        actual_factor = (
            new_zoom / self.zoom_factor
        )

        if actual_factor == 1.0:
            return

        # ----------------------------------------------------
        # Zoom around the current viewport center.
        #
        # Cursor-centered zoom is implemented separately by
        # zoom_at().
        # ----------------------------------------------------

        self.view.scale(
            actual_factor,
            actual_factor,
        )

        self.zoom_factor = new_zoom

    # ========================================================
    # CURSOR-CENTERED ZOOM
    # ========================================================

    def zoom_at(
        self,
        viewport_pos: QPoint,
        factor: float,
    ) -> None:
        """
        Zoom around a specific viewport position.

        This is the preferred method for mouse-wheel zoom.

        Parameters
        ----------
        viewport_pos:
            Mouse position in viewport coordinates.

        factor:
            Zoom multiplier.

        The point under the mouse cursor remains approximately
        stationary during the zoom operation.
        """

        if factor <= 0:
            return

        # ----------------------------------------------------
        # Determine requested zoom.
        # ----------------------------------------------------

        requested_zoom = (
            self.zoom_factor * factor
        )

        # ----------------------------------------------------
        # Clamp zoom.
        # ----------------------------------------------------

        new_zoom = max(
            self.MIN_ZOOM,
            min(
                self.MAX_ZOOM,
                requested_zoom,
            ),
        )

        if new_zoom == self.zoom_factor:
            return

        actual_factor = (
            new_zoom / self.zoom_factor
        )

        # ----------------------------------------------------
        # Record scene position before scaling.
        # ----------------------------------------------------

        scene_pos_before = (
            self.view.mapToScene(viewport_pos)
        )

        # ----------------------------------------------------
        # Apply scaling.
        # ----------------------------------------------------

        self.view.scale(
            actual_factor,
            actual_factor,
        )

        self.zoom_factor = new_zoom

        # ----------------------------------------------------
        # Determine where the same scene point moved to after
        # scaling.
        # ----------------------------------------------------

        scene_pos_after = (
            self.view.mapToScene(viewport_pos)
        )

        # ----------------------------------------------------
        # Correct the view so the original scene point remains
        # under the cursor.
        # ----------------------------------------------------

        delta = (
            scene_pos_after
            - scene_pos_before
        )

        self.view.translate(
            delta.x(),
            delta.y(),
        )

    # ========================================================
    # MOUSE-WHEEL ZOOM
    # ========================================================

    def handle_wheel(
        self,
        event: Any,
    ) -> None:
        """
        Handle a Qt wheel event.

        Positive wheel movement:
            Zoom in.

        Negative wheel movement:
            Zoom out.

        The zoom is centered on the mouse cursor.
        """

        delta = event.angleDelta().y()

        if delta == 0:
            return

        # ----------------------------------------------------
        # Determine direction.
        # ----------------------------------------------------

        if delta > 0:

            factor = self.ZOOM_STEP

        else:

            factor = 1.0 / self.ZOOM_STEP

        # ----------------------------------------------------
        # Zoom around cursor.
        # ----------------------------------------------------

        self.zoom_at(
            event.position().toPoint(),
            factor,
        )

        # ----------------------------------------------------
        # Consume the event.
        # ----------------------------------------------------

        event.accept()

    # ========================================================
    # PAN
    # ========================================================

    def start_pan(
        self,
        viewport_pos: QPoint,
    ) -> None:
        """
        Start a pan operation.

        Typically called when the middle mouse button is
        pressed.
        """

        self._panning = True

        self._pan_start = viewport_pos

    # --------------------------------------------------------

    def update_pan(
        self,
        viewport_pos: QPoint,
    ) -> None:
        """
        Update the current pan operation.

        Parameters
        ----------
        viewport_pos:
            Current mouse position in viewport coordinates.
        """

        if not self._panning:
            return

        # ----------------------------------------------------
        # Calculate movement in viewport coordinates.
        # ----------------------------------------------------

        delta = (
            viewport_pos
            - self._pan_start
        )

        if delta.isNull():
            return

        # ----------------------------------------------------
        # Move scrollbars.
        #
        # Using scrollbars rather than manipulating the scene
        # transform keeps panning independent of zoom.
        # ----------------------------------------------------

        horizontal = (
            self.view.horizontalScrollBar()
        )

        vertical = (
            self.view.verticalScrollBar()
        )

        horizontal.setValue(
            horizontal.value()
            - delta.x()
        )

        vertical.setValue(
            vertical.value()
            - delta.y()
        )

        # ----------------------------------------------------
        # Update starting point.
        # ----------------------------------------------------

        self._pan_start = viewport_pos

    # --------------------------------------------------------

    def end_pan(self) -> None:
        """
        Finish the current pan operation.
        """

        self._panning = False

    # --------------------------------------------------------

    @property
    def is_panning(self) -> bool:
        """
        Return True while a pan operation is active.
        """

        return self._panning

    # ========================================================
    # RESET VIEW
    # ========================================================

    def reset_view(self) -> None:
        """
        Reset the canvas to its default zoom and transformation.

        This does not modify the scene or model.
        """

        self.view.resetTransform()

        self.zoom_factor = (
            self.DEFAULT_ZOOM
        )

        # ----------------------------------------------------
        # Center the view on the scene center.
        # ----------------------------------------------------

        scene = self.view.scene()

        if scene is not None:

            self.view.centerOn(
                scene.sceneRect().center()
            )

    # ========================================================
    # FIT CONTENT
    # ========================================================

    def fit_content(
        self,
        margin: float = 50.0,
    ) -> None:
        """
        Fit all scene content into the viewport.

        Parameters
        ----------
        margin:
            Additional scene-space margin around the content.

        Notes
        -----
        This method does not modify model coordinates.
        """

        scene = self.view.scene()

        if scene is None:
            return

        # ----------------------------------------------------
        # Obtain items bounding rectangle.
        # ----------------------------------------------------

        content_rect = (
            scene.itemsBoundingRect()
        )

        if content_rect.isNull():
            return

        # ----------------------------------------------------
        # Add margin around the content.
        # ----------------------------------------------------

        content_rect = content_rect.adjusted(
            -margin,
            -margin,
            margin,
            margin,
        )

        # ----------------------------------------------------
        # Fit the rectangle into the viewport.
        # ----------------------------------------------------

        self.view.fitInView(
            content_rect,
            Qt.AspectRatioMode.KeepAspectRatio,
        )

        # ----------------------------------------------------
        # fitInView changes the transform directly.
        #
        # Therefore reset the logical zoom tracking.
        #
        # The exact transform scale will be recalculated from
        # the view when more advanced navigation state is added.
        # ----------------------------------------------------

        self.zoom_factor = (
            self.DEFAULT_ZOOM
        )

    # ========================================================
    # PAN KEYBOARD SUPPORT
    # ========================================================

    def pan_left(self) -> None:
        """
        Pan the viewport to the left.
        """

        self._pan_by(
            -self.PAN_STEP,
            0,
        )

    # --------------------------------------------------------

    def pan_right(self) -> None:
        """
        Pan the viewport to the right.
        """

        self._pan_by(
            self.PAN_STEP,
            0,
        )

    # --------------------------------------------------------

    def pan_up(self) -> None:
        """
        Pan the viewport upward.
        """

        self._pan_by(
            0,
            -self.PAN_STEP,
        )

    # --------------------------------------------------------

    def pan_down(self) -> None:
        """
        Pan the viewport downward.
        """

        self._pan_by(
            0,
            self.PAN_STEP,
        )

    # --------------------------------------------------------

    def _pan_by(
        self,
        dx: int,
        dy: int,
    ) -> None:
        """
        Move the viewport by a fixed number of pixels.

        This helper centralizes keyboard/programmatic panning.
        """

        horizontal = (
            self.view.horizontalScrollBar()
        )

        vertical = (
            self.view.verticalScrollBar()
        )

        horizontal.setValue(
            horizontal.value() + dx
        )

        vertical.setValue(
            vertical.value() + dy
        )

    # ========================================================
    # SCENE COORDINATE HELPERS
    # ========================================================

    def scene_position(
        self,
        viewport_pos: QPoint,
    ) -> Any:
        """
        Convert a viewport coordinate to a scene coordinate.

        This is a convenience wrapper so other canvas systems
        do not need to directly depend on QGraphicsView mapping.
        """

        return self.view.mapToScene(
            viewport_pos
        )

    # ========================================================
    # DEBUG / STATE
    # ========================================================

    def get_state(self) -> dict:
        """
        Return the current navigation state.

        Useful for debugging and future persistence.
        """

        return {
            "zoom_factor": self.zoom_factor,
            "is_panning": self._panning,
        }


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "NavigationController",
]
