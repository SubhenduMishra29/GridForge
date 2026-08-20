# ============================================================
# File: ui/canvas/navigation_controller.py
# GridForge V2 — Canvas Navigation Controller
# ============================================================
"""
Canvas-level navigation controller for GridForge V2.

NavigationController owns viewport navigation mechanics only.

Responsibilities
----------------
    - canvas zoom;
    - canvas panning;
    - view transformation;
    - wheel-based zoom;
    - middle-mouse pan state;
    - view reset;
    - fitting scene content into the viewport;
    - navigation diagnostics.

Architecture
------------

    GraphicsView
         │
         ▼
    NavigationController
         │
         ├── zoom
         ├── pan
         ├── reset
         └── fit
         │
         ▼
    QGraphicsView transform

NavigationController does NOT:

    - modify Core model state;
    - access the electrical model;
    - manage tools;
    - manage selection;
    - perform snapping;
    - perform rendering;
    - create graphics items;
    - own the QGraphicsScene;
    - decide application-level navigation policy;
    - communicate directly with domain objects.

Navigation transform contract
-----------------------------
GridForge navigation uses:

    - positive uniform scale;
    - viewport translation;
    - no rotation;
    - no shear;
    - no non-uniform scaling.

This makes the scalar ``_zoom_level`` an authoritative representation
of navigation scale.

Ownership
---------
GraphicsView owns the NavigationController instance.

NavigationController does not own the GraphicsView.

The supplied view is treated as the navigation target.

Qt Architecture
---------------
All Qt dependencies must be imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

import math
from typing import Any

from ui.core.qt import Qt


class NavigationController:
    """
    Canvas-level navigation mechanics.

    The controller is deliberately independent of GridForge Core.

    It operates only on the supplied GraphicsView and its viewport
    transform/scrollbars.
    """

    # ========================================================
    # DEFAULT CONFIGURATION
    # ========================================================

    DEFAULT_ZOOM_FACTOR = 1.15

    DEFAULT_MIN_ZOOM = 0.10
    DEFAULT_MAX_ZOOM = 20.0

    DEFAULT_PAN_BUTTON = Qt.MiddleButton

    DEFAULT_FIT_MARGIN = 50.0

    # Numerical tolerance used when validating QTransform values.
    TRANSFORM_TOLERANCE = 1.0e-9

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        view: Any,
        *,
        zoom_factor: float = DEFAULT_ZOOM_FACTOR,
        min_zoom: float = DEFAULT_MIN_ZOOM,
        max_zoom: float = DEFAULT_MAX_ZOOM,
    ) -> None:
        """
        Initialize canvas navigation.

        Parameters
        ----------
        view:
            GraphicsView receiving navigation operations.

        zoom_factor:
            Multiplicative zoom factor for one zoom step.

        min_zoom:
            Minimum allowed relative zoom.

        max_zoom:
            Maximum allowed relative zoom.
        """

        if view is None:
            raise ValueError(
                "view must not be None."
            )

        self.view = view

        self.zoom_factor = self._validate_zoom_factor(
            zoom_factor
        )

        self.min_zoom = self._validate_zoom_limit(
            min_zoom,
            "min_zoom",
        )

        self.max_zoom = self._validate_zoom_limit(
            max_zoom,
            "max_zoom",
        )

        if self.min_zoom > self.max_zoom:
            raise ValueError(
                "min_zoom must not be greater than max_zoom."
            )

        # ----------------------------------------------------
        # Navigation state.
        #
        # The zoom level represents positive uniform scale
        # relative to the identity transform.
        # ----------------------------------------------------

        self._zoom_level = self._estimate_zoom_level()

        self._is_panning = False
        self._pan_start = None

        self._disposed = False

    # ========================================================
    # VIEW ACCESS
    # ========================================================

    def get_view(
        self,
    ) -> Any:
        """
        Return the GraphicsView controlled by this instance.
        """

        return self.view

    # ========================================================
    # PAN STATE
    # ========================================================

    @property
    def is_panning(
        self,
    ) -> bool:
        """
        Return True while middle-button panning is active.
        """

        return self._is_panning

    # --------------------------------------------------------

    def start_pan(
        self,
        position: Any,
    ) -> None:
        """
        Begin middle-button panning.

        Parameters
        ----------
        position:
            Viewport-space position providing x() and y().
        """

        self._validate_position(
            position,
            "position",
        )

        self._ensure_active()

        self._is_panning = True
        self._pan_start = position

    # --------------------------------------------------------

    def update_pan(
        self,
        position: Any,
    ) -> None:
        """
        Update an active pan operation.

        The operation is ignored when panning is not active.
        """

        self._validate_position(
            position,
            "position",
        )

        self._ensure_active()

        if not self._is_panning:
            return

        if self._pan_start is None:
            self._is_panning = False
            return

        dx = (
            position.x()
            - self._pan_start.x()
        )

        dy = (
            position.y()
            - self._pan_start.y()
        )

        horizontal = self.view.horizontalScrollBar()
        vertical = self.view.verticalScrollBar()

        horizontal.setValue(
            horizontal.value()
            - int(dx)
        )

        vertical.setValue(
            vertical.value()
            - int(dy)
        )

        self._pan_start = position

    # --------------------------------------------------------

    def end_pan(
        self,
    ) -> None:
        """
        End the current pan operation.
        """

        self._is_panning = False
        self._pan_start = None

    # ========================================================
    # WHEEL
    # ========================================================

    def handle_wheel(
        self,
        event: Any,
    ) -> bool:
        """
        Handle a wheel event as canvas zoom.

        Returns
        -------
        bool
            True when the event was consumed.
        """

        if event is None:
            return False

        self._ensure_active()

        angle_delta = getattr(
            event,
            "angleDelta",
            None,
        )

        if not callable(angle_delta):
            return False

        delta = angle_delta()

        if delta is None:
            return False

        y_method = getattr(
            delta,
            "y",
            None,
        )

        if not callable(y_method):
            return False

        try:
            value = y_method()
        except Exception:
            return False

        if isinstance(value, bool):
            return False

        if not isinstance(value, (int, float)):
            return False

        if value == 0:
            return False

        steps = value / 120.0

        position = None

        position_method = getattr(
            event,
            "position",
            None,
        )

        if callable(position_method):
            try:
                position = position_method()
            except Exception:
                position = None

        if position is not None:
            try:
                self._validate_position(
                    position,
                    "position",
                )
            except (TypeError, ValueError):
                position = None

        if position is not None:
            self._zoom_at(
                steps,
                position,
            )
        else:
            self._zoom(
                steps
            )

        accept = getattr(
            event,
            "accept",
            None,
        )

        if callable(accept):
            accept()

        return True

    # ========================================================
    # ZOOM
    # ========================================================

    def zoom_in(
        self,
        steps: int = 1,
    ) -> None:
        """
        Zoom into the canvas.

        Positive steps increase zoom.
        """

        steps = self._validate_steps(
            steps
        )

        if steps == 0:
            return

        self._ensure_active()

        self._zoom(
            float(steps)
        )

    # --------------------------------------------------------

    def zoom_out(
        self,
        steps: int = 1,
    ) -> None:
        """
        Zoom out of the canvas.

        Positive steps decrease zoom.
        """

        steps = self._validate_steps(
            steps
        )

        if steps == 0:
            return

        self._ensure_active()

        self._zoom(
            -float(steps)
        )

    # --------------------------------------------------------

    def _zoom(
        self,
        steps: float,
    ) -> None:
        """
        Apply zoom steps around the viewport center.
        """

        if steps == 0:
            return

        target = (
            self._zoom_level
            * (
                self.zoom_factor
                ** steps
            )
        )

        target = self._clamp_zoom(
            target
        )

        factor = (
            target
            / self._zoom_level
        )

        if math.isclose(
            factor,
            1.0,
            rel_tol=self.TRANSFORM_TOLERANCE,
            abs_tol=self.TRANSFORM_TOLERANCE,
        ):
            return

        center = self._viewport_center()

        self._scale_at(
            factor,
            center,
        )

        self._zoom_level = self._estimate_zoom_level()

        self._zoom_level = self._clamp_zoom(
            self._zoom_level
        )

    # --------------------------------------------------------

    def _zoom_at(
        self,
        steps: float,
        position: Any,
    ) -> None:
        """
        Apply zoom around a viewport position.

        The cursor remains anchored to the same scene location.
        """

        self._validate_position(
            position,
            "position",
        )

        if steps == 0:
            return

        target = (
            self._zoom_level
            * (
                self.zoom_factor
                ** steps
            )
        )

        target = self._clamp_zoom(
            target
        )

        factor = (
            target
            / self._zoom_level
        )

        if math.isclose(
            factor,
            1.0,
            rel_tol=self.TRANSFORM_TOLERANCE,
            abs_tol=self.TRANSFORM_TOLERANCE,
        ):
            return

        self._scale_at(
            factor,
            position,
        )

        self._zoom_level = self._estimate_zoom_level()

        self._zoom_level = self._clamp_zoom(
            self._zoom_level
        )

    # --------------------------------------------------------

    def _scale_at(
        self,
        factor: float,
        position: Any,
    ) -> None:
        """
        Scale the view while preserving the scene point under
        ``position``.

        Parameters
        ----------
        factor:
            Positive uniform scale multiplier.

        position:
            Viewport-space anchor position.
        """

        if factor <= 0.0:
            raise ValueError(
                "scale factor must be greater than zero."
            )

        self._validate_position(
            position,
            "position",
        )

        scene_position = self.view.mapToScene(
            self._to_point(position)
        )

        self.view.scale(
            factor,
            factor,
        )

        mapped_position = self.view.mapFromScene(
            scene_position
        )

        delta_x = (
            mapped_position.x()
            - position.x()
        )

        delta_y = (
            mapped_position.y()
            - position.y()
        )

        horizontal = self.view.horizontalScrollBar()
        vertical = self.view.verticalScrollBar()

        horizontal.setValue(
            horizontal.value()
            + int(round(delta_x))
        )

        vertical.setValue(
            vertical.value()
            + int(round(delta_y))
        )

    # ========================================================
    # ZOOM STATE
    # ========================================================

    def get_zoom_level(
        self,
    ) -> float:
        """
        Return the current relative zoom level.
        """

        return self._zoom_level

    # --------------------------------------------------------

    def set_zoom_level(
        self,
        level: float,
    ) -> None:
        """
        Set the relative zoom level.

        The requested level is clamped to the configured range.

        Programmatic zoom is anchored at the viewport center.
        """

        if isinstance(
            level,
            bool,
        ) or not isinstance(
            level,
            (int, float),
        ):
            raise TypeError(
                "level must be numeric."
            )

        level = float(level)

        if not math.isfinite(level):
            raise ValueError(
                "level must be finite."
            )

        if level <= 0.0:
            raise ValueError(
                "level must be greater than zero."
            )

        self._ensure_active()

        target = self._clamp_zoom(
            level
        )

        factor = (
            target
            / self._zoom_level
        )

        if math.isclose(
            factor,
            1.0,
            rel_tol=self.TRANSFORM_TOLERANCE,
            abs_tol=self.TRANSFORM_TOLERANCE,
        ):
            self._zoom_level = target
            return

        self._scale_at(
            factor,
            self._viewport_center(),
        )

        self._zoom_level = self._estimate_zoom_level()

        self._zoom_level = self._clamp_zoom(
            self._zoom_level
        )

    # ========================================================
    # RESET
    # ========================================================

    def reset_view(
        self,
    ) -> None:
        """
        Reset the viewport transform and navigation state.
        """

        self._ensure_active()

        self.end_pan()

        self.view.resetTransform()

        self._zoom_level = 1.0

    # ========================================================
    # FIT CONTENT
    # ========================================================

    def fit_content(
        self,
        margin: float = DEFAULT_FIT_MARGIN,
    ) -> None:
        """
        Fit visible scene content into the viewport.

        Parameters
        ----------
        margin:
            Margin in viewport pixels.

        The content is fitted with preserved aspect ratio and
        then reduced uniformly so that the requested viewport
        margin remains available.

        Navigation state is synchronized from the resulting
        transform.
        """

        if isinstance(
            margin,
            bool,
        ) or not isinstance(
            margin,
            (int, float),
        ):
            raise TypeError(
                "margin must be numeric."
            )

        margin = float(margin)

        if not math.isfinite(margin):
            raise ValueError(
                "margin must be finite."
            )

        if margin < 0.0:
            raise ValueError(
                "margin must not be negative."
            )

        self._ensure_active()

        scene = self.view.scene()

        if scene is None:
            return

        items = scene.items()

        if not items:
            return

        rect = scene.itemsBoundingRect()

        if rect.isNull() or rect.isEmpty():
            return

        viewport = self.view.viewport()

        viewport_width = float(
            viewport.width()
        )

        viewport_height = float(
            viewport.height()
        )

        if viewport_width <= 0.0:
            return

        if viewport_height <= 0.0:
            return

        available_width = (
            viewport_width
            - 2.0 * margin
        )

        available_height = (
            viewport_height
            - 2.0 * margin
        )

        if (
            available_width <= 0.0
            or available_height <= 0.0
        ):
            return

        self.end_pan()

        # ----------------------------------------------------
        # Reset first so fitInView calculates the fit from a
        # deterministic transform.
        # ----------------------------------------------------

        self.view.resetTransform()

        self.view.fitInView(
            rect,
            Qt.KeepAspectRatio,
        )

        # ----------------------------------------------------
        # Reduce the fitted transform to accommodate the
        # requested viewport-pixel margin.
        # ----------------------------------------------------

        width_factor = (
            available_width
            / viewport_width
        )

        height_factor = (
            available_height
            / viewport_height
        )

        margin_factor = min(
            1.0,
            width_factor,
            height_factor,
        )

        if margin_factor < 1.0:
            self._scale_at(
                margin_factor,
                self._viewport_center(),
            )

        # ----------------------------------------------------
        # Re-establish authoritative navigation state from
        # the actual transform.
        # ----------------------------------------------------

        actual_zoom = self._estimate_zoom_level()

        target_zoom = self._clamp_zoom(
            actual_zoom
        )

        if not math.isclose(
            target_zoom,
            actual_zoom,
            rel_tol=self.TRANSFORM_TOLERANCE,
            abs_tol=self.TRANSFORM_TOLERANCE,
        ):
            self._apply_zoom_level(
                target_zoom
            )

        self._zoom_level = self._estimate_zoom_level()

        self._zoom_level = self._clamp_zoom(
            self._zoom_level
        )

    # ========================================================
    # VIEW TRANSFORM
    # ========================================================

    def get_transform(
        self,
    ) -> Any:
        """
        Return the current viewport transform.
        """

        return self.view.transform()

    # --------------------------------------------------------

    def set_transform(
        self,
        transform: Any,
    ) -> None:
        """
        Replace the viewport transform.

        Only positive uniform scaling with translation is
        supported by the GridForge navigation contract.

        Rotation, shear, reflection and non-uniform scaling are
        rejected.
        """

        if transform is None:
            raise ValueError(
                "transform must not be None."
            )

        self._ensure_active()

        scale = self._validate_navigation_transform(
            transform
        )

        target = self._clamp_zoom(
            scale
        )

        # ----------------------------------------------------
        # If the supplied transform is outside the configured
        # zoom limits, preserve its translation while adjusting
        # only the uniform scale.
        # ----------------------------------------------------

        if not math.isclose(
            target,
            scale,
            rel_tol=self.TRANSFORM_TOLERANCE,
            abs_tol=self.TRANSFORM_TOLERANCE,
        ):
            self.view.setTransform(
                transform
            )

            self._zoom_level = scale

            self._apply_zoom_level(
                target
            )

            return

        self.view.setTransform(
            transform
        )

        self._zoom_level = scale

    # ========================================================
    # ZOOM LIMITS
    # ========================================================

    def set_zoom_limits(
        self,
        min_zoom: float,
        max_zoom: float,
    ) -> None:
        """
        Replace the allowed relative zoom range.

        If the current zoom lies outside the new range, the
        actual viewport transform is adjusted immediately.
        """

        min_zoom = self._validate_zoom_limit(
            min_zoom,
            "min_zoom",
        )

        max_zoom = self._validate_zoom_limit(
            max_zoom,
            "max_zoom",
        )

        if min_zoom > max_zoom:
            raise ValueError(
                "min_zoom must not be greater than max_zoom."
            )

        self._ensure_active()

        self.min_zoom = min_zoom
        self.max_zoom = max_zoom

        current = self._estimate_zoom_level()

        target = self._clamp_zoom(
            current
        )

        if math.isclose(
            target,
            current,
            rel_tol=self.TRANSFORM_TOLERANCE,
            abs_tol=self.TRANSFORM_TOLERANCE,
        ):
            self._zoom_level = current
            return

        self._apply_zoom_level(
            target
        )

    # --------------------------------------------------------

    def _clamp_zoom(
        self,
        level: float,
    ) -> float:
        """
        Clamp a zoom level to the configured range.
        """

        return max(
            self.min_zoom,
            min(
                self.max_zoom,
                float(level),
            ),
        )

    # --------------------------------------------------------

    def _apply_zoom_level(
        self,
        target: float,
    ) -> None:
        """
        Apply an absolute relative zoom level to the view.

        Scaling is anchored at the viewport center.
        """

        target = self._clamp_zoom(
            target
        )

        current = self._estimate_zoom_level()

        if current <= 0.0:
            current = 1.0

        factor = (
            target
            / current
        )

        if math.isclose(
            factor,
            1.0,
            rel_tol=self.TRANSFORM_TOLERANCE,
            abs_tol=self.TRANSFORM_TOLERANCE,
        ):
            self._zoom_level = target
            return

        self._scale_at(
            factor,
            self._viewport_center(),
        )

        self._zoom_level = self._estimate_zoom_level()

    # ========================================================
    # TRANSFORM INSPECTION
    # ========================================================

    def _estimate_zoom_level(
        self,
    ) -> float:
        """
        Estimate the current uniform scale from the view
        transform.

        The GridForge navigation model requires positive
        uniform scaling.

        If transform access is unavailable, identity scale is
        used as the safe fallback for lightweight test doubles.
        """

        transform = self.view.transform()

        m11 = getattr(
            transform,
            "m11",
            None,
        )

        m22 = getattr(
            transform,
            "m22",
            None,
        )

        if not callable(m11):
            return 1.0

        try:
            scale_x = float(
                m11()
            )
        except (TypeError, ValueError):
            return 1.0

        if not math.isfinite(scale_x):
            return 1.0

        if not callable(m22):
            return (
                scale_x
                if scale_x > 0.0
                else 1.0
            )

        try:
            scale_y = float(
                m22()
            )
        except (TypeError, ValueError):
            return (
                scale_x
                if scale_x > 0.0
                else 1.0
            )

        if (
            scale_x > 0.0
            and scale_y > 0.0
        ):
            return math.sqrt(
                scale_x * scale_y
            )

        return 1.0

    # --------------------------------------------------------

    @classmethod
    def _validate_navigation_transform(
        cls,
        transform: Any,
    ) -> float:
        """
        Validate and return the positive uniform scale of a
        navigation transform.

        Translation is permitted.

        Rotation, shear, reflection and non-uniform scaling
        are rejected.
        """

        def read_component(
            name: str,
        ) -> float:
            method = getattr(
                transform,
                name,
                None,
            )

            if not callable(method):
                raise TypeError(
                    "transform must provide "
                    f"{name}()."
                )

            try:
                value = float(
                    method()
                )
            except (TypeError, ValueError):
                raise TypeError(
                    f"transform.{name}() must return a number."
                ) from None

            if not math.isfinite(value):
                raise ValueError(
                    f"transform.{name}() must be finite."
                )

            return value

        m11 = read_component("m11")
        m12 = read_component("m12")
        m21 = read_component("m21")
        m22 = read_component("m22")

        tolerance = cls.TRANSFORM_TOLERANCE

        if m11 <= 0.0 or m22 <= 0.0:
            raise ValueError(
                "navigation transform must use positive scaling."
            )

        if not math.isclose(
            m11,
            m22,
            rel_tol=tolerance,
            abs_tol=tolerance,
        ):
            raise ValueError(
                "navigation transform must use uniform scaling."
            )

        if not math.isclose(
            m12,
            0.0,
            rel_tol=tolerance,
            abs_tol=tolerance,
        ) or not math.isclose(
            m21,
            0.0,
            rel_tol=tolerance,
            abs_tol=tolerance,
        ):
            raise ValueError(
                "navigation transform must not contain "
                "rotation or shear."
            )

        return m11

    # ========================================================
    # VIEWPORT HELPERS
    # ========================================================

    def _viewport_center(
        self,
    ) -> Any:
        """
        Return the center of the viewport in viewport
        coordinates.

        Uses the viewport's rect when available and falls back
        to the view dimensions for lightweight test doubles.
        """

        viewport = self.view.viewport()

        rect_method = getattr(
            viewport,
            "rect",
            None,
        )

        if callable(rect_method):
            rect = rect_method()

            center_method = getattr(
                rect,
                "center",
                None,
            )

            if callable(center_method):
                return center_method()

        width = float(
            viewport.width()
        )

        height = float(
            viewport.height()
        )

        return self._make_point(
            width / 2.0,
            height / 2.0,
        )

    # --------------------------------------------------------

    @staticmethod
    def _to_point(
        position: Any,
    ) -> Any:
        """
        Convert a QPointF-compatible object to a point accepted
        by QGraphicsView mapping APIs.
        """

        to_point = getattr(
            position,
            "toPoint",
            None,
        )

        if callable(to_point):
            return to_point()

        return position

    # --------------------------------------------------------

    @staticmethod
    def _make_point(
        x: float,
        y: float,
    ) -> Any:
        """
        Create a QPointF-compatible point without importing Qt
        classes directly.

        This helper is intentionally limited to environments
        where the viewport does not expose QRect.center().
        """

        try:
            from ui.core.qt import QPointF
        except ImportError:
            class _Point:
                def __init__(
                    self,
                    px: float,
                    py: float,
                ) -> None:
                    self._x = px
                    self._y = py

                def x(self) -> float:
                    return self._x

                def y(self) -> float:
                    return self._y

            return _Point(
                x,
                y,
            )

        return QPointF(
            x,
            y,
        )

    # ========================================================
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic navigation state.
        """

        return {
            "view": self.view is not None,
            "zoom_level": self._zoom_level,
            "zoom_factor": self.zoom_factor,
            "min_zoom": self.min_zoom,
            "max_zoom": self.max_zoom,
            "is_panning": self._is_panning,
            "has_pan_start": (
                self._pan_start is not None
            ),
            "disposed": self._disposed,
        }

    # ========================================================
    # CLEANUP
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Release transient navigation state.

        The GraphicsView itself is not destroyed.
        """

        if self._disposed:
            return

        self.end_pan()

        self._disposed = True

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_zoom_factor(
        value: float,
    ) -> float:
        """
        Validate a multiplicative zoom factor.
        """

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(
                "zoom_factor must be numeric."
            )

        value = float(value)

        if not math.isfinite(value):
            raise ValueError(
                "zoom_factor must be finite."
            )

        if value <= 1.0:
            raise ValueError(
                "zoom_factor must be greater than 1.0."
            )

        return value

    # --------------------------------------------------------

    @staticmethod
    def _validate_zoom_limit(
        value: float,
        name: str,
    ) -> float:
        """
        Validate one zoom boundary.
        """

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(
                f"{name} must be numeric."
            )

        value = float(value)

        if not math.isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        if value <= 0.0:
            raise ValueError(
                f"{name} must be greater than zero."
            )

        return value

    # --------------------------------------------------------

    @staticmethod
    def _validate_steps(
        steps: int,
    ) -> int:
        """
        Validate an integer zoom-step count.
        """

        if isinstance(
            steps,
            bool,
        ) or not isinstance(
            steps,
            int,
        ):
            raise TypeError(
                "steps must be an integer."
            )

        return steps

    # --------------------------------------------------------

    @staticmethod
    def _validate_position(
        position: Any,
        name: str,
    ) -> None:
        """
        Validate a QPointF-compatible viewport position.
        """

        if position is None:
            raise ValueError(
                f"{name} must not be None."
            )

        if not callable(
            getattr(
                position,
                "x",
                None,
            )
        ):
            raise TypeError(
                f"{name} must provide x()."
            )

        if not callable(
            getattr(
                position,
                "y",
                None,
            )
        ):
            raise TypeError(
                f"{name} must provide y()."
            )

    # --------------------------------------------------------

    def _ensure_active(
        self,
    ) -> None:
        """
        Reject operations after disposal.
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

        return (
            "NavigationController("
            f"zoom={self._zoom_level}, "
            f"panning={self._is_panning}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "NavigationController",
]
