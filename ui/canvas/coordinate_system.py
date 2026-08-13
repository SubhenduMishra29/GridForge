# ============================================================
# File: ui/canvas/coordinate_system.py
# GridForge V2 — Canvas Coordinate System
# ============================================================
#
# PURPOSE
# -------
# Centralized coordinate conversion and presentation service
# for the GridForge canvas.
#
# Coordinate spaces:
#
#     VIEWPORT
#         Widget / mouse coordinates.
#
#     SCENE
#         QGraphicsScene coordinates.
#
#     GRID
#         Scene coordinates resolved against GridSystem
#         geometry.
#
#
# ARCHITECTURE
# ------------
#
#     Mouse / Widget
#           │
#           ▼
#       VIEWPORT
#           │
#           ▼
#     CoordinateSystem
#           │
#        ┌──┴──┐
#        ▼     ▼
#      SCENE  GRID
#        │     │
#        └──┬──┘
#           ▼
#        UI / Tools
#
#
# RESPONSIBILITIES
# ----------------
#
# CoordinateSystem:
#
#     - viewport → scene conversion
#     - scene → viewport conversion
#     - scene → grid resolution
#     - viewport → grid conversion
#     - geometric utilities
#     - coordinate formatting
#     - status-bar coordinate data
#
#
# CoordinateSystem does NOT:
#
#     - modify the Core model
#     - perform electrical calculations
#     - create QGraphicsItems
#     - manage tools
#     - perform selection
#     - own navigation state
#     - decide snapping priority
#     - perform object snapping
#     - perform engineering-unit conversion
#
#
# SNAP ARCHITECTURE
# -----------------
#
# GridSystem provides grid geometry.
#
# SnapSystem owns snapping policy.
#
# Therefore:
#
#     CoordinateSystem
#          │
#          ▼
#     GridSystem.snap_point()
#
# is only a coordinate/grid-resolution operation.
#
# Tools requiring actual snapping policy must use SnapSystem.
#
#
# UNIT HANDLING
# -------------
#
# ``unit`` is display metadata only.
#
# No unit conversion is performed here.
#
#
# QT RULE
# -------
#
# All Qt dependencies must be imported through:
#
#     ui.core.qt
#
# No direct PySide6/PyQt imports are permitted.
#
# ============================================================

from __future__ import annotations

from math import hypot
from typing import Any, Optional

from ui.core.qt import QPointF


class CoordinateSystem:
    """
    Central coordinate conversion and presentation service.

    The class contains no domain-model state and does not own
    navigation or interaction state.
    """

    # ========================================================
    # DEFAULT DISPLAY SETTINGS
    # ========================================================

    DEFAULT_DECIMALS = 2
    DEFAULT_UNIT = ""

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        view: Any,
        grid_system: Optional[Any] = None,
    ) -> None:
        """
        Initialize the coordinate system.

        Parameters
        ----------
        view:
            Graphics view used for viewport/scene conversion.

        grid_system:
            Optional GridSystem used for grid-coordinate
            resolution.
        """

        if view is None:
            raise ValueError(
                "view must not be None."
            )

        self.view = view
        self.grid_system = grid_system

        self.decimals = (
            self.DEFAULT_DECIMALS
        )

        self.unit = (
            self.DEFAULT_UNIT
        )

    # ========================================================
    # VIEWPORT → SCENE
    # ========================================================

    def viewport_to_scene(
        self,
        viewport_pos: Any,
    ) -> QPointF:
        """
        Convert viewport coordinates to scene coordinates.

        ``QPointF`` is accepted for convenience and converted
        to ``QPoint`` because QGraphicsView.mapToScene() uses
        integer viewport coordinates.
        """

        if viewport_pos is None:
            raise ValueError(
                "viewport_pos must not be None."
            )

        if hasattr(
            viewport_pos,
            "toPoint",
        ):
            viewport_pos = (
                viewport_pos.toPoint()
            )

        map_to_scene = getattr(
            self.view,
            "mapToScene",
            None,
        )

        if not callable(map_to_scene):
            raise TypeError(
                "view must provide mapToScene()."
            )

        return map_to_scene(
            viewport_pos
        )

    # ========================================================
    # SCENE → VIEWPORT
    # ========================================================

    def scene_to_viewport(
        self,
        scene_pos: QPointF,
    ) -> Any:
        """
        Convert scene coordinates to viewport coordinates.
        """

        self._validate_point(
            scene_pos,
            "scene_pos",
        )

        map_from_scene = getattr(
            self.view,
            "mapFromScene",
            None,
        )

        if not callable(map_from_scene):
            raise TypeError(
                "view must provide mapFromScene()."
            )

        return map_from_scene(
            scene_pos
        )

    # ========================================================
    # CURRENT SCENE POSITION
    # ========================================================

    def current_scene_position(
        self,
        viewport_pos: Any,
    ) -> QPointF:
        """
        Semantic alias for viewport_to_scene().
        """

        return self.viewport_to_scene(
            viewport_pos
        )

    # ========================================================
    # SCENE → GRID
    # ========================================================

    def scene_to_grid(
        self,
        scene_pos: QPointF,
    ) -> QPointF:
        """
        Resolve a scene position against the configured
        GridSystem.

        This is a coordinate-resolution operation only.

        CoordinateSystem does not decide whether grid snapping
        should occur. SnapSystem owns that policy.
        """

        self._validate_point(
            scene_pos,
            "scene_pos",
        )

        if self.grid_system is None:
            return QPointF(
                scene_pos.x(),
                scene_pos.y(),
            )

        snap_point = getattr(
            self.grid_system,
            "snap_point",
            None,
        )

        if not callable(snap_point):
            raise TypeError(
                "grid_system must provide snap_point()."
            )

        result = snap_point(
            scene_pos
        )

        if result is None:
            raise RuntimeError(
                "GridSystem.snap_point() returned None."
            )

        self._validate_point(
            result,
            "grid_system result",
        )

        return QPointF(
            result.x(),
            result.y(),
        )

    # ========================================================
    # VIEWPORT → GRID
    # ========================================================

    def grid_position(
        self,
        viewport_pos: Any,
    ) -> QPointF:
        """
        Convert viewport coordinates to grid coordinates.

        Processing:

            viewport
                ↓
             scene
                ↓
              grid
        """

        scene_pos = (
            self.viewport_to_scene(
                viewport_pos
            )
        )

        return self.scene_to_grid(
            scene_pos
        )

    # ========================================================
    # GEOMETRY
    # ========================================================

    def distance(
        self,
        first: QPointF,
        second: QPointF,
    ) -> float:
        """
        Return Euclidean distance between two scene points.

        This is purely geometric and has no electrical or
        engineering-unit meaning.
        """

        self._validate_point(
            first,
            "first",
        )

        self._validate_point(
            second,
            "second",
        )

        return hypot(
            second.x() - first.x(),
            second.y() - first.y(),
        )

    # --------------------------------------------------------

    def midpoint(
        self,
        first: QPointF,
        second: QPointF,
    ) -> QPointF:
        """
        Return the midpoint between two scene points.
        """

        self._validate_point(
            first,
            "first",
        )

        self._validate_point(
            second,
            "second",
        )

        return QPointF(
            (
                first.x()
                + second.x()
            ) / 2.0,
            (
                first.y()
                + second.y()
            ) / 2.0,
        )

    # ========================================================
    # FORMATTING
    # ========================================================

    def format_position(
        self,
        position: QPointF,
    ) -> str:
        """
        Format a coordinate pair for UI display.

        Example:

            X: 125.00    Y: 80.00

        If a display unit is configured:

            X: 125.00 m    Y: 80.00 m
        """

        self._validate_point(
            position,
            "position",
        )

        x = format(
            position.x(),
            f".{self.decimals}f",
        )

        y = format(
            position.y(),
            f".{self.decimals}f",
        )

        suffix = (
            f" {self.unit}"
            if self.unit
            else ""
        )

        return (
            f"X: {x}{suffix}"
            f"    "
            f"Y: {y}{suffix}"
        )

    # --------------------------------------------------------

    def format_point(
        self,
        position: QPointF,
    ) -> str:
        """
        Format a coordinate pair compactly.

        Example:

            (125.00, 80.00)
        """

        self._validate_point(
            position,
            "position",
        )

        x = format(
            position.x(),
            f".{self.decimals}f",
        )

        y = format(
            position.y(),
            f".{self.decimals}f",
        )

        suffix = (
            f" {self.unit}"
            if self.unit
            else ""
        )

        return (
            f"({x}, {y})"
            f"{suffix}"
        )

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def set_decimals(
        self,
        decimals: int,
    ) -> None:
        """
        Set the number of decimal places used for display.
        """

        if isinstance(
            decimals,
            bool,
        ) or not isinstance(
            decimals,
            int,
        ):
            raise TypeError(
                "decimals must be a non-negative integer."
            )

        if decimals < 0:
            raise ValueError(
                "decimals cannot be negative."
            )

        self.decimals = decimals

    # --------------------------------------------------------

    def set_unit(
        self,
        unit: str,
    ) -> None:
        """
        Set display-unit metadata.

        No unit conversion is performed.
        """

        if not isinstance(
            unit,
            str,
        ):
            raise TypeError(
                "unit must be a string."
            )

        self.unit = unit.strip()

    # ========================================================
    # GRID SYSTEM
    # ========================================================

    def set_grid_system(
        self,
        grid_system: Optional[Any],
    ) -> None:
        """
        Attach or replace the GridSystem.

        Passing None disables grid-coordinate resolution.
        """

        self.grid_system = grid_system

    # --------------------------------------------------------

    def get_grid_system(
        self,
    ) -> Optional[Any]:
        """
        Return the currently attached GridSystem.
        """

        return self.grid_system

    # ========================================================
    # STATUS BAR DATA
    # ========================================================

    def get_status_data(
        self,
        viewport_pos: Any,
    ) -> dict[str, Any]:
        """
        Return coordinate data suitable for the StatusBar.

        Both raw coordinates and formatted representations are
        provided.
        """

        scene_pos = (
            self.viewport_to_scene(
                viewport_pos
            )
        )

        grid_pos = (
            self.scene_to_grid(
                scene_pos
            )
        )

        return {
            "viewport": viewport_pos,
            "scene": scene_pos,
            "grid": grid_pos,
            "scene_text": (
                self.format_position(
                    scene_pos
                )
            ),
            "grid_text": (
                self.format_position(
                    grid_pos
                )
            ),
        }

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_point(
        point: Any,
        name: str,
    ) -> None:
        """
        Validate a QPointF-compatible object.
        """

        if point is None:
            raise ValueError(
                f"{name} must not be None."
            )

        if not callable(
            getattr(point, "x", None)
        ):
            raise TypeError(
                f"{name} must provide x()."
            )

        if not callable(
            getattr(point, "y", None)
        ):
            raise TypeError(
                f"{name} must provide y()."
            )

    # ========================================================
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic coordinate-system state.
        """

        return {
            "decimals": self.decimals,
            "unit": self.unit,
            "grid_system": (
                self.grid_system is not None
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
            "CoordinateSystem("
            f"decimals={self.decimals}, "
            f"unit={self.unit!r}, "
            f"grid_system="
            f"{self.grid_system is not None}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "CoordinateSystem",
]
