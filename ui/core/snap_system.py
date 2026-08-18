# ============================================================
# File: ui/core/snap_system.py
# GridForge V2 — Central Snap System
# ============================================================
"""
Centralized spatial snapping service for the GridForge UI.

Coordinate contract
-------------------
SnapSystem operates exclusively in SCENE coordinates.

    VIEWPORT
        │
        ▼
    CoordinateSystem
        │
        ▼
      SCENE
        │
        ▼
    SnapSystem
        │
        ├── GridSystem
        │
        └── scene snap candidates
        │
        ▼
    SnapResult
        │
        ▼
       Tool

Responsibilities
----------------
SnapSystem:

    - resolves grid snap candidates;
    - resolves object snap candidates;
    - applies snap tolerance;
    - applies snap priority;
    - selects a deterministic winning candidate;
    - exposes snap configuration;
    - provides diagnostic state.

SnapSystem does NOT:

    - convert viewport coordinates;
    - own CoordinateSystem;
    - own GridSystem;
    - own QGraphicsScene;
    - create graphics items;
    - own tools;
    - manage selection;
    - perform navigation;
    - modify Core state;
    - perform electrical calculations.

Ownership
---------
SnapSystem is a service owned by the UI composition layer.

The supplied GridSystem and scene are references only.

Qt boundary
-----------
All Qt dependencies must be imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.

Object snap contract
--------------------
A scene item may expose object snap points through either:

    snap_points()
    get_snap_points()

Each returned candidate must be either:

    QPointF-compatible

or:

    {
        "position": QPointF-compatible,
        "object_id": optional identifier,
    }

The returned position is required to already be in SCENE
coordinates.

Snap priority
-------------
Higher priority wins.

When priorities are equal:

    1. smaller distance wins;
    2. earlier candidate order wins.

This makes resolution deterministic without imposing an
ordering policy on graphical items.
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

    Parameters
    ----------
    position:
        Final scene-space position.

    snap_type:
        Type of snap selected.

    object_id:
        Identifier associated with an object snap, if available.

    source:
        Source object associated with an object snap, if available.

    distance:
        Scene-space distance between the requested position and
        the selected snap position.
    """

    position: QPointF
    snap_type: SnapType = SnapType.NONE
    object_id: Any = None
    source: Any = None
    distance: float = 0.0

    @property
    def snapped(self) -> bool:
        """
        Return True when an actual snap target was selected.
        """

        return self.snap_type is not SnapType.NONE

    @property
    def is_snapped(self) -> bool:
        """
        Compatibility alias for snapped.
        """

        return self.snapped


# ============================================================
# SNAP SYSTEM
# ============================================================


class SnapSystem:
    """
    Central scene-space snapping service.

    SnapSystem has no dependency on application navigation,
    interaction state, or Core-domain objects.
    """

    # ========================================================
    # DEFAULT CONFIGURATION
    # ========================================================

    DEFAULT_TOLERANCE = 10.0

    DEFAULT_GRID_ENABLED = True
    DEFAULT_OBJECT_ENABLED = True

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

        ``controller`` is retained only for compatibility with
        existing UI composition code. SnapSystem does not use it
        for snapping decisions and never mutates it.
        """

        self._validate_tolerance(
            tolerance
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

        self._disposed = False

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def set_tolerance(
        self,
        tolerance: float,
    ) -> None:
        """
        Set the maximum scene-space snap distance.
        """

        self._validate_tolerance(
            tolerance
        )

        self._ensure_active()

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

        self._validate_bool(
            enabled,
            "enabled",
        )

        self._ensure_active()

        self.grid_enabled = enabled

    # --------------------------------------------------------

    def set_object_enabled(
        self,
        enabled: bool,
    ) -> None:
        """
        Enable or disable object snapping.
        """

        self._validate_bool(
            enabled,
            "enabled",
        )

        self._ensure_active()

        self.object_enabled = enabled

    # --------------------------------------------------------

    def set_priorities(
        self,
        *,
        object_priority: int,
        grid_priority: int,
    ) -> None:
        """
        Configure relative snap priorities.

        Higher values win.
        """

        self._validate_priority(
            object_priority,
            "object_priority",
        )

        self._validate_priority(
            grid_priority,
            "grid_priority",
        )

        self._ensure_active()

        self.object_priority = (
            object_priority
        )

        self.grid_priority = (
            grid_priority
        )

    # ========================================================
    # GRID / SCENE REFERENCES
    # ========================================================

    def set_grid_system(
        self,
        grid_system: Any,
    ) -> None:
        """
        Attach or replace the GridSystem reference.

        Passing None disables grid snapping unless another
        grid source is subsequently attached.
        """

        self._ensure_active()

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
        Attach or replace the scene used for object queries.

        SnapSystem does not take ownership of the scene.
        """

        self._ensure_active()

        self.scene = scene

    # --------------------------------------------------------

    def get_scene(
        self,
    ) -> Any:
        """
        Return the configured scene.
        """

        return self.scene

    # ========================================================
    # MAIN SNAP API
    # ========================================================

    def snap(
        self,
        scene_pos: Any,
        *,
        allow_grid: Optional[bool] = None,
        allow_object: Optional[bool] = None,
    ) -> SnapResult:
        """
        Resolve the best snap candidate for a scene position.

        Resolution order is governed by priority rather than by
        hard-coded candidate type ordering.

        Equal-priority candidates are resolved by distance and
        then by discovery order.
        """

        self._ensure_active()

        self._validate_point(
            scene_pos,
            "scene_pos",
        )

        use_grid = self._resolve_bool_override(
            allow_grid,
            self.grid_enabled,
            "allow_grid",
        )

        use_object = self._resolve_bool_override(
            allow_object,
            self.object_enabled,
            "allow_object",
        )

        candidates: list[
            tuple[int, float, int, SnapResult]
        ] = []

        order = 0

        if use_object:
            result = self._find_object_snap(
                scene_pos
            )

            if result is not None:
                candidates.append(
                    (
                        self.object_priority,
                        result.distance,
                        order,
                        result,
                    )
                )

                order += 1

        if use_grid:
            result = self._find_grid_snap(
                scene_pos
            )

            if result is not None:
                candidates.append(
                    (
                        self.grid_priority,
                        result.distance,
                        order,
                        result,
                    )
                )

        if not candidates:
            return self._none_result(
                scene_pos
            )

        candidates.sort(
            key=lambda candidate: (
                -candidate[0],
                candidate[1],
                candidate[2],
            )
        )

        return candidates[0][3]

    # --------------------------------------------------------

    def snap_point(
        self,
        scene_pos: Any,
        **kwargs: Any,
    ) -> QPointF:
        """
        Return only the resolved scene-space position.
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
        scene_pos: Any,
    ) -> Optional[SnapResult]:
        """
        Resolve the GridSystem candidate.
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
                "grid_system must provide snap_point()."
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
        scene_pos: Any,
    ) -> Optional[SnapResult]:
        """
        Find the nearest valid object snap candidate.

        Items without the explicit snap-point contract are ignored.
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
        Obtain snap candidates from one graphics item.

        The first supported contract is authoritative.
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

            if not callable(
                method
            ):
                continue

            result = method()

            if result is None:
                return ()

            try:
                return tuple(result)
            except TypeError as exc:
                raise TypeError(
                    f"{method_name}() must return an iterable."
                ) from exc

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
        Normalize one object snap candidate.

        Candidate coordinates are assumed to already be in
        scene coordinates.
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
            if "position" not in candidate:
                return (
                    None,
                    object_id,
                )

            position = candidate.get(
                "position"
            )

            object_id = candidate.get(
                "object_id",
                object_id,
            )

        else:
            position = candidate

        if position is None:
            return (
                None,
                object_id,
            )

        if not (
            callable(
                getattr(
                    position,
                    "x",
                    None,
                )
            )
            and callable(
                getattr(
                    position,
                    "y",
                    None,
                )
            )
        ):
            return (
                None,
                object_id,
            )

        return (
            position,
            object_id,
        )

    # ========================================================
    # DIRECT OBJECT QUERY
    # ========================================================

    def snap_to_point(
        self,
        scene_pos: Any,
        target: Any,
        *,
        object_id: Any = None,
        source: Any = None,
    ) -> Optional[SnapResult]:
        """
        Evaluate one explicit object snap target.

        The operation is subject to the configured object-snap
        enable flag and tolerance.
        """

        self._ensure_active()

        self._validate_point(
            scene_pos,
            "scene_pos",
        )

        self._validate_point(
            target,
            "target",
        )

        if not self.object_enabled:
            return None

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
        Return Euclidean distance in scene coordinates.
        """

        return hypot(
            second.x() - first.x(),
            second.y() - first.y(),
        )

    # ========================================================
    # RESULT HELPERS
    # ========================================================

    @staticmethod
    def _none_result(
        scene_pos: Any,
    ) -> SnapResult:
        """
        Construct a non-snapped result.
        """

        return SnapResult(
            position=QPointF(
                scene_pos.x(),
                scene_pos.y(),
            ),
            snap_type=SnapType.NONE,
            distance=0.0,
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

    # --------------------------------------------------------

    @staticmethod
    def _validate_tolerance(
        tolerance: float,
    ) -> None:
        """
        Validate snap tolerance.
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

        if tolerance < 0.0:
            raise ValueError(
                "tolerance must not be negative."
            )

    # --------------------------------------------------------

    @staticmethod
    def _validate_bool(
        value: bool,
        name: str,
    ) -> None:
        """
        Validate a strict boolean.
        """

        if not isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be a bool."
            )

    # --------------------------------------------------------

    @staticmethod
    def _resolve_bool_override(
        override: Optional[bool],
        default: bool,
        name: str,
    ) -> bool:
        """
        Resolve an optional strict boolean override.
        """

        if override is None:
            return default

        SnapSystem._validate_bool(
            override,
            name,
        )

        return override

    # --------------------------------------------------------

    @staticmethod
    def _validate_priority(
        value: int,
        name: str,
    ) -> None:
        """
        Validate a priority value.
        """

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            int,
        ):
            raise TypeError(
                f"{name} must be an integer."
            )

    # --------------------------------------------------------

    def _ensure_active(
        self,
    ) -> None:
        """
        Reject service operations after disposal.
        """

        if self._disposed:
            raise RuntimeError(
                "SnapSystem has been disposed."
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
            "disposed": self._disposed,
        }

    # ========================================================
    # CLEANUP
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Release transient service references.

        The GridSystem and scene themselves are not owned and are
        therefore not disposed.
        """

        if self._disposed:
            return

        self.grid_system = None
        self.scene = None

        self._disposed = True

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
            f"grid_enabled={self.grid_enabled}, "
            f"object_enabled={self.object_enabled}, "
            f"disposed={self._disposed}"
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
