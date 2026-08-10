```python
# ============================================================
# File: ui/canvas/coordinate_system.py
# GridForge Canvas Coordinate System
# ============================================================
#
# PURPOSE
# -------
# Centralized coordinate handling for the GridForge canvas.
#
# This class provides one consistent place for converting and
# formatting coordinates used by:
#
#     - GraphicsView
#     - NavigationController
#     - GridSystem
#     - SnapSystem
#     - InteractionManager
#     - StatusBar
#     - Future measurement tools
#
#
# COORDINATE SPACES
# -----------------
#
# GridForge currently uses three important coordinate spaces:
#
#     1. VIEWPORT
#        Mouse/widget coordinates.
#
#     2. SCENE
#        QGraphicsScene coordinates.
#
#     3. GRID
#        Scene coordinates resolved against the engineering
#        grid.
#
#
# ARCHITECTURE
# ------------
#
#              Mouse
#                │
#                ▼
#          Viewport Position
#                │
#                ▼
#         CoordinateSystem
#                │
#          ┌─────┴─────┐
#          ▼           ▼
#       Scene        Grid
#      Position    Position
#          │
#          ▼
#       StatusBar
#
#
# IMPORTANT
# ---------
#
# CoordinateSystem does NOT:
#
#     - modify the Core model
#     - perform electrical calculations
#     - create graphics items
#     - manage tools
#     - perform selection
#
# It is purely a coordinate conversion and formatting service.
#
#
# QT RULE
# -------
#
# All Qt classes must be imported through:
#
#     ui.core.qt
#
# No direct PySide6/PyQt imports are permitted.
#
# ============================================================

from __future__ import annotations

from typing import Any


from ui.core.qt import QPointF


class CoordinateSystem:
    """
    Central coordinate conversion and formatting service.

    Parameters
    ----------
    view:
        QGraphicsView used by the GridForge canvas.

    grid_system:
        Optional GridSystem used for grid-coordinate conversion.
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
        grid_system=None,
    ) -> None:
        """
        Initialize the coordinate system.

        Parameters
        ----------
        view:
            GridForge QGraphicsView.

        grid_system:
            Optional GridSystem instance.

        The view is used only for coordinate conversion.
        """

        self.view = view

        self.grid_system = grid_system

        # ----------------------------------------------------
        # Display configuration.
        # ----------------------------------------------------

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
        viewport_pos,
    ) -> QPointF:
        """
        Convert viewport coordinates to scene coordinates.

        Parameters
        ----------
        viewport_pos:
            QPoint or QPointF in viewport coordinates.

        Returns
        -------
        QPointF
            Position in QGraphicsScene coordinates.

        This is the primary conversion required for mouse
        interaction.
        """

        # ----------------------------------------------------
        # QGraphicsView.mapToScene() accepts QPoint.
        #
        # If a QPointF is supplied, convert it to integer
        # viewport coordinates because the Qt API is designed
        # around QPoint for this mapping operation.
        # ----------------------------------------------------

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
    ):
        """
        Convert scene coordinates to viewport coordinates.

        Returns a QPoint suitable for QGraphicsView and
        QWidget-related operations.
        """

        return self.view.mapFromScene(
            scene_pos
        )

    # ========================================================
    # SCENE POSITION
    # ========================================================

    def current_scene_position(
        self,
        viewport_pos,
    ) -> QPointF:
        """
        Convenience wrapper for obtaining the scene position
        of a mouse cursor.

        Equivalent to viewport_to_scene(), but explicitly
        expresses the intended use.
        """

        return self.viewport_to_scene(
            viewport_pos
        )

    # ========================================================
    # GRID COORDINATES
    # ========================================================

    def scene_to_grid(
        self,
        scene_pos: QPointF,
    ) -> QPointF:
        """
        Convert a scene position to the nearest grid position.

        If no GridSystem is attached, the original position is
        returned unchanged.
        """

        if self.grid_system is None:

            return QPointF(
                scene_pos.x(),
                scene_pos.y(),
            )

        return self.grid_system.snap_point(
            scene_pos
        )

    # --------------------------------------------------------

    def grid_position(
        self,
        viewport_pos,
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

        scene_pos = (
            self.viewport_to_scene(
                viewport_pos
            )
        )

        return self.scene_to_grid(
            scene_pos
        )

    # ========================================================
    # COORDINATE DIFFERENCE
    # ========================================================

    def distance(
        self,
        first: QPointF,
        second: QPointF,
    ) -> float:
        """
        Calculate Euclidean distance between two scene points.

        This is a geometric utility only.

        No electrical units are implied.
        """

        dx = (
            second.x()
            - first.x()
        )

        dy = (
            second.y()
            - first.y()
        )

        return (
            dx * dx
            + dy * dy
        ) ** 0.5

    # ========================================================
    # MIDPOINT
    # ========================================================

    def midpoint(
        self,
        first: QPointF,
        second: QPointF,
    ) -> QPointF:
        """
        Return the midpoint between two scene coordinates.
        """

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

        Example
        -------
        X: 125.00  Y: 80.00
        """

        x = format(
            position.x(),
            f".{self.decimals}f",
        )

        y = format(
            position.y(),
            f".{self.decimals}f",
        )

        return (
            f"X: {x}    Y: {y}"
        )

    # --------------------------------------------------------

    def format_point(
        self,
        position: QPointF,
    ) -> str:
        """
        Format a coordinate pair as a compact point.

        Example
        -------
        (125.00, 80.00)
        """

        x = format(
            position.x(),
            f".{self.decimals}f",
        )

        y = format(
            position.y(),
            f".{self.decimals}f",
        )

        return (
            f"({x}, {y})"
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
            Number of decimal places.

        Zero or greater is required.
        """

        if decimals < 0:
            raise ValueError(
                "Decimal precision cannot be negative."
            )

        self.decimals = int(
            decimals
        )

    # --------------------------------------------------------

    def set_unit(
        self,
        unit: str,
    ) -> None:
        """
        Set the optional coordinate display unit.

        Example:
            "px"
            "m"
            "mm"

        The coordinate system itself does not convert units.
        Unit conversion belongs to a future engineering-unit
        system.
        """

        self.unit = (
            str(unit)
            if unit
            else ""
        )

    # ========================================================
    # STATUS BAR DATA
    # ========================================================

    def get_status_data(
        self,
        viewport_pos,
    ) -> dict:
        """
        Return coordinate information suitable for the
        GridForge StatusBar.

        The returned dictionary deliberately contains both
        scene and grid positions so the StatusBar can later
        display whichever representation is appropriate.
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
    # DEBUG / STATE
    # ========================================================

    def get_state(self) -> dict:
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
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "CoordinateSystem("
            f"decimals={self.decimals}, "
            f"unit='{self.unit}', "
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
```
