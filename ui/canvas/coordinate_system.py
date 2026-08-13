"""
GridForge V2 — Canvas Coordinate System
=======================================

File:
    ui/canvas/coordinate_system.py

Purpose
-------
Centralized coordinate conversion and presentation service for
the GridForge canvas.

Coordinate spaces
-----------------
GridForge uses three canvas coordinate representations:

    1. VIEWPORT
       Widget / mouse coordinates.

    2. SCENE
       QGraphicsScene coordinates.

    3. GRID
       Scene coordinates resolved against GridSystem snapping.

The CoordinateSystem is the single UI service responsible for
converting between these representations.

Architecture
------------

    Mouse / Widget
          │
          ▼
      VIEWPORT
          │
          ▼
    CoordinateSystem
          │
       ┌──┴──┐
       ▼     ▼
     SCENE  GRID
       │     │
       └──┬──┘
          ▼
       UI / Tools

Responsibilities
----------------
CoordinateSystem:

    - converts viewport coordinates to scene coordinates;
    - converts scene coordinates to viewport coordinates;
    - resolves scene coordinates against GridSystem;
    - provides geometric utilities;
    - formats coordinates for UI display;
    - provides status-bar coordinate data.

CoordinateSystem does NOT:

    - modify the Core model;
    - perform electrical calculations;
    - create QGraphicsItems;
    - manage tools;
    - perform selection;
    - own navigation state;
    - perform engineering-unit conversion.

Unit handling
-------------
The optional `unit` attribute is display metadata only.

This class does not perform:

    mm ↔ m
    pixel ↔ engineering distance
    drawing-unit ↔ physical-unit

conversion.

Those responsibilities belong to a future engineering/unit
system.

Qt Rule
-------
All Qt dependencies must be imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from math import hypot
from typing import Any, Optional

from ui.core.qt import QPointF


class CoordinateSystem:
    """
    Central coordinate conversion and formatting service.

    The class intentionally contains no domain-model state.
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
            GridForge QGraphicsView used for viewport/scene
            transformations.

        grid_system:
            Optional GridSystem used for scene-to-grid snapping.
        """

        if view is None:
            raise ValueError(
                "view must not be None"
            )

        self.view = view
        self.grid_system = grid_system

        self.decimals = self.DEFAULT_DECIMALS
        self.unit = self.DEFAULT_UNIT

    # ========================================================
    # VIEWPORT → SCENE
    # ========================================================

    def viewport_to_scene(
        self,
        viewport_pos: Any,
    ) -> QPointF:
        """
        Convert viewport coordinates to scene coordinates.

        Parameters
        ----------
        viewport_pos:
            Qt viewport coordinate, normally QPoint.

            QPointF is also accepted and converted to QPoint
            because QGraphicsView.mapToScene() uses integer
            viewport coordinates.

        Returns
        -------
        QPointF
            Scene-space coordinate.
        """

        if viewport_pos is None:
            raise ValueError(
                "viewport_pos must not be None"
            )

        if hasattr(
            viewport_pos,
            "toPoint",
        ):
            viewport_pos = (
                viewport_pos.toPoint()
            )

        return self.view.mapToScene(
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

        Returns
        -------
        QPoint
            Viewport coordinate suitable for QGraphicsView
            and QWidget operations.
        """

        self._validate_point(
            scene_pos,
            "scene_pos",
        )

        return self.view.mapFromScene(
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
        Convert a viewport position to scene coordinates.

        This is an explicit semantic alias for
        viewport_to_scene().
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
        Resolve a scene coordinate against the GridSystem.

        If no GridSystem is attached, a copy of the original
        scene coordinate is returned.

        GridSystem is responsible for the actual snapping policy.
        CoordinateSystem only provides the coordinate-space
        boundary.
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
                "grid_system must provide "
                "snap_point()"
            )

        result = snap_point(
            scene_pos
        )

        if result is None:
            raise RuntimeError(
                "GridSystem.snap_point() returned None"
            )

        return result

    # ========================================================
    # VIEWPORT → GRID
    # ========================================================

    def grid_position(
        self,
        viewport_pos: Any,
    ) -> QPointF:
        """
        Convert viewport coordinates directly to grid
        coordinates.

        Processing:

            viewport
                ↓
            scene
                ↓
             grid
        """

        scene_pos = self.viewport_to_scene(
            viewport_pos
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

        This is purely geometric.

        No physical/electrical unit is implied.
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

        The configured unit is appended when non-empty.
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

        Parameters
        ----------
        decimals:
            Non-negative integer.
        """

        if isinstance(
            decimals,
            bool,
        ) or not isinstance(
            decimals,
            int,
        ):
            raise TypeError(
                "decimals must be a non-negative integer"
            )

        if decimals < 0:
            raise ValueError(
                "decimals cannot be negative"
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
                "unit must be a string"
            )

        self.unit = unit.strip()

    # ========================================================
    # STATUS BAR DATA
    # ========================================================

    def get_status_data(
        self,
        viewport_pos: Any,
    ) -> dict[str, Any]:
        """
        Return coordinate information suitable for StatusBar.

        The result contains both raw coordinates and formatted
        display strings.
        """

        scene_pos = self.viewport_to_scene(
            viewport_pos
        )

        grid_pos = self.scene_to_grid(
            scene_pos
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
    # GRID SYSTEM
    # ========================================================

    def set_grid_system(
        self,
        grid_system: Optional[Any],
    ) -> None:
        """
        Attach or replace the GridSystem.

        Passing None disables grid resolution while preserving
        the scene coordinate system.
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
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_point(
        point: Any,
        name: str,
    ) -> None:
        """
        Validate that an object provides QPointF-compatible
        x() and y() accessors.
        """

        if point is None:
            raise ValueError(
                f"{name} must not be None"
            )

        if not callable(
            getattr(point, "x", None)
        ) or not callable(
            getattr(point, "y", None)
        ):
            raise TypeError(
                f"{name} must provide x() and y()"
            )

    # ========================================================
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return current coordinate-system configuration.
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
