# ============================================================
# File: ui/canvas/coordinate_system.py
# GridForge V2 — Canvas Coordinate System
# ============================================================
"""
Canonical coordinate conversion service for the GridForge canvas.

Coordinate spaces
-----------------
GridForge canvas interaction uses three coordinate spaces:

    VIEWPORT
        Widget / mouse coordinates supplied by Qt events.

    SCENE
        QGraphicsScene coordinates.

    GRID
        Scene coordinates resolved against GridSystem geometry.

Architecture
------------

    Qt Mouse Position
           │
           ▼
       VIEWPORT
           │
           ▼
    CoordinateSystem
       │         │
       ▼         ▼
     SCENE      GRID
       │         │
       └────┬────┘
            ▼
        Canvas / Tools

Responsibilities
----------------
CoordinateSystem provides:

    - viewport → scene conversion;
    - scene → viewport conversion;
    - viewport → grid conversion;
    - scene → grid resolution;
    - basic geometric utilities;
    - coordinate formatting;
    - status-bar coordinate data.

CoordinateSystem does NOT:

    - implement snapping policy;
    - perform object snapping;
    - own tools;
    - perform selection;
    - own navigation;
    - modify Core state;
    - perform electrical calculations;
    - perform engineering-unit conversion.

Snapping boundary
-----------------
GridSystem may provide geometric grid resolution.

SnapSystem owns actual snapping policy.

Therefore:

    CoordinateSystem
          │
          ▼
      GridSystem

is only a coordinate/grid-resolution relationship.

Tools requiring semantic/object snapping must use SnapSystem.

Qt boundary
-----------
All Qt dependencies must pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from math import hypot
from typing import Any, Optional

from ui.core.qt import QPointF


class CoordinateSystem:
    """
    Canonical canvas coordinate conversion service.

    CoordinateSystem contains no application or domain-model
    state. It delegates viewport transformations to the supplied
    QGraphicsView and optional grid resolution to GridSystem.
    """

    # ========================================================
    # DEFAULT PRESENTATION SETTINGS
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
        Initialize the coordinate service.

        Parameters
        ----------
        view:
            QGraphicsView-compatible canvas viewport.

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
        Convert a viewport position into scene coordinates.

        QGraphicsView.mapToScene() is the authoritative
        transformation boundary.

        QPointF input is converted to QPoint when required by
        the QGraphicsView API.
        """

        if viewport_pos is None:
            raise ValueError(
                "viewport_pos must not be None."
            )

        map_to_scene = getattr(
            self.view,
            "mapToScene",
            None,
        )

        if not callable(
            map_to_scene
        ):
            raise TypeError(
                "view must provide mapToScene()."
            )

        position = viewport_pos

        # ----------------------------------------------------
        # Qt mouse events expose QPointF through position().
        # QGraphicsView.mapToScene() expects a QPoint in the
        # usual Qt 6 interface.
        # ----------------------------------------------------

        to_point = getattr(
            position,
            "toPoint",
            None,
        )

        if callable(
            to_point
        ):
            position = to_point()

        result = map_to_scene(
            position
        )

        self._validate_point(
            result,
            "scene result",
        )

        return QPointF(
            result.x(),
            result.y(),
        )

    # ========================================================
    # SCENE → VIEWPORT
    # ========================================================

    def scene_to_viewport(
        self,
        scene_pos: Any,
    ) -> Any:
        """
        Convert a scene position into viewport coordinates.
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

        if not callable(
            map_from_scene
        ):
            raise TypeError(
                "view must provide mapFromScene()."
            )

        return map_from_scene(
            scene_pos
        )

    # ========================================================
    # SEMANTIC POSITION ALIASES
    # ========================================================

    def current_scene_position(
        self,
        viewport_pos: Any,
    ) -> QPointF:
        """
        Convert the supplied viewport position into scene space.
        """

        return self.viewport_to_scene(
            viewport_pos
        )

    # ========================================================
    # SCENE → GRID
    # ========================================================

    def scene_to_grid(
        self,
        scene_pos: Any,
    ) -> QPointF:
        """
        Resolve scene coordinates against GridSystem geometry.

        This method does not implement semantic snapping policy.

        If no GridSystem is attached, the scene coordinate is
        returned unchanged as a QPointF.
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

        if not callable(
            snap_point
        ):
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
            "grid result",
        )

        return QPointF(
            result.x(),
            result.y(),
        )

    # ========================================================
    # VIEWPORT → GRID
    # ========================================================

    def viewport_to_grid(
        self,
        viewport_pos: Any,
    ) -> QPointF:
        """
        Convert viewport coordinates to grid coordinates.

            VIEWPORT
                ↓
             SCENE
                ↓
              GRID
        """

        scene_pos = (
            self.viewport_to_scene(
                viewport_pos
            )
        )

        return self.scene_to_grid(
            scene_pos
        )

    # --------------------------------------------------------

    def grid_position(
        self,
        viewport_pos: Any,
    ) -> QPointF:
        """
        Semantic alias for viewport_to_grid().
        """

        return self.viewport_to_grid(
            viewport_pos
        )

    # ========================================================
    # GEOMETRY
    # ========================================================

    @staticmethod
    def distance(
        first: Any,
        second: Any,
    ) -> float:
        """
        Return Euclidean distance between two points.

        This is pure canvas geometry.

        No engineering or electrical unit is implied.
        """

        CoordinateSystem._validate_point(
            first,
            "first",
        )

        CoordinateSystem._validate_point(
            second,
            "second",
        )

        return hypot(
            second.x() - first.x(),
            second.y() - first.y(),
        )

    # --------------------------------------------------------

    @staticmethod
    def midpoint(
        first: Any,
        second: Any,
    ) -> QPointF:
        """
        Return the midpoint between two points.
        """

        CoordinateSystem._validate_point(
            first,
            "first",
        )

        CoordinateSystem._validate_point(
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
        position: Any,
    ) -> str:
        """
        Format a coordinate pair for UI display.

        Example:

            X: 125.00    Y: 80.00

        When a display unit exists:

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
        position: Any,
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
    # DISPLAY CONFIGURATION
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

        No coordinate conversion or engineering-unit conversion
        is performed.
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

        Passing None disables grid resolution.
        """

        self.grid_system = grid_system

    # --------------------------------------------------------

    def get_grid_system(
        self,
    ) -> Optional[Any]:
        """
        Return the attached GridSystem.
        """

        return self.grid_system

    # ========================================================
    # STATUS-BAR DATA
    # ========================================================

    def get_status_data(
        self,
        viewport_pos: Any,
    ) -> dict[str, Any]:
        """
        Return coordinate information suitable for StatusBar.
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
        Validate a QPoint/QPointF-compatible object.
        """

        if point is None:
            raise ValueError(
                f"{name} must not be None."
            )

        if not callable(
            getattr(
                point,
                "x",
                None,
            )
        ):
            raise TypeError(
                f"{name} must provide x()."
            )

        if not callable(
            getattr(
                point,
                "y",
                None,
            )
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
            "has_grid_system": (
                self.grid_system is not None
            ),
        }

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
