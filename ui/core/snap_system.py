# ============================================================
# File: ui/core/snap_system.py
# GridForge V2 — Central Snap System
# ============================================================
"""
Centralized spatial snapping service for the GridForge UI.

Architecture
------------

    InteractionManager
           │
           ▼
      SnapSystem
       ┌───┴───────────────┐
       ▼                   ▼
    GridSystem        Spatial queries
       │                   │
       ▼                   ▼
    Grid snap         Object snap
           │
           ▼
      snapped point
           │
           ▼
          Tool

Purpose
-------
SnapSystem is the single UI service responsible for resolving
interaction positions against available snapping targets.

GridForge uses two conceptually different operations:

    1. Grid resolution
       Resolve a point against GridSystem geometry.

    2. Object snapping
       Resolve a point against selectable/spatially relevant
       graphical or canvas objects.

CoordinateSystem provides coordinate conversion.

SnapSystem owns snapping policy.

Tools consume SnapSystem rather than implementing independent
spatial-query logic.

Responsibilities
----------------
SnapSystem:

    - resolve grid snapping;
    - resolve object snapping;
    - combine available snap candidates;
    - apply snap priority;
    - enforce snap tolerance;
    - expose snap configuration;
    - provide deterministic snap results;
    - provide diagnostics.

SnapSystem does NOT:

    - modify Core model state;
    - create model objects;
    - create QGraphicsItems;
    - own tools;
    - manage tool lifecycle;
    - manage selection;
    - perform navigation;
    - perform electrical calculations;
    - perform coordinate conversion from viewport space;
    - decide application-level tool selection.

Coordinate Ownership
--------------------
CoordinateSystem owns:

    viewport → scene
    scene → viewport
    scene → grid coordinate resolution

SnapSystem operates on scene-space coordinates.

Therefore tools should normally perform:

    viewport event
          ↓
    InteractionManager
          ↓
    CoordinateSystem
          ↓
       scene point
          ↓
      SnapSystem
          ↓
      snap result

Grid Ownership
--------------
GridSystem owns grid geometry.

SnapSystem decides whether and how grid snapping participates
in the final snapping decision.

SnapSystem does not duplicate grid geometry or spacing logic.

Object Ownership
----------------
SnapSystem does not own graphical objects.

The optional scene supplied to SnapSystem is a spatial query
source only.

QGraphicsItem state remains owned by the graphics layer.

Qt Architecture
---------------
All Qt dependencies must be imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.

Design Note
-----------
The system intentionally returns a structured SnapResult rather
than only a QPointF.

This allows tools to distinguish:

    - no snap;
    - grid snap;
    - object snap;

and gives future versions room for terminal, connection-point,
bus, line, and other engineering snap targets without changing
the tool-facing contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import hypot
from typing import Any, Optional

from ui.core.qt import QPointF


# ============================================================
# SNAP TYPES
# ============================================================


class SnapType(str, Enum):
    """
    Classification of a resolved snap.
    """

    NONE = "none"
    GRID = "grid"
    OBJECT = "object"


# ============================================================
# SNAP RESULT
# ============================================================


@dataclass(frozen=True)
class SnapResult:
    """
    Immutable result of a snapping operation.

    Attributes
    ----------
    position:
        Final scene-space position.

    snap_type:
        Classification of the selected snap.

    object_id:
        Object identifier when an object snap was selected.

    source:
        Optional spatial source object representing the snap
        target.

    distance:
        Scene-space distance between the original position and
        the selected snap position.

    snapped:
        True when an actual snap target was selected.
    """

    position: QPointF
    snap_type: SnapType = SnapType.NONE
    object_id: Any = None
    source: Any = None
    distance: float = 0.0

    @property
    def is_snapped(self) -> bool:
        """
        Return True when a snap target was selected.
        """

        return self.snapped

    @property
    def snapped(self) -> bool:
        """
        Return True when this result represents a snap.
        """

        return (
            self.snap_type
            is not SnapType.NONE
        )


# ============================================================
# SNAP SYSTEM
# ============================================================


class SnapSystem:
    """
    Central spatial snapping service.

    SnapSystem operates exclusively in scene coordinates.

    It does not perform viewport-to-scene conversion.
    """

    # ========================================================
    # DEFAULT CONFIGURATION
    # ========================================================

    DEFAULT_TOLERANCE = 10.0

    DEFAULT_GRID_ENABLED = True
    DEFAULT_OBJECT_ENABLED = True

    # Object snapping has higher priority than grid snapping.
    DEFAULT_OBJECT_PRIORITY = 100
    DEFAULT_GRID_PRIORITY = 50

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any = None,
        *,
        grid_system: Any = None,
        scene: Any = None,
        tolerance: float = DEFAULT_TOLERANCE,
    ) -> None:
        """
        Initialize the SnapSystem.

        Parameters
        ----------
        controller:
            Optional Controller reference.

            It is retained only as an application context
            reference. SnapSystem does not mutate controller
            state.

        grid_system:
            Optional GridSystem providing grid geometry.

        scene:
            Optional QGraphicsScene used for object snapping.

        tolerance:
            Maximum scene-space distance within which a candidate
            may be selected.
        """

        if tolerance < 0:
            raise ValueError(
                "tolerance must not be negative."
            )

        self.controller = controller
        self.grid_system = grid_system
        self.scene = scene

        self.tolerance = float(
            tolerance
        )

        self.grid_enabled = (
            self.DEFAULT_GRID_ENABLED
        )

        self.object_enabled = (
            self.DEFAULT_OBJECT_ENABLED
        )

        self.object_priority = (
            self.DEFAULT_OBJECT_PRIORITY
        )

        self.grid_priority = (
            self.DEFAULT_GRID_PRIORITY
        )

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def set_tolerance(
        self,
        tolerance: float,
    ) -> None:
        """
        Set the maximum snap distance in scene coordinates.
        """

        if isinstance(
            tolerance,
            bool,
        ) or not isinstance(
            tolerance,
            (int, float),
        ):
            raise TypeError(
                "tolerance must be numeric."
            )

        if tolerance < 0:
            raise ValueError(
                "tolerance must not be negative."
            )

        self.tolerance = float(
            tolerance
        )

    # --------------------------------------------------------

    def set_grid_enabled(
        self,
        enabled: bool,
    ) -> None:
        """
        Enable or disable grid snapping.
        """

        if not isinstance(
            enabled,
            bool,
        ):
            raise TypeError(
                "enabled must be a bool."
            )

        self.grid_enabled = enabled

    # --------------------------------------------------------

    def set_object_enabled(
        self,
        enabled: bool,
    ) -> None:
        """
        Enable or disable object snapping.
        """

        if not isinstance(
            enabled,
            bool,
        ):
            raise TypeError(
                "enabled must be a bool."
            )

        self.object_enabled = enabled

    # ========================================================
    # SERVICES
    # ========================================================

    def set_grid_system(
        self,
        grid_system: Any,
    ) -> None:
        """
        Attach a GridSystem.

        GridSystem remains the owner of grid geometry.
        """

        self.grid_system = grid_system

    # --------------------------------------------------------

    def get_grid_system(
        self,
    ) -> Any:
        """
        Return the attached GridSystem.
        """

        return self.grid_system

    # --------------------------------------------------------

    def set_scene(
        self,
        scene: Any,
    ) -> None:
        """
        Attach the scene used for object spatial queries.

        SnapSystem does not take ownership of the scene.
        """

        self.scene = scene

    # --------------------------------------------------------

    def get_scene(
        self,
    ) -> Any:
        """
        Return the attached scene.
        """

        return self.scene

    # ========================================================
    # MAIN SNAP API
    # ========================================================

    def snap(
        self,
        scene_pos: QPointF,
        *,
        allow_grid: Optional[bool] = None,
        allow_object: Optional[bool] = None,
    ) -> SnapResult:
        """
        Resolve the best snap candidate for a scene position.

        Candidate priority:

            object snap
                ↓
            grid snap
                ↓
            original position

        Priority is considered first, followed by distance.

        Parameters
        ----------
        scene_pos:
            Input scene-space position.

        allow_grid:
            Optional per-request grid override.

        allow_object:
            Optional per-request object-snap override.
        """

        self._validate_point(
            scene_pos,
            "scene_pos",
        )

        use_grid = (
            self.grid_enabled
            if allow_grid is None
            else bool(allow_grid)
        )

        use_object = (
            self.object_enabled
            if allow_object is None
            else bool(allow_object)
        )

        candidates: list[
            tuple[int, float, SnapResult]
        ] = []

        if use_object:
            object_result = (
                self._find_object_snap(
                    scene_pos
                )
            )

            if object_result is not None:
                candidates.append(
                    (
                        self.object_priority,
                        object_result.distance,
                        object_result,
                    )
                )

        if use_grid:
            grid_result = (
                self._find_grid_snap(
                    scene_pos
                )
            )

            if grid_result is not None:
                candidates.append(
                    (
                        self.grid_priority,
                        grid_result.distance,
                        grid_result,
                    )
                )

        if not candidates:
            return SnapResult(
                position=QPointF(
                    scene_pos.x(),
                    scene_pos.y(),
                ),
                snap_type=SnapType.NONE,
                distance=0.0,
            )

        # Higher priority wins.
        #
        # For equal priority, the closest candidate wins.
        candidates.sort(
            key=lambda candidate: (
                -candidate[0],
                candidate[1],
            )
        )

        return candidates[0][2]

    # --------------------------------------------------------

    def snap_point(
        self,
        scene_pos: QPointF,
        **kwargs: Any,
    ) -> QPointF:
        """
        Return only the final snapped scene position.

        This convenience API is useful for tools that do not need
        snap metadata.
        """

        return self.snap(
            scene_pos,
            **kwargs,
        ).position

    # ========================================================
    # GRID SNAP
    # ========================================================

    def _find_grid_snap(
        self,
        scene_pos: QPointF,
    ) -> Optional[SnapResult]:
        """
        Resolve a grid snap candidate.

        GridSystem owns the actual grid geometry.
        """

        if self.grid_system is None:
            return None

        snap_point = getattr(
            self.grid_system,
            "snap_point",
            None,
        )

        if not callable(
            snap_point
        ):
            raise TypeError(
                "grid_system must provide "
                "snap_point()."
            )

        result = snap_point(
            scene_pos
        )

        if result is None:
            return None

        self._validate_point(
            result,
            "grid snap result",
        )

        distance = self._distance(
            scene_pos,
            result,
        )

        if distance > self.tolerance:
            return None

        return SnapResult(
            position=QPointF(
                result.x(),
                result.y(),
            ),
            snap_type=SnapType.GRID,
            distance=distance,
        )

    # ========================================================
    # OBJECT SNAP
    # ========================================================

    def _find_object_snap(
        self,
        scene_pos: QPointF,
    ) -> Optional[SnapResult]:
        """
        Find the nearest supported object snap candidate.

        This method intentionally uses an explicit item contract
        rather than assuming a particular concrete graphics-item
        hierarchy.

        Supported candidate methods are checked in this order:

            snap_points()
            get_snap_points()

        Each method may return QPointF-compatible positions or
        candidate descriptors.

        A candidate descriptor may be:

            QPointF

        or:

            {
                "position": QPointF,
                "object_id": ...,
            }

        Items without a snap-point contract are ignored.
        """

        if self.scene is None:
            return None

        items_method = getattr(
            self.scene,
            "items",
            None,
        )

        if not callable(
            items_method
        ):
            raise TypeError(
                "scene must provide items()."
            )

        best: Optional[
            SnapResult
        ] = None

        for item in tuple(
            items_method()
        ):
            candidates = (
                self._get_item_snap_points(
                    item
                )
            )

            for candidate in candidates:

                position, object_id = (
                    self._normalize_candidate(
                        candidate,
                        item,
                    )
                )

                if position is None:
                    continue

                distance = self._distance(
                    scene_pos,
                    position,
                )

                if distance > self.tolerance:
                    continue

                result = SnapResult(
                    position=QPointF(
                        position.x(),
                        position.y(),
                    ),
                    snap_type=SnapType.OBJECT,
                    object_id=object_id,
                    source=item,
                    distance=distance,
                )

                if (
                    best is None
                    or distance < best.distance
                ):
                    best = result

        return best

    # --------------------------------------------------------

    @staticmethod
    def _get_item_snap_points(
        item: Any,
    ) -> tuple[Any, ...]:
        """
        Obtain snap candidates exposed by a graphics item.
        """

        for method_name in (
            "snap_points",
            "get_snap_points",
        ):
            method = getattr(
                item,
                method_name,
                None,
            )

            if callable(method):
                result = method()

                if result is None:
                    return ()

                return tuple(result)

        return ()

    # --------------------------------------------------------

    @staticmethod
    def _normalize_candidate(
        candidate: Any,
        item: Any,
    ) -> tuple[
        Optional[Any],
        Any,
    ]:
        """
        Normalize an object snap candidate.
        """

        object_id = getattr(
            item,
            "object_id",
            None,
        )

        if isinstance(
            candidate,
            dict,
        ):
            position = candidate.get(
                "position"
            )

            object_id = candidate.get(
                "object_id",
                object_id,
            )

            return (
                position,
                object_id,
            )

        if callable(
            getattr(candidate, "x", None)
        ) and callable(
            getattr(candidate, "y", None)
        ):
            return (
                candidate,
                object_id,
            )

        return (
            None,
            object_id,
        )

    # ========================================================
    # DIRECT OBJECT QUERY
    # ========================================================

    def snap_to_point(
        self,
        scene_pos: QPointF,
        target: QPointF,
        *,
        object_id: Any = None,
        source: Any = None,
    ) -> Optional[SnapResult]:
        """
        Evaluate a single explicit snap target.

        This is useful for tools or higher-level systems that
        already know the relevant target and do not need a scene
        search.
        """

        self._validate_point(
            scene_pos,
            "scene_pos",
        )

        self._validate_point(
            target,
            "target",
        )

        distance = self._distance(
            scene_pos,
            target,
        )

        if distance > self.tolerance:
            return None

        return SnapResult(
            position=QPointF(
                target.x(),
                target.y(),
            ),
            snap_type=SnapType.OBJECT,
            object_id=object_id,
            source=source,
            distance=distance,
        )

    # ========================================================
    # GEOMETRY
    # ========================================================

    @staticmethod
    def _distance(
        first: Any,
        second: Any,
    ) -> float:
        """
        Return Euclidean scene-space distance.
        """

        return hypot(
            second.x() - first.x(),
            second.y() - first.y(),
        )

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
        Return diagnostic snapping state.
        """

        return {
            "tolerance": self.tolerance,
            "grid_enabled": self.grid_enabled,
            "object_enabled": self.object_enabled,
            "grid_system": (
                self.grid_system is not None
            ),
            "scene": (
                self.scene is not None
            ),
            "object_priority": (
                self.object_priority
            ),
            "grid_priority": (
                self.grid_priority
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
            "SnapSystem("
            f"tolerance={self.tolerance}, "
            f"grid_enabled="
            f"{self.grid_enabled}, "
            f"object_enabled="
            f"{self.object_enabled}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "SnapResult",
    "SnapSystem",
    "SnapType",
]
