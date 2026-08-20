# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/connections/connection_router.py
#
# Purpose:
#     Calculates renderer-neutral visual paths between SLD
#     terminals.
#
# Architectural Role:
#     Separates connection geometry/routing from LineItem and
#     LineRenderer.
#
# Responsibilities:
#     - calculate direct routes;
#     - provide routing points;
#     - validate routing coordinates;
#     - provide a future extension point for orthogonal routing.
#
# Does NOT:
#     - create QGraphicsPathItem;
#     - render the path;
#     - validate electrical topology;
#     - resolve terminals;
#     - modify Core state.
#
# ============================================================

"""
GridForge V2 — Connection Router.
"""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Real
from typing import TypeAlias


Point: TypeAlias = tuple[float, float]


def _validate_point(
    point: object,
    *,
    name: str,
) -> Point:
    """
    Validate and normalize a routing point.

    A point must contain exactly two real numeric coordinates.

    bool is deliberately rejected because bool is a subclass of int
    but is not a meaningful graphical coordinate.
    """

    if isinstance(point, (str, bytes)):
        raise TypeError(
            f"{name} must be a 2D numeric point."
        )

    if not isinstance(point, (tuple, list)):
        raise TypeError(
            f"{name} must be a tuple or list of two numeric values."
        )

    if len(point) != 2:
        raise ValueError(
            f"{name} must contain exactly two coordinates."
        )

    x, y = point

    if isinstance(x, bool) or not isinstance(x, Real):
        raise TypeError(
            f"{name}[0] must be a real number."
        )

    if isinstance(y, bool) or not isinstance(y, Real):
        raise TypeError(
            f"{name}[1] must be a real number."
        )

    return (
        float(x),
        float(y),
    )


@dataclass(frozen=True)
class ConnectionPath:
    """
    Renderer-neutral connection path.

    A valid path contains at least two points:

        start → end

    Intermediate points are supported so that future routing
    strategies can produce orthogonal or obstacle-aware paths
    without changing the public path representation.
    """

    points: tuple[Point, ...]

    def __post_init__(self) -> None:
        if not isinstance(
            self.points,
            tuple,
        ):
            raise TypeError(
                "points must be a tuple of points."
            )

        if len(self.points) < 2:
            raise ValueError(
                "A connection path must contain at least "
                "two points."
            )

        normalized: list[Point] = []

        for index, point in enumerate(self.points):
            normalized.append(
                _validate_point(
                    point,
                    name=f"points[{index}]",
                )
            )

        object.__setattr__(
            self,
            "points",
            tuple(normalized),
        )

    @property
    def start(self) -> Point:
        """Return the first routing point."""

        return self.points[0]

    @property
    def end(self) -> Point:
        """Return the final routing point."""

        return self.points[-1]


class ConnectionRouter:
    """
    Computes renderer-neutral connection geometry.

    The initial implementation uses a direct two-point route.

    Future implementations may provide:

        - orthogonal routing;
        - grid-aware routing;
        - obstacle-aware routing;
        - terminal-direction-aware routing.

    Those strategies remain presentation geometry concerns and
    must not perform electrical topology validation.
    """

    def route(
        self,
        source_position: Point,
        target_position: Point,
    ) -> ConnectionPath:
        """
        Calculate a direct route between two positions.

        Parameters
        ----------
        source_position:
            Source terminal position as ``(x, y)``.

        target_position:
            Target terminal position as ``(x, y)``.

        Returns
        -------
        ConnectionPath
            A renderer-neutral two-point path.
        """

        source = _validate_point(
            source_position,
            name="source_position",
        )

        target = _validate_point(
            target_position,
            name="target_position",
        )

        return ConnectionPath(
            points=(
                source,
                target,
            )
        )


__all__ = [
    "ConnectionPath",
    "ConnectionRouter",
    "Point",
]
