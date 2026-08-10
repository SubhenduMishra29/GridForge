```python
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
# The grid is a VIEW feature only.
#
# It does not:
#
#     - modify the Core model
#     - create electrical objects
#     - perform topology operations
#     - handle tools
#     - perform snapping
#
#
# ARCHITECTURE
# ------------
#
#                 QGraphicsScene
#                       │
#                       ▼
#                  GridSystem
#                       │
#                       ▼
#                 Grid rendering
#
#
# IMPORTANT
# ---------
#
# Grid display and snapping are deliberately separate.
#
# GridSystem:
#     visual grid + coordinate/grid calculations
#
# SnapSystem:
#     snap-to-grid + snap-to-bus + future snapping modes
#
#
# This separation prevents the visual grid implementation from
# becoming coupled to interaction tools.
#
#
# QT RULE
# -------
#
# All Qt imports come through:
#
#     ui.core.qt
#
# No direct PySide6 / PyQt imports are permitted here.
#
# ============================================================

from __future__ import annotations

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
    Manages the visual engineering grid of the GridForge canvas.

    The GridSystem does not own the QGraphicsScene.

    Instead, it is given a scene and provides methods that the
    canvas/view can use to render the grid.
    """

    # ========================================================
    # DEFAULT CONFIGURATION
    # ========================================================

    # Distance between minor grid lines in scene coordinates.
    DEFAULT_MINOR_SPACING = 20.0

    # Number of minor cells between major grid lines.
    DEFAULT_MAJOR_INTERVAL = 5

    # Whether the grid is initially visible.
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
            QGraphicsScene used by the GridForge canvas.

        minor_spacing:
            Distance between adjacent minor grid lines in
            scene coordinates.

        major_interval:
            Number of minor grid cells between major grid lines.
        """

        self.scene = scene

        # ----------------------------------------------------
        # Validate spacing.
        # ----------------------------------------------------

        if minor_spacing <= 0:
            raise ValueError(
                "Grid spacing must be greater than zero."
            )

        if major_interval <= 0:
            raise ValueError(
                "Major grid interval must be greater than zero."
            )

        self.minor_spacing = float(
            minor_spacing
        )

        self.major_interval = int(
            major_interval
        )

        # ----------------------------------------------------
        # Visibility.
        # ----------------------------------------------------

        self.visible = (
            self.DEFAULT_VISIBLE
        )

        # ----------------------------------------------------
        # Visual configuration.
        #
        # These attributes are intentionally configurable so
        # the future appearance/settings system can modify
        # them without changing the grid implementation.
        # ----------------------------------------------------

        self.minor_color = (
            self.DEFAULT_MINOR_COLOR
        )

        self.major_color = (
            self.DEFAULT_MAJOR_COLOR
        )

        self.minor_width = (
            self.DEFAULT_MINOR_WIDTH
        )

        self.major_width = (
            self.DEFAULT_MAJOR_WIDTH
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

        if spacing <= 0:
            raise ValueError(
                "Grid spacing must be greater than zero."
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
        Change the number of minor cells per major grid cell.
        """

        if interval <= 0:
            raise ValueError(
                "Major grid interval must be greater than zero."
            )

        self.major_interval = int(
            interval
        )

    # ========================================================
    # GRID CALCULATIONS
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

        IMPORTANT
        ---------
        This method only calculates grid coordinates.

        The actual application SnapSystem will eventually
        decide whether grid snapping should be applied.
        """

        spacing = self.minor_spacing

        x = round(
            point.x() / spacing
        ) * spacing

        y = round(
            point.y() / spacing
        ) * spacing

        return QPointF(
            x,
            y,
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
        Calculate the first grid coordinate visible from a
        minimum scene coordinate.
        """

        return (
            int(minimum / spacing)
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
        Draw the grid inside a scene rectangle.

        Parameters
        ----------
        painter:
            QPainter supplied by the canvas/view.

        rect:
            Scene-space rectangle that needs to be painted.

        Notes
        -----
        The grid is drawn in scene coordinates.

        Therefore the same grid coordinates remain valid when
        the canvas is zoomed or panned.
        """

        if not self.visible:
            return

        if rect.isEmpty():
            return

        # ----------------------------------------------------
        # Grid spacing.
        # ----------------------------------------------------

        minor = self.minor_spacing
        major = self.major_spacing

        # ----------------------------------------------------
        # Determine first visible grid coordinates.
        # ----------------------------------------------------

        first_x = self._first_grid_value(
            rect.left(),
            minor,
        )

        first_y = self._first_grid_value(
            rect.top(),
            minor,
        )

        # ----------------------------------------------------
        # Prepare pens.
        # ----------------------------------------------------

        minor_pen = QPen(
            self.minor_color,
            self.minor_width,
        )

        major_pen = QPen(
            self.major_color,
            self.major_width,
        )

        # ----------------------------------------------------
        # Draw vertical grid lines.
        # ----------------------------------------------------

        x = first_x

        while x <= rect.right():

            # Determine whether this is a major grid line.
            grid_index = round(
                x / minor
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
        # Draw horizontal grid lines.
        # ----------------------------------------------------

        y = first_y

        while y <= rect.bottom():

            grid_index = round(
                y / minor
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
        Return current grid configuration.

        Useful for:
            - debugging
            - preferences
            - future serialization
            - UI settings panels
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

    # ========================================================
    # DEBUG
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
```
