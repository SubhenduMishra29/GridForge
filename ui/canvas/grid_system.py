# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/canvas/grid_system.py
#
# Purpose:
#     Centralized visual grid geometry service for the GridForge
#     SLD canvas.
#
# Architectural Role:
#     GridSystem is the authoritative owner of canvas-grid
#     geometry and grid presentation configuration.
#
# Detailed Working:
#
#     Mouse / Tool Position
#             |
#             v
#     CoordinateSystem
#             |
#             v
#        scene position
#             |
#             v
#        GridSystem
#          /      \
#         v        v
#      grid      geometry
#      resolve      |
#         |         |
#         v         v
#     Coordinate  RenderSystem
#     / SnapSystem
#
# GridSystem owns:
#     - minor grid spacing;
#     - major grid spacing;
#     - grid visibility;
#     - major/minor visibility;
#     - scene-space grid resolution;
#     - grid index conversion;
#     - major-grid detection;
#     - grid-line geometry;
#     - grid-aligned bounds;
#     - diagnostic configuration state.
#
# GridSystem does NOT:
#     - create QGraphicsItem objects;
#     - render the grid;
#     - own QGraphicsScene;
#     - own QGraphicsView;
#     - perform object snapping;
#     - perform terminal snapping;
#     - manage selection;
#     - manage tools;
#     - manage navigation;
#     - modify Core state;
#     - perform electrical calculations;
#     - perform engineering-unit conversion.
#
# Snapping Boundary:
#
#     GridSystem
#          |
#          | geometric grid resolution only
#          v
#     CoordinateSystem
#
#     Tool
#       |
#       v
#     SnapSystem
#       |
#       +-- terminal snapping
#       +-- object snapping
#       +-- bus snapping
#       +-- grid snapping policy
#
# Therefore GridSystem does NOT decide whether a point should
# snap. It only knows how to resolve a coordinate to the grid.
#
# Rendering Boundary:
#
#     GridSystem
#          |
#          | geometry/configuration
#          v
#     RenderSystem
#          |
#          v
#       Canvas
#
# Qt Boundary:
#
#     GridSystem has no module-level Qt import.
#
#     When a QPointF must be created, it is obtained through:
#
#         ui.core.qt
#
# This preserves the GridForge Qt abstraction boundary.
#
# Coordinate Convention:
#
#     All grid geometry is expressed in SCENE coordinates.
#
#     GridSystem has no knowledge of viewport coordinates.
#
# Numerical Policy:
#
#     Grid indices are calculated from integer arithmetic derived
#     from floating-point coordinates. Grid-line positions are
#     reconstructed from:
#
#         index * spacing
#
#     rather than repeatedly adding spacing.
#
#     This prevents cumulative floating-point drift.
#
# ============================================================

"""
GridForge V2 — Canvas Grid System.

Qt-independent grid geometry and configuration service.
"""

from __future__ import annotations

from math import ceil, floor, isfinite
from typing import Any


class GridSystem:
    """
    Central grid geometry and configuration service.

    GridSystem is deliberately independent of QGraphicsScene,
    QGraphicsView and QGraphicsItem.

    It provides deterministic scene-space grid calculations for:

        - CoordinateSystem;
        - SnapSystem;
        - RenderSystem;
        - canvas diagnostics.
    """

    # ========================================================
    # DEFAULT CONFIGURATION
    # ========================================================

    DEFAULT_MINOR_SPACING = 10.0
    DEFAULT_MAJOR_SPACING = 50.0

    DEFAULT_VISIBLE = True
    DEFAULT_MINOR_VISIBLE = True
    DEFAULT_MAJOR_VISIBLE = True

    # Smallest permitted positive grid spacing.
    MIN_SPACING = 1e-9

    # Numerical tolerance used for floating-point comparisons.
    NUMERICAL_TOLERANCE = 1e-9

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
            Minor-grid presentation flag.

        major_visible:
            Major-grid presentation flag.

        Validation is completed before the object enters a valid
        runtime state.
        """

        validated_minor = self._validate_spacing(
            minor_spacing,
            "minor_spacing",
        )

        validated_major = self._validate_spacing(
            major_spacing,
            "major_spacing",
        )

        self._validate_spacing_values(
            validated_minor,
            validated_major,
        )

        self.minor_spacing = validated_minor
        self.major_spacing = validated_major

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

    # ========================================================
    # SPACING
    # ========================================================

    def set_minor_spacing(
        self,
        spacing: float,
    ) -> None:
        """
        Change the minor-grid spacing.

        The existing major spacing must remain an integer
        multiple of the new minor spacing.

        No partial state update occurs if validation fails.
        """

        validated = self._validate_spacing(
            spacing,
            "minor_spacing",
        )

        self._validate_spacing_values(
            validated,
            self.major_spacing,
        )

        self.minor_spacing = validated

    # --------------------------------------------------------

    def get_minor_spacing(
        self,
    ) -> float:
        """
        Return the current minor-grid spacing.
        """

        return self.minor_spacing

    # --------------------------------------------------------

    def set_major_spacing(
        self,
        spacing: float,
    ) -> None:
        """
        Change the major-grid spacing.

        Major spacing must:

            - be positive;
            - be >= minor spacing;
            - be an integer multiple of minor spacing.
        """

        validated = self._validate_spacing(
            spacing,
            "major_spacing",
        )

        self._validate_spacing_values(
            self.minor_spacing,
            validated,
        )

        self.major_spacing = validated

    # --------------------------------------------------------

    def get_major_spacing(
        self,
    ) -> float:
        """
        Return the current major-grid spacing.
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
        Return True when the complete grid is enabled.
        """

        return self.visible

    # --------------------------------------------------------

    def set_minor_visible(
        self,
        visible: bool,
    ) -> None:
        """
        Enable or disable minor-grid presentation.
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
        Return True when minor-grid presentation is enabled.

        Global visibility is also considered.
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
        Enable or disable major-grid presentation.
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
        Return True when major-grid presentation is enabled.

        Global visibility is also considered.
        """

        return (
            self.visible
            and self.major_visible
        )

    # ========================================================
    # GRID SNAP / RESOLUTION
    # ========================================================

    def snap_point(
        self,
        point: Any,
    ) -> Any:
        """
        Resolve a scene-space point to the nearest minor-grid
        coordinate.

        IMPORTANT:
            This is geometric resolution only.

        GridSystem does not know:

            - snap tolerance;
            - selected objects;
            - terminal priority;
            - bus priority;
            - connection policy.

        Those responsibilities belong to SnapSystem.
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
        Snap one coordinate to the nearest grid coordinate.

        Rounding is deterministic and symmetric around zero.

        Example, spacing = 10:

            +4.9  ->   0
            +5.0  ->  10
            +5.1  ->  10

            -4.9  ->   0
            -5.0  -> -10
            -5.1  -> -10

        This avoids Python's banker-rounding behavior and gives
        explicit engineering/CAD-style half-grid behavior.
        """

        self._validate_numeric(
            value,
            "value",
        )

        selected_spacing = (
            self.minor_spacing
            if spacing is None
            else self._validate_spacing(
                spacing,
                "spacing",
            )
        )

        quotient = (
            float(value)
            / selected_spacing
        )

        if quotient >= 0.0:
            index = floor(
                quotient + 0.5
            )
        else:
            index = -floor(
                -quotient + 0.5
            )

        return (
            index
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
        Convert a scene-space point to its nearest minor-grid
        integer index.
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
        Convert a coordinate to the nearest integer grid index.

        The rounding policy is identical to snap_value().
        """

        self._validate_numeric(
            value,
            "value",
        )

        selected_spacing = (
            self.minor_spacing
            if spacing is None
            else self._validate_spacing(
                spacing,
                "spacing",
            )
        )

        quotient = (
            float(value)
            / selected_spacing
        )

        if quotient >= 0.0:
            return int(
                floor(
                    quotient + 0.5
                )
            )

        return int(
            -floor(
                -quotient + 0.5
            )
        )

    # --------------------------------------------------------

    def index_to_value(
        self,
        index: int,
        spacing: float | None = None,
    ) -> float:
        """
        Convert an integer grid index to scene coordinates.
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
        Return True when a coordinate lies on a major-grid line.

        The calculation is based on the major spacing directly.
        """

        self._validate_numeric(
            value,
            "value",
        )

        index = self.value_to_index(
            value,
            self.major_spacing,
        )

        major_value = self.index_to_value(
            index,
            self.major_spacing,
        )

        tolerance = max(
            self.NUMERICAL_TOLERANCE,
            abs(self.major_spacing)
            * self.NUMERICAL_TOLERANCE,
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
        Return True when both point coordinates lie on
        major-grid lines.
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
    # GRID LINE GEOMETRY
    # ========================================================

    def get_lines(
        self,
        rect: Any,
        major: bool = False,
    ) -> tuple[
        tuple[float, float, float, float],
        ...,
    ]:
        """
        Return grid-line geometry covering a scene rectangle.

        Parameters
        ----------
        rect:
            QRectF-compatible rectangle.

        major:
            False -> minor grid.
            True  -> major grid.

        Returns
        -------
        tuple
            Line tuples:

                (x1, y1, x2, y2)

        Implementation detail
        ---------------------
        Grid positions are reconstructed from integer indices:

            coordinate = index * spacing

        rather than repeatedly adding spacing.

        This avoids cumulative floating-point drift.
        """

        self._validate_rect(
            rect,
            "rect",
        )

        if not isinstance(
            major,
            bool,
        ):
            raise TypeError(
                "major must be a bool."
            )

        spacing = (
            self.major_spacing
            if major
            else self.minor_spacing
        )

        left = float(
            rect.left()
        )

        right = float(
            rect.right()
        )

        top = float(
            rect.top()
        )

        bottom = float(
            rect.bottom()
        )

        if left > right:
            left, right = right, left

        if top > bottom:
            top, bottom = bottom, top

        # ----------------------------------------------------
        # ceil() on the ending coordinate means that a grid
        # line exactly on the rectangle boundary is included,
        # while no line outside the rectangle is unnecessarily
        # generated.
        # ----------------------------------------------------

        start_x = ceil(
            left / spacing
        )

        end_x = floor(
            right / spacing
        )

        start_y = ceil(
            top / spacing
        )

        end_y = floor(
            bottom / spacing
        )

        lines: list[
            tuple[float, float, float, float]
        ] = []

        # ----------------------------------------------------
        # Vertical grid lines.
        # ----------------------------------------------------

        for index in range(
            start_x,
            end_x + 1,
        ):
            x = (
                index
                * spacing
            )

            lines.append(
                (
                    x,
                    top,
                    x,
                    bottom,
                )
            )

        # ----------------------------------------------------
        # Horizontal grid lines.
        # ----------------------------------------------------

        for index in range(
            start_y,
            end_y + 1,
        ):
            y = (
                index
                * spacing
            )

            lines.append(
                (
                    left,
                    y,
                    right,
                    y,
                )
            )

        return tuple(
            lines
        )

    # --------------------------------------------------------

    def get_minor_lines(
        self,
        rect: Any,
    ) -> tuple[
        tuple[float, float, float, float],
        ...,
    ]:
        """
        Return minor-grid geometry.
        """

        return self.get_lines(
            rect,
            major=False,
        )

    # --------------------------------------------------------

    def get_major_lines(
        self,
        rect: Any,
    ) -> tuple[
        tuple[float, float, float, float],
        ...,
    ]:
        """
        Return major-grid geometry.
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

        self._validate_numeric(
            x,
            "x",
        )

        self._validate_numeric(
            y,
            "y",
        )

        return (
            self.snap_value(x),
            self.snap_value(y),
        )

    # --------------------------------------------------------

    def grid_bounds(
        self,
        rect: Any,
    ) -> tuple[
        float,
        float,
        float,
        float,
    ]:
        """
        Return grid-aligned bounds covering a scene rectangle.

        Returns:

            left, top, right, bottom

        The bounds are the smallest grid-aligned rectangle that
        contains the supplied rectangle.

        Example, spacing = 10:

            input:
                left=3, right=97

            output:
                left=0, right=100

        If a boundary is already aligned, it is preserved rather
        than unnecessarily expanding by one grid cell.
        """

        self._validate_rect(
            rect,
            "rect",
        )

        left = float(
            rect.left()
        )

        right = float(
            rect.right()
        )

        top = float(
            rect.top()
        )

        bottom = float(
            rect.bottom()
        )

        if left > right:
            left, right = right, left

        if top > bottom:
            top, bottom = bottom, top

        left_index = floor(
            left / self.minor_spacing
        )

        right_index = ceil(
            right / self.minor_spacing
        )

        top_index = floor(
            top / self.minor_spacing
        )

        bottom_index = ceil(
            bottom / self.minor_spacing
        )

        aligned_left = (
            left_index
            * self.minor_spacing
        )

        aligned_right = (
            right_index
            * self.minor_spacing
        )

        aligned_top = (
            top_index
            * self.minor_spacing
        )

        aligned_bottom = (
            bottom_index
            * self.minor_spacing
        )

        return (
            aligned_left,
            aligned_top,
            aligned_right,
            aligned_bottom,
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

        All supplied values are validated before any state is
        modified.

        Therefore a failed configuration request leaves the
        existing GridSystem completely unchanged.
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

        # ----------------------------------------------------
        # Commit only after complete validation.
        # ----------------------------------------------------

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
        Return diagnostic grid configuration.

        This is diagnostic state only. It is not Core electrical
        model state.
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
        Validate a finite positive grid spacing.
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

        if not isfinite(value):
            raise ValueError(
                f"{name} must be finite."
            )

        if value <= cls.MIN_SPACING:
            raise ValueError(
                f"{name} must be greater than "
                f"{cls.MIN_SPACING}."
            )

        return value

    # --------------------------------------------------------

    @staticmethod
    def _validate_numeric(
        value: Any,
        name: str,
    ) -> None:
        """
        Validate a finite scalar numeric value.

        bool is explicitly rejected because bool is a subclass
        of int in Python.
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

        if not isfinite(
            float(value)
        ):
            raise ValueError(
                f"{name} must be finite."
            )

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

    @classmethod
    def _validate_spacing_values(
        cls,
        minor_spacing: float,
        major_spacing: float,
    ) -> None:
        """
        Validate the major/minor spacing relationship.

        Required invariant:

            major >= minor

        and:

            major / minor == integer
        """

        minor = cls._validate_spacing(
            minor_spacing,
            "minor_spacing",
        )

        major = cls._validate_spacing(
            major_spacing,
            "major_spacing",
        )

        if major < minor:
            raise ValueError(
                "major_spacing must be greater than "
                "or equal to minor_spacing."
            )

        ratio = (
            major / minor
        )

        nearest_integer = round(
            ratio
        )

        if abs(
            ratio - nearest_integer
        ) > cls.NUMERICAL_TOLERANCE:
            raise ValueError(
                "major_spacing must be an integer multiple "
                "of minor_spacing."
            )

    # --------------------------------------------------------

    def _validate_spacing_relationship(
        self,
    ) -> None:
        """
        Validate the current spacing invariant.

        This helper is useful for diagnostics and future
        configuration extensions.
        """

        self._validate_spacing_values(
            self.minor_spacing,
            self.major_spacing,
        )

    # --------------------------------------------------------

    @staticmethod
    def _validate_point(
        point: Any,
        name: str,
    ) -> None:
        """
        Validate a QPoint/QPointF-compatible point.

        The point must expose callable x() and y() methods.
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

        # Validate the actual coordinate values as well.
        GridSystem._validate_numeric(
            float(point.x()),
            f"{name}.x",
        )

        GridSystem._validate_numeric(
            float(point.y()),
            f"{name}.y",
        )

    # --------------------------------------------------------

    @staticmethod
    def _validate_rect(
        rect: Any,
        name: str,
    ) -> None:
        """
        Validate a QRectF-compatible rectangle.

        Required interface:

            left()
            right()
            top()
            bottom()
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

        for method_name in (
            "left",
            "right",
            "top",
            "bottom",
        ):
            GridSystem._validate_numeric(
                float(
                    getattr(rect, method_name)()
                ),
                f"{name}.{method_name}",
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
        Construct a QPointF through the GridForge Qt boundary.

        The import remains local intentionally.

        GridSystem therefore does not establish a module-level
        dependency on PySide6/PyQt.
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
