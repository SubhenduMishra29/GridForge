# ============================================================
# File: ui/canvas/grid_system.py
# GridForge V2 — Canvas Grid System
# ============================================================
"""
Centralized visual grid geometry service for the GridForge
canvas.

Responsibilities
----------------
GridSystem owns only canvas-grid geometry and presentation
state.

It is responsible for:

    - grid spacing;
    - major/minor grid configuration;
    - grid visibility;
    - scene-space grid snapping;
    - grid coordinate resolution;
    - grid geometry queries;
    - grid configuration diagnostics.

GridSystem does NOT:

    - modify the Core model;
    - create QGraphicsItems;
    - render the grid directly;
    - own the canvas scene;
    - manage tools;
    - manage selection;
    - perform object snapping;
    - perform electrical calculations;
    - perform navigation;
    - decide application-level tool selection.

Rendering
---------
GridSystem provides geometry/configuration.

RenderSystem owns visual grid rendering.

Therefore:

    GridSystem
         │
         ├── geometry
         ├── spacing
         ├── visibility/configuration
         │
         ▼
    RenderSystem

Snapping
--------
GridSystem provides only grid-coordinate resolution.

SnapSystem owns snapping policy and object snapping.

Therefore:

    CoordinateSystem
          │
          ▼
    GridSystem.snap_point()

is a pure grid-resolution operation.

Whereas:

    Tool
      │
      ▼
    SnapSystem
      │
      ├── object snapping
      ├── terminal snapping
      ├── bus snapping
      └── grid snapping policy

Qt Architecture
---------------
GridSystem contains no direct Qt dependency.

Grid coordinates are represented using simple numeric
coordinates where possible so the service remains independent
of rendering and interaction infrastructure.
"""

from __future__ import annotations

from math import floor
from typing import Any


class GridSystem:
    """
    Central grid geometry and configuration service.

    GridSystem is deliberately independent of QGraphicsScene and
    QGraphicsItem. It provides deterministic scene-space grid
    calculations for CoordinateSystem, SnapSystem and
    RenderSystem.
    """

    # ========================================================
    # DEFAULT CONFIGURATION
    # ========================================================

    DEFAULT_MINOR_SPACING = 10.0
    DEFAULT_MAJOR_SPACING = 50.0

    DEFAULT_VISIBLE = True
    DEFAULT_MINOR_VISIBLE = True
    DEFAULT_MAJOR_VISIBLE = True

    MIN_SPACING = 1e-9

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        minor_spacing: float = DEFAULT_MINOR_SPACING,
        major_spacing: float = DEFAULT_MAJOR_SPACING,
        visible: bool = DEFAULT_VISIBLE,
        minor_visible: bool = DEFAULT_MINOR_VISIBLE,
        major_visible: bool = DEFAULT_MAJOR_VISIBLE,
    ) -> None:
        """
        Initialize the grid system.

        Parameters
        ----------
        minor_spacing:
            Distance between adjacent minor grid lines in
            scene coordinates.

        major_spacing:
            Distance between adjacent major grid lines in
            scene coordinates.

        visible:
            Global grid visibility.

        minor_visible:
            Visibility of minor grid geometry.

        major_visible:
            Visibility of major grid geometry.
        """

        self.set_minor_spacing(
            minor_spacing
        )

        self.set_major_spacing(
            major_spacing
        )

        self.visible = self._validate_bool(
            visible,
            "visible",
        )

        self.minor_visible = self._validate_bool(
            minor_visible,
            "minor_visible",
        )

        self.major_visible = self._validate_bool(
            major_visible,
            "major_visible",
        )

        self._validate_spacing_relationship()

    # ========================================================
    # SPACING
    # ========================================================

    def set_minor_spacing(
        self,
        spacing: float,
    ) -> None:
        """
        Set minor grid spacing.
        """

        spacing = self._validate_spacing(
            spacing,
            "minor_spacing",
        )

        self.minor_spacing = spacing

        if hasattr(
            self,
            "major_spacing",
        ):
            self._validate_spacing_relationship()

    # --------------------------------------------------------

    def get_minor_spacing(
        self,
    ) -> float:
        """
        Return minor grid spacing.
        """

        return self.minor_spacing

    # --------------------------------------------------------

    def set_major_spacing(
        self,
        spacing: float,
    ) -> None:
        """
        Set major grid spacing.
        """

        spacing = self._validate_spacing(
            spacing,
            "major_spacing",
        )

        self.major_spacing = spacing

        if hasattr(
            self,
            "minor_spacing",
        ):
            self._validate_spacing_relationship()

    # --------------------------------------------------------

    def get_major_spacing(
        self,
    ) -> float:
        """
        Return major grid spacing.
        """

        return self.major_spacing

    # ========================================================
    # GRID VISIBILITY
    # ========================================================

    def set_visible(
        self,
        visible: bool,
    ) -> None:
        """
        Enable or disable the complete grid.
        """

        self.visible = self._validate_bool(
            visible,
            "visible",
        )

    # --------------------------------------------------------

    def is_visible(
        self,
    ) -> bool:
        """
        Return True when the grid is globally visible.
        """

        return self.visible

    # --------------------------------------------------------

    def set_minor_visible(
        self,
        visible: bool,
    ) -> None:
        """
        Enable or disable minor grid geometry.
        """

        self.minor_visible = self._validate_bool(
            visible,
            "minor_visible",
        )

    # --------------------------------------------------------

    def is_minor_visible(
        self,
    ) -> bool:
        """
        Return True when minor grid geometry is visible.
        """

        return (
            self.visible
            and self.minor_visible
        )

    # --------------------------------------------------------

    def set_major_visible(
        self,
        visible: bool,
    ) -> None:
        """
        Enable or disable major grid geometry.
        """

        self.major_visible = self._validate_bool(
            visible,
            "major_visible",
        )

    # --------------------------------------------------------

    def is_major_visible(
        self,
    ) -> bool:
        """
        Return True when major grid geometry is visible.
        """

        return (
            self.visible
            and self.major_visible
        )

    # ========================================================
    # GRID SNAP
    # ========================================================

    def snap_point(
        self,
        point: Any,
    ) -> Any:
        """
        Resolve a scene-space point to the nearest minor-grid
        coordinate.

        Parameters
        ----------
        point:
            QPointF-compatible object providing x() and y().

        Returns
        -------
        QPointF-compatible object
            The nearest grid coordinate.

        Notes
        -----
        GridSystem performs no object snapping and no snapping
        policy decision.

        It simply resolves the supplied scene coordinate against
        the configured grid.
        """

        self._validate_point(
            point,
            "point",
        )

        x = self.snap_value(
            float(point.x()),
            self.minor_spacing,
        )

        y = self.snap_value(
            float(point.y()),
            self.minor_spacing,
        )

        return self._make_point(
            x,
            y,
        )

    # --------------------------------------------------------

    def snap_value(
        self,
        value: float,
        spacing: float | None = None,
    ) -> float:
        """
        Snap one numeric coordinate to the nearest grid
        coordinate.

        Parameters
        ----------
        value:
            Scene-space coordinate.

        spacing:
            Optional grid spacing.

            If omitted, minor spacing is used.
        """

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(
                "value must be numeric."
            )

        selected_spacing = (
            self.minor_spacing
            if spacing is None
            else self._validate_spacing(
                spacing,
                "spacing",
            )
        )

        return (
            floor(
                float(value)
                / selected_spacing
                + 0.5
            )
            * selected_spacing
        )

    # ========================================================
    # GRID INDEX
    # ========================================================

    def point_to_index(
        self,
        point: Any,
    ) -> tuple[int, int]:
        """
        Return the integer minor-grid indices containing the
        nearest grid point.
        """

        self._validate_point(
            point,
            "point",
        )

        return (
            self.value_to_index(
                float(point.x()),
                self.minor_spacing,
            ),
            self.value_to_index(
                float(point.y()),
                self.minor_spacing,
            ),
        )

    # --------------------------------------------------------

    def value_to_index(
        self,
        value: float,
        spacing: float | None = None,
    ) -> int:
        """
        Convert a coordinate to its nearest grid index.
        """

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(
                "value must be numeric."
            )

        selected_spacing = (
            self.minor_spacing
            if spacing is None
            else self._validate_spacing(
                spacing,
                "spacing",
            )
        )

        return int(
            floor(
                float(value)
                / selected_spacing
                + 0.5
            )
        )

    # --------------------------------------------------------

    def index_to_value(
        self,
        index: int,
        spacing: float | None = None,
    ) -> float:
        """
        Convert a grid index into a scene-space coordinate.
        """

        if isinstance(
            index,
            bool,
        ) or not isinstance(
            index,
            int,
        ):
            raise TypeError(
                "index must be an integer."
            )

        selected_spacing = (
            self.minor_spacing
            if spacing is None
            else self._validate_spacing(
                spacing,
                "spacing",
            )
        )

        return (
            index
            * selected_spacing
        )

    # ========================================================
    # MAJOR GRID
    # ========================================================

    def is_major_coordinate(
        self,
        value: float,
    ) -> bool:
        """
        Return True when a coordinate lies on a major-grid
        boundary.
        """

        if isinstance(
            value,
            bool,
        ) or not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(
                "value must be numeric."
            )

        index = self.value_to_index(
            float(value),
            self.major_spacing,
        )

        major_value = self.index_to_value(
            index,
            self.major_spacing,
        )

        tolerance = (
            self.major_spacing
            * 1e-9
        )

        return (
            abs(
                float(value)
                - major_value
            )
            <= tolerance
        )

    # --------------------------------------------------------

    def point_is_major(
        self,
        point: Any,
    ) -> bool:
        """
        Return True when both coordinates of a point lie on
        major-grid boundaries.
        """

        self._validate_point(
            point,
            "point",
        )

        return (
            self.is_major_coordinate(
                float(point.x())
            )
            and self.is_major_coordinate(
                float(point.y())
            )
        )

    # ========================================================
    # GRID GEOMETRY
    # ========================================================

    def get_lines(
        self,
        rect: Any,
        major: bool = False,
    ) -> tuple[tuple[float, float, float, float], ...]:
        """
        Return grid-line geometry intersecting a scene rectangle.

        Parameters
        ----------
        rect:
            QRectF-compatible rectangle providing left(), right(),
            top(), and bottom().

        major:
            When True, generate major-grid lines.
            Otherwise generate minor-grid lines.

        Returns
        -------
        tuple
            Line tuples in the form:

                (x1, y1, x2, y2)

        Notes
        -----
        This method provides geometry only.

        RenderSystem remains responsible for drawing the lines.
        """

        self._validate_rect(
            rect,
            "rect",
        )

        spacing = (
            self.major_spacing
            if major
            else self.minor_spacing
        )

        left = float(rect.left())
        right = float(rect.right())
        top = float(rect.top())
        bottom = float(rect.bottom())

        start_x = (
            floor(
                left / spacing
            )
            * spacing
        )

        start_y = (
            floor(
                top / spacing
            )
            * spacing
        )

        lines = []

        x = start_x

        while x <= right:
            lines.append(
                (
                    x,
                    top,
                    x,
                    bottom,
                )
            )
            x += spacing

        y = start_y

        while y <= bottom:
            lines.append(
                (
                    left,
                    y,
                    right,
                    y,
                )
            )
            y += spacing

        return tuple(
            lines
        )

    # --------------------------------------------------------

    def get_minor_lines(
        self,
        rect: Any,
    ) -> tuple[tuple[float, float, float, float], ...]:
        """
        Return minor-grid line geometry.
        """

        return self.get_lines(
            rect,
            major=False,
        )

    # --------------------------------------------------------

    def get_major_lines(
        self,
        rect: Any,
    ) -> tuple[tuple[float, float, float, float], ...]:
        """
        Return major-grid line geometry.
        """

        return self.get_lines(
            rect,
            major=True,
        )

    # ========================================================
    # GRID EXTENT HELPERS
    # ========================================================

    def nearest_grid_point(
        self,
        x: float,
        y: float,
    ) -> tuple[float, float]:
        """
        Return the nearest minor-grid coordinate pair.
        """

        return (
            self.snap_value(
                x
            ),
            self.snap_value(
                y
            ),
        )

    # --------------------------------------------------------

    def grid_bounds(
        self,
        rect: Any,
    ) -> tuple[float, float, float, float]:
        """
        Return the grid-aligned bounds covering a scene
        rectangle.

        Returns:

            left, top, right, bottom
        """

        self._validate_rect(
            rect,
            "rect",
        )

        left = (
            floor(
                float(rect.left())
                / self.minor_spacing
            )
            * self.minor_spacing
        )

        top = (
            floor(
                float(rect.top())
                / self.minor_spacing
            )
            * self.minor_spacing
        )

        right = (
            floor(
                float(rect.right())
                / self.minor_spacing
            )
            + 1
        ) * self.minor_spacing

        bottom = (
            floor(
                float(rect.bottom())
                / self.minor_spacing
            )
            + 1
        ) * self.minor_spacing

        return (
            left,
            top,
            right,
            bottom,
        )

    # ========================================================
    # CONFIGURATION
    # ========================================================

    def configure(
        self,
        *,
        minor_spacing: float | None = None,
        major_spacing: float | None = None,
        visible: bool | None = None,
        minor_visible: bool | None = None,
        major_visible: bool | None = None,
    ) -> None:
        """
        Update grid configuration atomically.

        Omitted values remain unchanged.
        """

        new_minor = (
            self.minor_spacing
            if minor_spacing is None
            else self._validate_spacing(
                minor_spacing,
                "minor_spacing",
            )
        )

        new_major = (
            self.major_spacing
            if major_spacing is None
            else self._validate_spacing(
                major_spacing,
                "major_spacing",
            )
        )

        self._validate_spacing_values(
            new_minor,
            new_major,
        )

        new_visible = (
            self.visible
            if visible is None
            else self._validate_bool(
                visible,
                "visible",
            )
        )

        new_minor_visible = (
            self.minor_visible
            if minor_visible is None
            else self._validate_bool(
                minor_visible,
                "minor_visible",
            )
        )

        new_major_visible = (
            self.major_visible
            if major_visible is None
            else self._validate_bool(
                major_visible,
                "major_visible",
            )
        )

        self.minor_spacing = new_minor
        self.major_spacing = new_major
        self.visible = new_visible
        self.minor_visible = new_minor_visible
        self.major_visible = new_major_visible

    # ========================================================
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic grid state.
        """

        return {
            "minor_spacing": self.minor_spacing,
            "major_spacing": self.major_spacing,
            "visible": self.visible,
            "minor_visible": self.minor_visible,
            "major_visible": self.major_visible,
        }

    # ========================================================
    # VALIDATION
    # ========================================================

    @classmethod
    def _validate_spacing(
        cls,
        spacing: float,
        name: str,
    ) -> float:
        """
        Validate a positive numeric grid spacing.
        """

        if isinstance(
            spacing,
            bool,
        ) or not isinstance(
            spacing,
            (int, float),
        ):
            raise TypeError(
                f"{name} must be numeric."
            )

        value = float(
            spacing
        )

        if value <= cls.MIN_SPACING:
            raise ValueError(
                f"{name} must be greater than "
                f"{cls.MIN_SPACING}."
            )

        return value

    # --------------------------------------------------------

    @staticmethod
    def _validate_bool(
        value: bool,
        name: str,
    ) -> bool:
        """
        Validate a boolean configuration value.
        """

        if not isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{name} must be a bool."
            )

        return value

    # --------------------------------------------------------

    def _validate_spacing_relationship(
        self,
    ) -> None:
        """
        Validate the major/minor spacing relationship.
        """

        self._validate_spacing_values(
            self.minor_spacing,
            self.major_spacing,
        )

    # --------------------------------------------------------

    @staticmethod
    def _validate_spacing_values(
        minor_spacing: float,
        major_spacing: float,
    ) -> None:
        """
        Validate a major/minor spacing pair.
        """

        if major_spacing < minor_spacing:
            raise ValueError(
                "major_spacing must be greater than "
                "or equal to minor_spacing."
            )

        ratio = (
            major_spacing
            / minor_spacing
        )

        nearest_integer = round(
            ratio
        )

        if abs(
            ratio
            - nearest_integer
        ) > 1e-9:
            raise ValueError(
                "major_spacing must be an integer multiple "
                "of minor_spacing."
            )

    # --------------------------------------------------------

    @staticmethod
    def _validate_point(
        point: Any,
        name: str,
    ) -> None:
        """
        Validate a QPointF-compatible point.
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

    # --------------------------------------------------------

    @staticmethod
    def _validate_rect(
        rect: Any,
        name: str,
    ) -> None:
        """
        Validate a QRectF-compatible rectangle.
        """

        if rect is None:
            raise ValueError(
                f"{name} must not be None."
            )

        for method_name in (
            "left",
            "right",
            "top",
            "bottom",
        ):
            if not callable(
                getattr(
                    rect,
                    method_name,
                    None,
                )
            ):
                raise TypeError(
                    f"{name} must provide "
                    f"{method_name}()."
                )

    # ========================================================
    # POINT CONSTRUCTION
    # ========================================================

    @staticmethod
    def _make_point(
        x: float,
        y: float,
    ) -> Any:
        """
        Construct a QPointF lazily through the Qt abstraction.

        GridSystem itself does not import Qt at module level.
        """

        from ui.core.qt import QPointF

        return QPointF(
            x,
            y,
        )

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
            "GridSystem("
            f"minor_spacing="
            f"{self.minor_spacing}, "
            f"major_spacing="
            f"{self.major_spacing}, "
            f"visible="
            f"{self.visible}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "GridSystem",
]
