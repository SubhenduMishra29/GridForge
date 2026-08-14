# ============================================================
# File: ui/core/snap_system.py
# GridForge V2 — Snap System
# ============================================================
"""
Centralized spatial snapping service for the GridForge UI.

The SnapSystem resolves a scene-space cursor position against
the currently supported snapping targets.

Current snapping targets
------------------------
1. Bus
2. Grid
3. Original cursor position

Resolution priority
-------------------
    Bus
      ↓
    Grid
      ↓
    Original position

Architectural responsibilities
------------------------------
SnapSystem:

    - owns snapping policy;
    - determines snap priority;
    - determines model-object snap radius;
    - queries authoritative model topology for bus targets;
    - delegates grid-coordinate calculation to GridSystem;
    - returns an immutable SnapResult;
    - provides common snapping APIs to tools.

SnapSystem does NOT:

    - create model objects;
    - modify the Core model;
    - perform topology mutation;
    - create graphics items;
    - render previews;
    - implement individual tool behavior;
    - perform electrical calculations;
    - perform coordinate conversion.

Tools must not implement their own snapping algorithms.

Instead of:

    tool.snap_to_bus(...)

tools should use:

    result = interaction_manager.get_snap_system().resolve(
        position
    )

Qt rule
-------
All Qt dependencies are imported through ui.core.qt.

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot, isfinite
from typing import Any, Optional

from ui.core.qt import QPointF


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
        Final resolved scene-space position.

    target:
        Authoritative model object selected by the snap
        operation.

        Currently this is normally a Bus for
        ``snap_type="bus"``.

        It is None for grid and unsnapped positions.

    snap_type:
        Resolution type.

        Current values:

            "bus"
            "grid"
            "none"

    distance:
        Euclidean scene-space distance from the original cursor
        position to the resolved target.

        None means that no snapping target was selected.
    """

    position: QPointF
    target: Optional[Any] = None
    snap_type: str = "none"
    distance: Optional[float] = None

    # ========================================================
    # CONVENIENCE
    # ========================================================

    @property
    def snapped(self) -> bool:
        """
        Return True when the cursor was resolved to a snap
        target.
        """

        return self.snap_type != "none"

    # --------------------------------------------------------

    @property
    def bus(self) -> Optional[Any]:
        """
        Return the snapped Bus.

        Returns None when the result is not a bus snap.
        """

        if self.snap_type == "bus":
            return self.target

        return None


# ============================================================
# SNAP SYSTEM
# ============================================================


class SnapSystem:
    """
    Central spatial snapping service for GridForge.

    The service is intentionally independent of individual tools.

    Parameters
    ----------
    controller:
        GridForge UI controller providing access to the
        authoritative Core model.

    radius:
        Maximum scene-space distance for model-object snapping.

    grid_system:
        Optional GridSystem used for grid-coordinate resolution.
    """

    # ========================================================
    # DEFAULT CONFIGURATION
    # ========================================================

    DEFAULT_RADIUS = 20.0

    DEFAULT_GRID_ENABLED = False

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        radius: float = DEFAULT_RADIUS,
        grid_system: Optional[Any] = None,
    ) -> None:
        """
        Initialize the SnapSystem.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        self._validate_radius(radius)

        self.controller = controller
        self.radius = float(radius)
        self.grid_system = grid_system

        self.grid_enabled = (
            self.DEFAULT_GRID_ENABLED
        )

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def set_radius(
        self,
        radius: float,
    ) -> None:
        """
        Set the maximum model-object snapping radius.

        The radius must be finite and greater than zero.
        """

        self._validate_radius(radius)

        self.radius = float(radius)

    # --------------------------------------------------------

    def enable_grid(
        self,
    ) -> None:
        """
        Enable grid snapping.

        Grid geometry remains owned by GridSystem.
        """

        self.grid_enabled = True

    # --------------------------------------------------------

    def disable_grid(
        self,
    ) -> None:
        """
        Disable grid snapping.
        """

        self.grid_enabled = False

    # --------------------------------------------------------

    def toggle_grid(
        self,
    ) -> bool:
        """
        Toggle grid snapping.

        Returns
        -------
        bool
            New grid-enabled state.
        """

        self.grid_enabled = not self.grid_enabled

        return self.grid_enabled

    # --------------------------------------------------------

    def set_grid_system(
        self,
        grid_system: Optional[Any],
    ) -> None:
        """
        Attach or replace the GridSystem.

        Passing None removes the grid geometry service while
        preserving the grid-enabled preference.
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
    # BUS SNAP
    # ========================================================

    def snap_to_bus(
        self,
        pos: QPointF,
    ) -> SnapResult:
        """
        Resolve the cursor against the nearest authoritative Bus.

        A bus is selected only when its authoritative scene-space
        position lies within ``self.radius``.

        Boundary behavior
        -----------------
        A bus exactly on the snapping-radius boundary is accepted.

        Tie behavior
        ------------
        When two buses have exactly equal distance, the first bus
        returned by authoritative graph iteration is retained.

        Returns
        -------
        SnapResult
            ``snap_type="bus"`` when a Bus is found.

            Otherwise ``snap_type="none"``.
        """

        self._validate_point(
            pos,
            "pos",
        )

        graph = self._get_graph()

        if graph is None:
            return self._none_result(pos)

        all_buses = getattr(
            graph,
            "all_buses",
            None,
        )

        if not callable(all_buses):
            raise TypeError(
                "controller.model.graph must provide "
                "all_buses()."
            )

        px = float(pos.x())
        py = float(pos.y())

        radius_squared = (
            self.radius * self.radius
        )

        nearest_bus = None
        nearest_distance_squared = float("inf")

        for bus in all_buses():

            bx, by = self._bus_position(
                bus
            )

            dx = bx - px
            dy = by - py

            distance_squared = (
                dx * dx
                + dy * dy
            )

            # ------------------------------------------------
            # Boundary is inclusive.
            #
            # Strictly smaller distance wins so an exact
            # distance tie preserves authoritative iteration
            # order.
            # ------------------------------------------------

            if (
                distance_squared <= radius_squared
                and distance_squared
                < nearest_distance_squared
            ):
                nearest_bus = bus
                nearest_distance_squared = (
                    distance_squared
                )

        if nearest_bus is None:
            return self._none_result(pos)

        bx, by = self._bus_position(
            nearest_bus
        )

        distance = hypot(
            bx - px,
            by - py,
        )

        return SnapResult(
            position=QPointF(
                bx,
                by,
            ),
            target=nearest_bus,
            snap_type="bus",
            distance=distance,
        )

    # ========================================================
    # GRID SNAP
    # ========================================================

    def snap_to_grid(
        self,
        pos: QPointF,
    ) -> SnapResult:
        """
        Resolve a scene-space position against GridSystem.

        GridSystem owns the actual grid-coordinate calculation.

        If no GridSystem is attached, no grid snap is possible
        and an unsnapped result is returned.
        """

        self._validate_point(
            pos,
            "pos",
        )

        if self.grid_system is None:
            return self._none_result(pos)

        snap_point = getattr(
            self.grid_system,
            "snap_point",
            None,
        )

        if not callable(snap_point):
            raise TypeError(
                "grid_system must provide snap_point()."
            )

        snapped = snap_point(
            pos
        )

        self._validate_point(
            snapped,
            "grid_system.snap_point() result",
        )

        snapped_x = float(
            snapped.x()
        )

        snapped_y = float(
            snapped.y()
        )

        distance = hypot(
            snapped_x - float(pos.x()),
            snapped_y - float(pos.y()),
        )

        if not isfinite(distance):
            raise ValueError(
                "grid_system.snap_point() returned "
                "non-finite coordinates."
            )

        return SnapResult(
            position=QPointF(
                snapped_x,
                snapped_y,
            ),
            target=None,
            snap_type="grid",
            distance=distance,
        )

    # ========================================================
    # MASTER RESOLUTION
    # ========================================================

    def resolve(
        self,
        pos: QPointF,
    ) -> SnapResult:
        """
        Resolve the final snap position.

        Priority
        --------
        1. Bus
        2. Grid, when enabled
        3. Original cursor position

        This is the primary API intended for tools.
        """

        self._validate_point(
            pos,
            "pos",
        )

        # ----------------------------------------------------
        # 1. Authoritative model-object snapping.
        # ----------------------------------------------------

        bus_result = self.snap_to_bus(
            pos
        )

        if bus_result.snapped:
            return bus_result

        # ----------------------------------------------------
        # 2. Grid snapping.
        # ----------------------------------------------------

        if self.grid_enabled:

            grid_result = self.snap_to_grid(
                pos
            )

            if grid_result.snapped:
                return grid_result

        # ----------------------------------------------------
        # 3. Original cursor position.
        # ----------------------------------------------------

        return self._none_result(
            pos
        )

    # ========================================================
    # BUS-ONLY RESOLUTION
    # ========================================================

    def resolve_bus(
        self,
        pos: QPointF,
    ) -> Optional[Any]:
        """
        Return the Bus selected by the snapping rules.

        Returns None when no Bus is within the snap radius.
        """

        result = self.snap_to_bus(
            pos
        )

        return result.bus

    # ========================================================
    # POSITION-ONLY RESOLUTION
    # ========================================================

    def resolve_position(
        self,
        pos: QPointF,
    ) -> QPointF:
        """
        Return only the resolved scene-space position.
        """

        return self.resolve(
            pos
        ).position

    # ========================================================
    # MODEL ACCESS
    # ========================================================

    def _get_graph(
        self,
    ) -> Any:
        """
        Return the authoritative Core graph.

        The SnapSystem does not own or cache the graph.

        The Core model may be replaced during project loading
        or reset operations, so the graph is resolved dynamically.
        """

        model = getattr(
            self.controller,
            "model",
            None,
        )

        if model is None:
            return None

        return getattr(
            model,
            "graph",
            None,
        )

    # ========================================================
    # BUS POSITION
    # ========================================================

    @staticmethod
    def _bus_position(
        bus: Any,
    ) -> tuple[float, float]:
        """
        Extract the authoritative scene position of a Bus.

        Current GridForge model contract:

            bus.x
            bus.y

        SnapSystem does not maintain a second spatial
        representation.
        """

        if bus is None:
            raise TypeError(
                "Bus target must not be None."
            )

        try:
            x = float(
                bus.x
            )
            y = float(
                bus.y
            )

        except (
            AttributeError,
            TypeError,
            ValueError,
        ) as exc:

            raise TypeError(
                "Bus snap targets must provide numeric "
                "x and y attributes."
            ) from exc

        if not isfinite(x) or not isfinite(y):
            raise ValueError(
                "Bus snap targets must provide finite "
                "x and y coordinates."
            )

        return x, y

    # ========================================================
    # RESULT HELPERS
    # ========================================================

    @staticmethod
    def _none_result(
        pos: QPointF,
    ) -> SnapResult:
        """
        Construct an explicit unsnapped result.

        A copy of the position is returned so the result does
        not depend on mutable external QPointF state.
        """

        return SnapResult(
            position=QPointF(
                float(pos.x()),
                float(pos.y()),
            ),
            target=None,
            snap_type="none",
            distance=None,
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

        The point must expose callable x()/y() methods and
        contain finite numeric coordinates.
        """

        if point is None:
            raise ValueError(
                f"{name} must not be None."
            )

        x_method = getattr(
            point,
            "x",
            None,
        )

        if not callable(x_method):
            raise TypeError(
                f"{name} must provide x()."
            )

        y_method = getattr(
            point,
            "y",
            None,
        )

        if not callable(y_method):
            raise TypeError(
                f"{name} must provide y()."
            )

        try:
            x = float(
                x_method()
            )
            y = float(
                y_method()
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise TypeError(
                f"{name} must provide numeric x/y "
                "coordinates."
            ) from exc

        if not isfinite(x) or not isfinite(y):
            raise ValueError(
                f"{name} must provide finite coordinates."
            )

    # --------------------------------------------------------

    @staticmethod
    def _validate_radius(
        radius: float,
    ) -> None:
        """
        Validate a snap radius.

        Radius must be a finite numeric value greater than zero.
        """

        if isinstance(
            radius,
            bool,
        ):
            raise TypeError(
                "radius must be a positive finite number."
            )

        try:
            numeric_radius = float(
                radius
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise TypeError(
                "radius must be a positive finite number."
            ) from exc

        if not isfinite(
            numeric_radius
        ):
            raise ValueError(
                "Snap radius must be finite."
            )

        if numeric_radius <= 0:
            raise ValueError(
                "Snap radius must be greater than zero."
            )

    # ========================================================
    # DEBUG / INTROSPECTION
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return the current snapping configuration.
        """

        return {
            "radius": self.radius,
            "grid_enabled": self.grid_enabled,
            "grid_system": (
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
            "SnapSystem("
            f"radius={self.radius}, "
            f"grid_enabled={self.grid_enabled}, "
            f"grid_system="
            f"{self.grid_system is not None}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "SnapResult",
    "SnapSystem",
]
