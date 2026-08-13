# ============================================================
# File: ui/canvas/grid_system.py
# GridForge Canvas Grid System
# ============================================================
#
# PURPOSE
# -------
# Provides the visual engineering grid used by the GridForge
# canvas.
#
# The GridSystem is a canvas/view infrastructure service.
#
# It provides:
#
#     - grid visibility
#     - grid spacing
#     - major/minor grid configuration
#     - grid-coordinate calculation
#     - grid rendering
#
# It does NOT:
#
#     - modify the Core model
#     - create electrical objects
#     - perform topology operations
#     - manage tools
#     - perform selection
#     - decide whether snapping is enabled
#     - perform object-target snapping
#
#
# ARCHITECTURE
# ------------
#
#                 QGraphicsScene/View
#                         │
#                         ▼
#                    GridSystem
#                         │
#                  ┌──────┴──────┐
#                  ▼             ▼
#             Grid Geometry   Rendering
#                  │
#                  ▼
#              SnapSystem
#
#
# IMPORTANT
# ---------
#
# Grid display and snapping are separate concerns.
#
# GridSystem:
#
#     visual grid
#     grid geometry
#     scene-space grid calculation
#
# SnapSystem:
#
#     snapping policy
#     snap priority
#     bus/object snapping
#     grid snapping enable/disable
#
#
# QT RULE
# -------
#
# All Qt classes must be imported through:
#
#     ui.core.qt
#
# No direct PySide6 / PyQt imports are permitted.
#
# ============================================================

from __future__ import annotations

import math
from typing import Any

from ui.core.qt import (
    QColor,
    QPainter,
    QPen,
    QPointF,
    QRectF,
)


class GridSystem:
    """
    Provides the visual and geometric engineering grid for the
    GridForge canvas.

    GridSystem is deliberately independent of:

        - Core model
        - Controller
        - ToolManager
        - InteractionManager
        - SnapSystem

    SnapSystem may use ``snap_point()`` when grid snapping is
    enabled.
    """

    # ========================================================
    # DEFAULT CONFIGURATION
    # ========================================================

    DEFAULT_MINOR_SPACING = 20.0

    DEFAULT_MAJOR_INTERVAL = 5

    DEFAULT_VISIBLE = True

    # --------------------------------------------------------
    # Visual configuration
    # --------------------------------------------------------

    DEFAULT_MINOR_COLOR = QColor(
        225,
        225,
        225,
    )

    DEFAULT_MAJOR_COLOR = QColor(
        195,
        195,
        195,
    )

    DEFAULT_MINOR_WIDTH = 0.5

    DEFAULT_MAJOR_WIDTH = 1.0

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        scene: Any,
        minor_spacing: float = DEFAULT_MINOR_SPACING,
        major_interval: int = DEFAULT_MAJOR_INTERVAL,
    ) -> None:
        """
        Initialize the GridSystem.

        Parameters
        ----------
        scene:
            QGraphicsScene associated with the canvas.

            GridSystem does not own or mutate the scene.

        minor_spacing:
            Distance between adjacent minor grid lines in
            scene coordinates.

        major_interval:
            Number of minor grid cells between major grid lines.
        """

        if scene is None:
            raise ValueError(
                "scene cannot be None."
            )

        self.scene = scene

        self._validate_spacing(
            minor_spacing
        )

        self._validate_major_interval(
            major_interval
        )

        self.minor_spacing = float(
            minor_spacing
        )

        self.major_interval = int(
            major_interval
        )

        self.visible = (
            self.DEFAULT_VISIBLE
        )

        # ----------------------------------------------------
        # Visual configuration.
        # ----------------------------------------------------

        self.minor_color = QColor(
            self.DEFAULT_MINOR_COLOR
        )

        self.major_color = QColor(
            self.DEFAULT_MAJOR_COLOR
        )

        self.minor_width = float(
            self.DEFAULT_MINOR_WIDTH
        )

        self.major_width = float(
            self.DEFAULT_MAJOR_WIDTH
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_spacing(
        spacing: float,
    ) -> None:
        """
        Validate grid spacing.
        """

        if not isinstance(
            spacing,
            (int, float),
        ):
            raise TypeError(
                "Grid spacing must be numeric."
            )

        if not math.isfinite(
            float(spacing)
        ):
            raise ValueError(
                "Grid spacing must be finite."
            )

        if spacing <= 0:
            raise ValueError(
                "Grid spacing must be greater than zero."
            )

    # --------------------------------------------------------

    @staticmethod
    def _validate_major_interval(
        interval: int,
    ) -> None:
        """
        Validate major-grid interval.
        """

        if isinstance(
            interval,
            bool,
        ) or not isinstance(
            interval,
            int,
        ):
            raise TypeError(
                "Major grid interval must be an integer."
            )

        if interval <= 0:
            raise ValueError(
                "Major grid interval must be greater than zero."
            )

    # ========================================================
    # VISIBILITY
    # ========================================================

    def show(self) -> None:
        """
        Enable grid rendering.
        """

        self.visible = True

    # --------------------------------------------------------

    def hide(self) -> None:
        """
        Disable grid rendering.
        """

        self.visible = False

    # --------------------------------------------------------

    def toggle(self) -> bool:
        """
        Toggle grid visibility.

        Returns
        -------
        bool
            New visibility state.
        """

        self.visible = not self.visible

        return self.visible

    # ========================================================
    # GRID SPACING
    # ========================================================

    def set_spacing(
        self,
        spacing: float,
    ) -> None:
        """
        Change the minor grid spacing.

        Parameters
        ----------
        spacing:
            New spacing in scene coordinates.
        """

        self._validate_spacing(
            spacing
        )

        self.minor_spacing = float(
            spacing
        )

    # --------------------------------------------------------

    def set_major_interval(
        self,
        interval: int,
    ) -> None:
        """
        Change the number of minor cells between major grid
        lines.
        """

        self._validate_major_interval(
            interval
        )

        self.major_interval = int(
            interval
        )

    # ========================================================
    # GRID GEOMETRY
    # ========================================================

    @property
    def major_spacing(self) -> float:
        """
        Return the distance between major grid lines.
        """

        return (
            self.minor_spacing
            * self.major_interval
        )

    # --------------------------------------------------------

    def snap_point(
        self,
        point: QPointF,
    ) -> QPointF:
        """
        Return the nearest grid intersection.

        This method performs only the geometric grid
        calculation.

        It does NOT determine whether grid snapping should
        occur. That policy belongs to SnapSystem.

        Parameters
        ----------
        point:
            Scene-space position.

        Returns
        -------
        QPointF
            Nearest grid position.
        """

        if point is None:
            raise ValueError(
                "point cannot be None."
            )

        spacing = self.minor_spacing

        x = (
            round(
                point.x() / spacing
            )
            * spacing
        )

        y = (
            round(
                point.y() / spacing
            )
            * spacing
        )

        return QPointF(
            x,
            y,
        )

    # ========================================================
    # GRID INDEX
    # ========================================================

    def _grid_index(
        self,
        coordinate: float,
    ) -> int:
        """
        Return the nearest integer grid index.

        This helper is used only for determining major/minor
        classification.

        Python's round() is intentionally used so that the
        classification corresponds to the same grid geometry
        used by snap_point().
        """

        return int(
            round(
                coordinate
                / self.minor_spacing
            )
        )

    # ========================================================
    # GRID RANGE
    # ========================================================

    def _first_grid_value(
        self,
        minimum: float,
        spacing: float,
    ) -> float:
        """
        Return the first grid coordinate at or before
        ``minimum``.

        ``math.floor`` is required here.

        Using ``int()`` would be incorrect for negative scene
        coordinates because int() truncates toward zero.
        """

        return (
            math.floor(
                minimum / spacing
            )
            * spacing
        )

    # ========================================================
    # GRID DRAWING
    # ========================================================

    def draw(
        self,
        painter: QPainter,
        rect: QRectF,
    ) -> None:
        """
        Draw the grid inside a scene-space rectangle.

        Parameters
        ----------
        painter:
            QPainter supplied by the canvas/view.

        rect:
            Scene-space rectangle requiring grid rendering.

        Notes
        -----
        Grid coordinates are scene coordinates.

        Consequently the grid naturally follows the scene
        transformation during zooming and panning.
        """

        if not self.visible:
            return

        if painter is None:
            raise ValueError(
                "painter cannot be None."
            )

        if rect is None:
            raise ValueError(
                "rect cannot be None."
            )

        if rect.isEmpty():
            return

        minor = self.minor_spacing

        first_x = self._first_grid_value(
            rect.left(),
            minor,
        )

        first_y = self._first_grid_value(
            rect.top(),
            minor,
        )

        minor_pen = QPen(
            self.minor_color,
            self.minor_width,
        )

        major_pen = QPen(
            self.major_color,
            self.major_width,
        )

        # ----------------------------------------------------
        # Vertical lines
        # ----------------------------------------------------

        x = first_x

        while x <= rect.right():

            grid_index = self._grid_index(
                x
            )

            if (
                grid_index
                % self.major_interval
                == 0
            ):
                painter.setPen(
                    major_pen
                )
            else:
                painter.setPen(
                    minor_pen
                )

            painter.drawLine(
                QPointF(
                    x,
                    rect.top(),
                ),
                QPointF(
                    x,
                    rect.bottom(),
                ),
            )

            x += minor

        # ----------------------------------------------------
        # Horizontal lines
        # ----------------------------------------------------

        y = first_y

        while y <= rect.bottom():

            grid_index = self._grid_index(
                y
            )

            if (
                grid_index
                % self.major_interval
                == 0
            ):
                painter.setPen(
                    major_pen
                )
            else:
                painter.setPen(
                    minor_pen
                )

            painter.drawLine(
                QPointF(
                    rect.left(),
                    y,
                ),
                QPointF(
                    rect.right(),
                    y,
                ),
            )

            y += minor

    # ========================================================
    # GRID INFORMATION
    # ========================================================

    def get_grid_info(self) -> dict:
        """
        Return the current grid configuration.
        """

        return {
            "visible": self.visible,
            "minor_spacing": self.minor_spacing,
            "major_interval": self.major_interval,
            "major_spacing": self.major_spacing,
        }

    # ========================================================
    # RESET
    # ========================================================

    def reset(self) -> None:
        """
        Restore the default grid configuration.

        Visual styling is also restored because reset is
        defined as a complete GridSystem configuration reset.
        """

        self.minor_spacing = (
            self.DEFAULT_MINOR_SPACING
        )

        self.major_interval = (
            self.DEFAULT_MAJOR_INTERVAL
        )

        self.visible = (
            self.DEFAULT_VISIBLE
        )

        self.minor_color = QColor(
            self.DEFAULT_MINOR_COLOR
        )

        self.major_color = QColor(
            self.DEFAULT_MAJOR_COLOR
        )

        self.minor_width = (
            self.DEFAULT_MINOR_WIDTH
        )

        self.major_width = (
            self.DEFAULT_MAJOR_WIDTH
        )

    # ========================================================
    # DEBUG / INTROSPECTION
    # ========================================================

    def get_state(self) -> dict:
        """
        Return diagnostic GridSystem state.
        """

        return {
            "visible": self.visible,
            "minor_spacing": self.minor_spacing,
            "major_interval": self.major_interval,
            "major_spacing": self.major_spacing,
            "minor_width": self.minor_width,
            "major_width": self.major_width,
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "GridSystem("
            f"visible={self.visible}, "
            f"minor_spacing={self.minor_spacing}, "
            f"major_interval={self.major_interval}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "GridSystem",
]
