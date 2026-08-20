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
#     the different coordinate spaces used by the SLD editor.
#
# Coordinate Spaces
# -----------------
#
#     VIEWPORT
#         Qt widget coordinates.
#         Origin is associated with the visible viewport.
#
#     SCENE
#         QGraphicsScene coordinates.
#         This is the primary canvas/world coordinate space.
#
#     GRID
#         Scene coordinates resolved against GridSystem geometry.
#
#     ITEM LOCAL
#         Coordinates relative to an equipment/symbol/item.
#
#
#                       VIEWPORT
#                           │
#                           │ mapToScene()
#                           ▼
#                         SCENE
#                           │
#                           │ GridSystem
#                           ▼
#                          GRID
#
#     Equipment / Symbol
#             │
#             ▼
#        ITEM LOCAL
#             │
#             ▼
#           SCENE
#
#
# Detailed Working
# ----------------
#
#     Mouse Event
#          │
#          ▼
#     viewport position
#          │
#          ▼
#     CoordinateSystem
#          │
#          ├──────────────► scene position
#          │
#          └──────────────► grid position
#
#     Tools use this service for coordinate interpretation.
#
#     Canvas navigation modifies the VIEWPORT ↔ SCENE transform
#     through the QGraphicsView.
#
#     CoordinateSystem does not own that navigation state.
#
#
# Responsibilities
# ----------------
#     - viewport → scene conversion;
#     - scene → viewport conversion;
#     - scene → grid resolution;
#     - viewport → grid conversion;
#     - local → scene conversion;
#     - scene → local conversion;
#     - distance calculation;
#     - midpoint calculation;
#     - coordinate formatting;
#     - status-bar coordinate information;
#     - coordinate-system diagnostics.
#
#
# Does NOT
# --------
#     - implement semantic snapping;
#     - select objects;
#     - manage tools;
#     - manage navigation state;
#     - create graphics items;
#     - render symbols;
#     - perform electrical calculations;
#     - perform engineering-unit conversion;
#     - modify the SLD model;
#     - modify Core state.
#
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
#       grid resolution
#
#     SnapSystem
#            │
#            ▼
#       semantic/object snapping
#
# Grid snapping and semantic snapping must remain separate.
#
#
# Qt Boundary
# ----------
#     Direct Qt imports are prohibited.
#
#     All Qt types must pass through:
#
#         ui.core.qt
#
# ============================================================

"""
GridForge V2 — Canvas Coordinate System.

Canonical coordinate conversion service for the SLD canvas.
"""

from __future__ import annotations

from math import hypot
from typing import Any, Optional

from ui.core.qt import QPointF


class CoordinateSystem:
    """
    Canonical coordinate transformation service for the SLD canvas.

    The class deliberately contains no application state and no
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
        if view is None:
            raise ValueError(
                "view must not be None."
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
    def view(self) -> Any:
        """
        Return the QGraphicsView-compatible canvas view.
        """
        return self._view

    @property
    def grid_system(self) -> Optional[Any]:
        """
        Return the currently attached GridSystem.
        """
        return self._grid_system

    @property
    def decimals(self) -> int:
        """
        Number of decimal places used for display formatting.
        """
        return self._decimals

    @property
    def unit(self) -> str:
        """
        Display-only coordinate unit.
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
        transformation boundary.
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

        # Qt mouse events commonly provide QPointF while
        # QGraphicsView.mapToScene() normally accepts QPoint.
        to_point = getattr(
            position,
            "toPoint",
            None,
        )

        if callable(to_point):
            position = to_point()

        result = map_to_scene(position)

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
        Convert scene coordinates into viewport coordinates.
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

        return map_from_scene(scene_pos)

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
        Resolve a scene position against GridSystem.

        This is geometric grid resolution only.

        Semantic/object snapping belongs to SnapSystem.
        """

        self._validate_point(
            scene_pos,
            "scene_pos",
        )

        if self._grid_system is None:
            return QPointF(
                scene_pos.x(),
                scene_pos.y(),
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
            result.x(),
            result.y(),
        )

    # ========================================================
    # GRID → SCENE
    # ========================================================

    def grid_to_scene(
        self,
        grid_pos: Any,
    ) -> QPointF:
        """
        Convert a grid coordinate into scene coordinates.

        GridSystem may provide a specialized conversion in the
        future. At the current architecture level, grid coordinates
        are represented in the same geometric space as scene
        coordinates after resolution.
        """

        self._validate_point(
            grid_pos,
            "grid_pos",
        )

        return QPointF(
            grid_pos.x(),
            grid_pos.y(),
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

        The item is expected to provide mapToScene().
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
            result.x(),
            result.y(),
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

        The item is expected to provide mapFromScene().
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
            result.x(),
            result.y(),
        )

    # ========================================================
    # SEMANTIC POSITION ALIASES
    # ========================================================

    def current_scene_position(
        self,
        viewport_pos: Any,
    ) -> QPointF:
        """
        Return the current scene position represented by a
        viewport position.
        """

        return self.viewport_to_scene(
            viewport_pos
        )

    def current_grid_position(
        self,
        viewport_pos: Any,
    ) -> QPointF:
        """
        Return the current grid-resolved position represented by
        a viewport position.
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
            second.x() - first.x(),
            second.y() - first.y(),
        )

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
                first.x()
                + second.x()
            ) / 2.0,
            (
                first.y()
                + second.y()
            ) / 2.0,
        )

    # ========================================================
    # OFFSET
    # ========================================================

    @staticmethod
    def offset(
        position: Any,
        dx: float,
        dy: float,
    ) -> QPointF:
        """
        Return a new point offset from the supplied position.

        This is pure geometry and does not modify the input.
        """

        CoordinateSystem._validate_point(
            position,
            "position",
        )

        return QPointF(
            position.x() + float(dx),
            position.y() + float(dy),
        )

    # ========================================================
    # FORMATTING
    # ========================================================

    def format_position(
        self,
        position: Any,
    ) -> str:
        """
        Format coordinates for status-bar/UI display.

        Example:

            X: 125.00    Y: 80.00
        """

        self._validate_point(
            position,
            "position",
        )

        x = format(
            position.x(),
            f".{self._decimals}f",
        )

        y = format(
            position.y(),
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
            position.x(),
            f".{self._decimals}f",
        )

        y = format(
            position.y(),
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
        Configure coordinate display precision.
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

    def set_unit(
        self,
        unit: str,
    ) -> None:
        """
        Configure display-only coordinate units.

        No engineering-unit conversion occurs here.
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
        """

        self._grid_system = grid_system

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
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic state without exposing internal
        implementation details.
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
        return (
            "CoordinateSystem("
            f"decimals={self._decimals}, "
            f"unit={self._unit!r}, "
            f"grid_system="
            f"{self._grid_system is not None}"
            ")"
        )


__all__ = [
    "CoordinateSystem",
]
