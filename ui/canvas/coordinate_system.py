# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/canvas/coordinate_system.py
#
# Purpose:
#     Canonical coordinate transformation service for the
#     GridForge V2 Single Line Diagram (SLD) canvas.
#
# Architectural Role:
#     CoordinateSystem is the authoritative boundary between
#     viewport, scene, grid, and item-local coordinate spaces.
#
# Coordinate Spaces
# -----------------
#
#     VIEWPORT
#         Qt widget coordinates.
#
#     SCENE
#         QGraphicsScene coordinates.
#
#     GRID
#         Scene coordinates resolved through GridSystem.
#
#     ITEM LOCAL
#         Coordinates relative to a graphical item.
#
# Responsibilities
# ----------------
#     - viewport → scene conversion;
#     - scene → viewport conversion;
#     - viewport → grid conversion;
#     - scene → grid resolution;
#     - grid → scene conversion;
#     - grid → viewport conversion;
#     - item-local → scene conversion;
#     - scene → item-local conversion;
#     - geometric distance;
#     - midpoint and offset calculations;
#     - coordinate formatting;
#     - status-bar coordinate information;
#     - diagnostic state.
#
# Does NOT
# --------
#     - implement semantic snapping;
#     - manage tools;
#     - manage selection;
#     - manage navigation;
#     - create graphics items;
#     - render graphics;
#     - perform electrical calculations;
#     - modify Core state;
#     - perform engineering-unit conversion.
#
# Snapping Boundary
# -----------------
#
#     CoordinateSystem
#            │
#            ▼
#       GridSystem
#            │
#            ▼
#       geometric grid resolution
#
#     SnapSystem
#            │
#            ▼
#       semantic/object snapping
#
# Grid resolution and semantic snapping remain separate.
#
# Qt Boundary
# -----------
#     All Qt imports pass through:
#
#         ui.core.qt
#
#     No direct PySide6/PyQt imports are permitted.
# ============================================================

"""
GridForge V2 — Canvas Coordinate System.

Canonical coordinate transformation service for the SLD canvas.
"""

from __future__ import annotations

from math import hypot
from typing import Any, Optional

from ui.core.qt import QPointF


class CoordinateSystem:
    """
    Canonical coordinate transformation service for the SLD canvas.

    CoordinateSystem contains no application state and no
    electrical-domain state.

    The supplied QGraphicsView remains authoritative for the
    viewport/scene transformation.
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
            Optional GridSystem-compatible geometric grid service.
        """

        if view is None:
            raise ValueError(
                "view must not be None."
            )

        self._validate_view(
            view
        )

        if grid_system is not None:
            self._validate_grid_system(
                grid_system
            )

        self._view = view
        self._grid_system = grid_system

        self._decimals = (
            self.DEFAULT_DECIMALS
        )

        self._unit = (
            self.DEFAULT_UNIT
        )

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def view(
        self,
    ) -> Any:
        """
        Return the authoritative canvas view.
        """

        return self._view

    @property
    def grid_system(
        self,
    ) -> Optional[Any]:
        """
        Return the currently attached GridSystem.
        """

        return self._grid_system

    @property
    def decimals(
        self,
    ) -> int:
        """
        Return the coordinate display precision.
        """

        return self._decimals

    @property
    def unit(
        self,
    ) -> str:
        """
        Return the display-only coordinate unit.
        """

        return self._unit

    # ========================================================
    # VIEWPORT → SCENE
    # ========================================================

    def viewport_to_scene(
        self,
        viewport_pos: Any,
    ) -> QPointF:
        """
        Convert viewport coordinates into scene coordinates.

        QGraphicsView.mapToScene() remains the authoritative
        viewport-to-scene transformation.

        Qt mouse positions may be QPointF-compatible objects.
        QGraphicsView's integer viewport mapping path is used when
        the supplied point exposes toPoint().
        """

        self._validate_point(
            viewport_pos,
            "viewport_pos",
        )

        map_to_scene = getattr(
            self._view,
            "mapToScene",
            None,
        )

        if not callable(map_to_scene):
            raise TypeError(
                "view must provide mapToScene()."
            )

        position = viewport_pos

        to_point = getattr(
            position,
            "toPoint",
            None,
        )

        if callable(to_point):
            position = to_point()

        result = map_to_scene(
            position
        )

        self._validate_point(
            result,
            "scene result",
        )

        return QPointF(
            float(result.x()),
            float(result.y()),
        )

    # ========================================================
    # SCENE → VIEWPORT
    # ========================================================

    def scene_to_viewport(
        self,
        scene_pos: Any,
    ) -> Any:
        """
        Convert scene coordinates into viewport coordinates.

        QGraphicsView.mapFromScene() remains authoritative.
        """

        self._validate_point(
            scene_pos,
            "scene_pos",
        )

        map_from_scene = getattr(
            self._view,
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
    # VIEWPORT → GRID
    # ========================================================

    def viewport_to_grid(
        self,
        viewport_pos: Any,
    ) -> QPointF:
        """
        Convert:

            VIEWPORT → SCENE → GRID
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
    # SCENE → GRID
    # ========================================================

    def scene_to_grid(
        self,
        scene_pos: Any,
    ) -> QPointF:
        """
        Resolve a scene coordinate against GridSystem.

        This performs geometric grid resolution only.

        Semantic/object snapping remains the responsibility of
        SnapSystem.
        """

        self._validate_point(
            scene_pos,
            "scene_pos",
        )

        if self._grid_system is None:
            return QPointF(
                float(scene_pos.x()),
                float(scene_pos.y()),
            )

        snap_point = getattr(
            self._grid_system,
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
            "grid result",
        )

        return QPointF(
            float(result.x()),
            float(result.y()),
        )

    # ========================================================
    # GRID → SCENE
    # ========================================================

    def grid_to_scene(
        self,
        grid_pos: Any,
    ) -> QPointF:
        """
        Convert a resolved grid coordinate into scene space.

        Grid coordinates currently use scene geometry directly.
        Therefore this conversion is an explicit identity
        transformation at the coordinate boundary.
        """

        self._validate_point(
            grid_pos,
            "grid_pos",
        )

        return QPointF(
            float(grid_pos.x()),
            float(grid_pos.y()),
        )

    # ========================================================
    # GRID → VIEWPORT
    # ========================================================

    def grid_to_viewport(
        self,
        grid_pos: Any,
    ) -> Any:
        """
        Convert:

            GRID → SCENE → VIEWPORT
        """

        scene_pos = self.grid_to_scene(
            grid_pos
        )

        return self.scene_to_viewport(
            scene_pos
        )

    # ========================================================
    # ITEM LOCAL → SCENE
    # ========================================================

    @staticmethod
    def local_to_scene(
        item: Any,
        local_pos: Any,
    ) -> QPointF:
        """
        Convert item-local coordinates into scene coordinates.

        The graphical item remains authoritative for its own
        local-to-scene transformation.
        """

        if item is None:
            raise ValueError(
                "item must not be None."
            )

        CoordinateSystem._validate_point(
            local_pos,
            "local_pos",
        )

        map_to_scene = getattr(
            item,
            "mapToScene",
            None,
        )

        if not callable(map_to_scene):
            raise TypeError(
                "item must provide mapToScene()."
            )

        result = map_to_scene(
            local_pos
        )

        CoordinateSystem._validate_point(
            result,
            "scene result",
        )

        return QPointF(
            float(result.x()),
            float(result.y()),
        )

    # ========================================================
    # SCENE → ITEM LOCAL
    # ========================================================

    @staticmethod
    def scene_to_local(
        item: Any,
        scene_pos: Any,
    ) -> QPointF:
        """
        Convert scene coordinates into item-local coordinates.
        """

        if item is None:
            raise ValueError(
                "item must not be None."
            )

        CoordinateSystem._validate_point(
            scene_pos,
            "scene_pos",
        )

        map_from_scene = getattr(
            item,
            "mapFromScene",
            None,
        )

        if not callable(map_from_scene):
            raise TypeError(
                "item must provide mapFromScene()."
            )

        result = map_from_scene(
            scene_pos
        )

        CoordinateSystem._validate_point(
            result,
            "local result",
        )

        return QPointF(
            float(result.x()),
            float(result.y()),
        )

    # ========================================================
    # CURRENT POSITION HELPERS
    # ========================================================

    def current_scene_position(
        self,
        viewport_pos: Any,
    ) -> QPointF:
        """
        Return the scene position represented by a viewport point.
        """

        return self.viewport_to_scene(
            viewport_pos
        )

    # --------------------------------------------------------

    def current_grid_position(
        self,
        viewport_pos: Any,
    ) -> QPointF:
        """
        Return the grid-resolved position represented by a
        viewport point.
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
            float(second.x())
            - float(first.x()),
            float(second.y())
            - float(first.y()),
        )

    # --------------------------------------------------------

    @staticmethod
    def midpoint(
        first: Any,
        second: Any,
    ) -> QPointF:
        """
        Return the geometric midpoint between two points.
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
                float(first.x())
                + float(second.x())
            ) / 2.0,
            (
                float(first.y())
                + float(second.y())
            ) / 2.0,
        )

    # --------------------------------------------------------

    @staticmethod
    def offset(
        position: Any,
        dx: float,
        dy: float,
    ) -> QPointF:
        """
        Return a new point offset from a supplied position.

        The input point is never modified.
        """

        CoordinateSystem._validate_point(
            position,
            "position",
        )

        CoordinateSystem._validate_numeric(
            dx,
            "dx",
        )

        CoordinateSystem._validate_numeric(
            dy,
            "dy",
        )

        return QPointF(
            float(position.x())
            + float(dx),
            float(position.y())
            + float(dy),
        )

    # ========================================================
    # FORMATTING
    # ========================================================

    def format_position(
        self,
        position: Any,
    ) -> str:
        """
        Format coordinates for status-bar presentation.

        Example:

            X: 125.00    Y: 80.00
        """

        self._validate_point(
            position,
            "position",
        )

        x = format(
            float(position.x()),
            f".{self._decimals}f",
        )

        y = format(
            float(position.y()),
            f".{self._decimals}f",
        )

        suffix = (
            f" {self._unit}"
            if self._unit
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
        Format coordinates compactly.

        Example:

            (125.00, 80.00)
        """

        self._validate_point(
            position,
            "position",
        )

        x = format(
            float(position.x()),
            f".{self._decimals}f",
        )

        y = format(
            float(position.y()),
            f".{self._decimals}f",
        )

        suffix = (
            f" {self._unit}"
            if self._unit
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
        Configure display precision.
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

        self._decimals = decimals

    # --------------------------------------------------------

    def set_unit(
        self,
        unit: str,
    ) -> None:
        """
        Configure the display-only coordinate unit.

        No engineering-unit conversion occurs.
        """

        if not isinstance(
            unit,
            str,
        ):
            raise TypeError(
                "unit must be a string."
            )

        self._unit = unit.strip()

    # ========================================================
    # GRID SYSTEM
    # ========================================================

    def set_grid_system(
        self,
        grid_system: Optional[Any],
    ) -> None:
        """
        Attach or replace the GridSystem.

        None detaches grid resolution.
        """

        if grid_system is not None:
            self._validate_grid_system(
                grid_system
            )

        self._grid_system = grid_system

    # --------------------------------------------------------

    def get_grid_system(
        self,
    ) -> Optional[Any]:
        """
        Return the currently attached GridSystem.
        """

        return self._grid_system

    # ========================================================
    # STATUS BAR
    # ========================================================

    def get_status_data(
        self,
        viewport_pos: Any,
    ) -> dict[str, Any]:
        """
        Produce canonical coordinate information for the
        status-bar subsystem.
        """

        self._validate_point(
            viewport_pos,
            "viewport_pos",
        )

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
    def _validate_view(
        view: Any,
    ) -> None:
        """
        Validate the minimum QGraphicsView-compatible contract.
        """

        if not callable(
            getattr(
                view,
                "mapToScene",
                None,
            )
        ):
            raise TypeError(
                "view must provide mapToScene()."
            )

        if not callable(
            getattr(
                view,
                "mapFromScene",
                None,
            )
        ):
            raise TypeError(
                "view must provide mapFromScene()."
            )

    # --------------------------------------------------------

    @staticmethod
    def _validate_grid_system(
        grid_system: Any,
    ) -> None:
        """
        Validate the minimum GridSystem-compatible contract.
        """

        if not callable(
            getattr(
                grid_system,
                "snap_point",
                None,
            )
        ):
            raise TypeError(
                "grid_system must provide snap_point()."
            )

    # --------------------------------------------------------

    @staticmethod
    def _validate_numeric(
        value: Any,
        name: str,
    ) -> None:
        """
        Validate a scalar numeric value.
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

    # --------------------------------------------------------

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
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic state.
        """

        return {
            "decimals": self._decimals,
            "unit": self._unit,
            "has_grid_system": (
                self._grid_system is not None
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
            f"decimals={self._decimals}, "
            f"unit={self._unit!r}, "
            f"grid_system="
            f"{self._grid_system is not None}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "CoordinateSystem",
]
