# ============================================================
# File: ui/core/snap_system.py
# GridForge Snap System
# ============================================================
#
# PURPOSE
# -------
# Centralized spatial snapping system for the GridForge UI.
#
# The SnapSystem determines whether a cursor position should
# be attached to a nearby electrical object or grid position.
#
# CURRENTLY SUPPORTED
# -------------------
#
#     1. Snap to nearest Bus
#     2. Snap to Grid
#
# The system is designed so additional snapping targets can
# be added later without putting spatial-query logic into tools.
#
#
# ARCHITECTURE
# ------------
#
#                  Mouse Position
#                        │
#                        ▼
#                   SnapSystem
#                        │
#              ┌─────────┴─────────┐
#              │                   │
#          Bus Snap            Grid Snap
#              │                   │
#              └─────────┬─────────┘
#                        ▼
#                  SnapResult
#
#
# IMPORTANT DESIGN RULE
# ---------------------
#
# Tools must NOT independently calculate snapping distances.
#
# For example, LineTool should NOT contain:
#
#     snap_to_bus(...)
#
# Instead:
#
#     result = snap_system.resolve(position)
#
# This guarantees that:
#
#     BusTool
#     LineTool
#     TransformerTool
#     GeneratorTool
#     LoadTool
#
# all use exactly the same snapping rules.
#
#
# SNAP PRIORITY
# -------------
#
# The current priority is:
#
#     1. Bus
#     2. Grid
#     3. Original cursor position
#
# A future priority system can introduce:
#
#     - line terminals
#     - transformer terminals
#     - generator terminals
#     - breaker terminals
#     - custom connection points
#
#
# QT RULE
# -------
#
# All Qt classes are imported through:
#
#     ui.core.qt
#
# No direct PySide6 or PyQt imports are permitted.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Any, Optional


from ui.core.qt import QPointF


# ============================================================
# SNAP RESULT
# ============================================================

@dataclass(frozen=True)
class SnapResult:
    """
    Immutable result returned by the SnapSystem.

    Attributes
    ----------
    position:
        Final resolved scene position.

    target:
        Model object to which the position was snapped.

        For example:
            Bus instance

        None means that no model object was selected.

    snap_type:
        Identifies how the position was resolved.

        Possible values currently include:

            "bus"
            "grid"
            "none"

    distance:
        Original cursor distance from the selected target.

        For grid snapping this represents the distance from
        the original cursor position to the grid position.

        None means that no target was selected.
    """

    position: QPointF

    target: Optional[Any] = None

    snap_type: str = "none"

    distance: Optional[float] = None

    # --------------------------------------------------------
    # Convenience properties
    # --------------------------------------------------------

    @property
    def snapped(self) -> bool:
        """
        Return True if a snapping operation occurred.
        """

        return self.snap_type != "none"

    # --------------------------------------------------------

    @property
    def bus(self):
        """
        Return the snapped Bus if the target is a bus.

        Returns None for all other snap types.

        This convenience property keeps tools from needing
        to inspect the snap_type manually.
        """

        if self.snap_type == "bus":
            return self.target

        return None


# ============================================================
# SNAP SYSTEM
# ============================================================

class SnapSystem:
    """
    Central spatial snapping service.

    The SnapSystem is intentionally independent from tools.

    It receives:
        - controller
        - cursor position

    and returns:
        - resolved position
        - snapping target
        - snap type
        - distance
    """

    # ========================================================
    # DEFAULT CONFIGURATION
    # ========================================================

    # Default snapping radius in scene coordinates.

    DEFAULT_RADIUS = 20.0

    # Default grid snapping state.

    DEFAULT_GRID_ENABLED = False

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller,
        radius: float = DEFAULT_RADIUS,
        grid_system=None,
    ) -> None:
        """
        Initialize the SnapSystem.

        Parameters
        ----------
        controller:
            GridForge UI Controller.

        radius:
            Maximum scene-space distance within which a model
            object can be selected as a snap target.

        grid_system:
            Optional GridSystem instance.

            It is kept optional because grid snapping should
            not be required for bus snapping.
        """

        if radius <= 0:
            raise ValueError(
                "Snap radius must be greater than zero."
            )

        self.controller = controller

        self.radius = float(radius)

        self.grid_system = grid_system

        # ----------------------------------------------------
        # Grid snapping is deliberately disabled by default.
        #
        # Bus snapping remains available independently.
        # ----------------------------------------------------

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
        Change the maximum snapping distance.

        Parameters
        ----------
        radius:
            New snapping radius in scene coordinates.
        """

        if radius <= 0:
            raise ValueError(
                "Snap radius must be greater than zero."
            )

        self.radius = float(radius)

    # --------------------------------------------------------

    def enable_grid(self) -> None:
        """
        Enable grid snapping.
        """

        self.grid_enabled = True

    # --------------------------------------------------------

    def disable_grid(self) -> None:
        """
        Disable grid snapping.
        """

        self.grid_enabled = False

    # --------------------------------------------------------

    def toggle_grid(self) -> bool:
        """
        Toggle grid snapping.

        Returns
        -------
        bool
            New grid snapping state.
        """

        self.grid_enabled = not self.grid_enabled

        return self.grid_enabled

    # ========================================================
    # BUS SNAP
    # ========================================================

    def snap_to_bus(
        self,
        pos: QPointF,
    ) -> SnapResult:
        """
        Find the nearest Bus within the snapping radius.

        Parameters
        ----------
        pos:
            Cursor position in scene coordinates.

        Returns
        -------
        SnapResult
            If a bus is within range:

                position = bus position
                target   = bus
                snap_type = "bus"

            Otherwise:

                position = original cursor position
                target   = None
                snap_type = "none"
        """

        graph = (
            self.controller.model.graph
        )

        nearest_bus = None

        min_distance = float("inf")

        px = pos.x()
        py = pos.y()

        # ----------------------------------------------------
        # Search every bus in the graph.
        #
        # The comparison uses squared distance so that we do
        # not repeatedly calculate square roots.
        # ----------------------------------------------------

        radius_squared = (
            self.radius * self.radius
        )

        nearest_distance_squared = (
            radius_squared
        )

        for bus in graph.all_buses():

            dx = bus.x - px
            dy = bus.y - py

            distance_squared = (
                dx * dx
                + dy * dy
            )

            if (
                distance_squared
                <= nearest_distance_squared
            ):

                nearest_distance_squared = (
                    distance_squared
                )

                nearest_bus = bus

        # ----------------------------------------------------
        # A valid bus was found.
        # ----------------------------------------------------

        if nearest_bus is not None:

            distance = hypot(
                nearest_bus.x - px,
                nearest_bus.y - py,
            )

            return SnapResult(
                position=QPointF(
                    nearest_bus.x,
                    nearest_bus.y,
                ),
                target=nearest_bus,
                snap_type="bus",
                distance=distance,
            )

        # ----------------------------------------------------
        # No bus found.
        # ----------------------------------------------------

        return SnapResult(
            position=QPointF(
                px,
                py,
            ),
            target=None,
            snap_type="none",
            distance=None,
        )

    # ========================================================
    # GRID SNAP
    # ========================================================

    def snap_to_grid(
        self,
        pos: QPointF,
    ) -> SnapResult:
        """
        Snap a scene position to the nearest grid point.

        GridSystem performs the actual grid-coordinate
        calculation.

        If no GridSystem has been configured, the original
        position is returned unchanged.
        """

        if self.grid_system is None:

            return SnapResult(
                position=QPointF(
                    pos.x(),
                    pos.y(),
                ),
                target=None,
                snap_type="none",
                distance=None,
            )

        snapped = (
            self.grid_system.snap_point(pos)
        )

        distance = hypot(
            snapped.x() - pos.x(),
            snapped.y() - pos.y(),
        )

        return SnapResult(
            position=snapped,
            target=None,
            snap_type="grid",
            distance=distance,
        )

    # ========================================================
    # MASTER SNAP RESOLUTION
    # ========================================================

    def resolve(
        self,
        pos: QPointF,
    ) -> SnapResult:
        """
        Resolve the final snapping position.

        This is the primary API that tools should use.

        SNAP PRIORITY
        -------------

        1. Bus
        2. Grid
        3. Original position

        Therefore, if the cursor is close enough to a bus,
        the bus always wins over the grid.

        Parameters
        ----------
        pos:
            Cursor position in scene coordinates.

        Returns
        -------
        SnapResult
            Final resolved snap result.
        """

        # ----------------------------------------------------
        # 1. Try Bus snapping first.
        # ----------------------------------------------------

        bus_result = self.snap_to_bus(pos)

        if bus_result.snapped:

            return bus_result

        # ----------------------------------------------------
        # 2. Try Grid snapping if enabled.
        # ----------------------------------------------------

        if self.grid_enabled:

            return self.snap_to_grid(pos)

        # ----------------------------------------------------
        # 3. No snapping.
        # ----------------------------------------------------

        return SnapResult(
            position=QPointF(
                pos.x(),
                pos.y(),
            ),
            target=None,
            snap_type="none",
            distance=None,
        )

    # ========================================================
    # BUS-ONLY RESOLUTION
    # ========================================================

    def resolve_bus(
        self,
        pos: QPointF,
    ):
        """
        Convenience method for tools that specifically require
        a Bus connection.

        Example:
            LineTool

        Returns
        -------
        Bus or None
        """

        result = self.snap_to_bus(pos)

        return result.bus

    # ========================================================
    # POSITION-ONLY RESOLUTION
    # ========================================================

    def resolve_position(
        self,
        pos: QPointF,
    ) -> QPointF:
        """
        Return only the final resolved position.

        Useful for tools such as BusTool where the tool needs
        the snapped location but not necessarily the target.
        """

        return self.resolve(pos).position

    # ========================================================
    # DEBUG / INTROSPECTION
    # ========================================================

    def get_state(self) -> dict:
        """
        Return current snapping configuration.

        Useful for:
            - debugging
            - future UI settings
            - persistence
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

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "SnapSystem("
            f"radius={self.radius}, "
            f"grid_enabled={self.grid_enabled}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "SnapResult",
    "SnapSystem",
]
