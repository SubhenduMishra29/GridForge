# ============================================================
# File: ui/canvas/coordinate_system.py
# GridForge V2 — Canvas Coordinate System
# ============================================================
"""
Centralized coordinate conversion and presentation service
for the GridForge canvas.

Coordinate spaces
-----------------
GridForge uses three UI coordinate representations:

    VIEWPORT
        Widget / mouse coordinates.

    SCENE
        QGraphicsScene coordinates.

    GRID
        Scene coordinates resolved through GridSystem geometry.

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

    - viewport → scene conversion;
    - scene → viewport conversion;
    - scene → grid resolution;
    - viewport → grid resolution;
    - geometric utilities;
    - coordinate formatting;
    - status-bar coordinate data.

CoordinateSystem does NOT:

    - modify the Core model;
    - perform electrical calculations;
    - create QGraphicsItems;
    - manage tools;
    - perform selection;
    - own navigation state;
    - decide snapping priority;
    - perform object snapping;
    - perform engineering-unit conversion.

Snapping architecture
---------------------
GridSystem owns grid geometry/resolution.

SnapSystem owns snapping policy and target priority.

Therefore:

    CoordinateSystem
         │
         ▼
    GridSystem.snap_point()

is only a grid-resolution operation.

Tools requiring actual snapping policy must use SnapSystem.

Unit handling
-------------
``unit`` is display metadata only.

No engineering-unit conversion is performed here.

Qt rule
-------
All Qt dependencies are imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from math import hypot
from typing import Any, Optional

from ui.core.qt import QPointF


class CoordinateSystem:
    """
    Canonical UI coordinate conversion and presentation service.

    The class contains no domain-model state and does not own
    navigation, interaction, selection, or snapping policy.
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
            GraphicsView used for viewport/scene conversion.

        grid_system:
            Optional GridSystem used for grid resolution.

        Notes
        -----
        CoordinateSystem does not own the GridSystem. It only
        keeps a reference to the service used for coordinate
        resolution.
        """

        if view is None:
            raise ValueError(
                "view must not be None."
            )

        if not callable(
            getattr(view, "mapToScene", None)
        ):
            raise TypeError(
                "view must provide mapToScene()."
            )

        if not callable(
            getattr(view, "mapFromScene", None)
        ):
            raise TypeError(
                "view must provide mapFromScene()."
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
        Convert a viewport coordinate to scene coordinates.

        Parameters
        ----------
        viewport_pos:
            QPoint-compatible viewport position.

        Returns
        -------
        QPointF
            Independent scene-space coordinate.

        Notes
        -----
        QGraphicsView is the authoritative owner of the
        viewport-to-scene transformation.

        Qt's standard mouse-position path provides a QPointF.
        QGraphicsView.mapToScene() accepts the integer viewport
        position in the PySide6 API, so QPointF is explicitly
        converted to QPoint where required.
        """

        if viewport_pos is None:
            raise ValueError(
                "viewport_pos must not be None."
            )

        position = viewport_pos

        to_point = getattr(
            position,
            "toPoint",
            None,
        )

        if callable(to_point):
            position = to_point()

        result = self.view.mapToScene(
            position
        )

        self._validate_point(
            result,
            "scene result",
        )

        # Return an independent QPointF rather than exposing
        # a Qt object owned by another subsystem.
        return QPointF(
            float(result.x()),
            float(result.y()),
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

        QGraphicsView remains the authoritative transformation
        boundary.
        """

        self._validate_point(
            scene_pos,
            "scene_pos",
        )

        result = self.view.mapFromScene(
            scene_pos
        )

        return result

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
        Resolve a scene coordinate through GridSystem.

        This method performs grid-coordinate resolution only.

        It does NOT:

            - decide whether snapping should occur;
            - check Bus proximity;
            - choose between Bus/Grid/None;
            - apply SnapSystem priority.

        SnapSystem owns snapping policy.
        """

        self._validate_point(
            scene_pos,
            "scene_pos",
        )

        if self.grid_system is None:
            return QPointF(
                float(scene_pos.x()),
                float(scene_pos.y()),
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
            float(result.x()),
            float(result.y()),
        )

    # ========================================================
    # VIEWPORT → GRID
    # ========================================================

    def grid_position(
        self,
        viewport_pos: Any,
    ) -> QPointF:
        """
        Convert viewport coordinates to grid-resolved
        scene coordinates.

        Processing:

            VIEWPORT
                ↓
             SCENE
                ↓
              GRID
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

        No physical or electrical unit is implied.
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
            float(second.x()) - float(first.x()),
            float(second.y()) - float(first.y()),
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
                float(first.x())
                + float(second.x())
            ) / 2.0,
            (
                float(first.y())
                + float(second.y())
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

        With display metadata:

            X: 125.00 m    Y: 80.00 m

        ``unit`` is presentation metadata only.
        """

        self._validate_point(
            position,
            "position",
        )

        x = format(
            float(position.x()),
            f".{self.decimals}f",
        )

        y = format(
            float(position.y()),
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

        With display metadata:

            (125.00, 80.00) m
        """

        self._validate_point(
            position,
            "position",
        )

        x = format(
            float(position.x()),
            f".{self.decimals}f",
        )

        y = format(
            float(position.y()),
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

        No engineering-unit conversion is performed.
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
        Return coordinate data suitable for StatusBar.

        The returned values distinguish:

            viewport
            scene
            grid-resolved scene position

        No snapping policy is applied here.
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
            "scene_text": self.format_position(
                scene_pos
            ),
            "grid_text": self.format_position(
                grid_pos
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
