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
#     - provide future extension point for orthogonal routing.
#
# Does NOT:
#     - create QGraphicsPathItem;
#     - render the path;
#     - validate electrical topology.
#
# ============================================================

"""
GridForge V2 — Connection Router.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


Point = Tuple[float, float]


@dataclass(frozen=True)
class ConnectionPath:
    """
    Renderer-neutral connection path.
    """

    points: tuple[Point, ...]

    @property
    def start(self) -> Point:
        return self.points[0]

    @property
    def end(self) -> Point:
        return self.points[-1]


class ConnectionRouter:
    """
    Computes logical connection geometry.

    The initial implementation uses a direct two-point route. Orthogonal,
    grid-aware and obstacle-aware routing can be added later without
    changing the connection model.
    """

    def route(
        self,
        source_position: Point,
        target_position: Point,
    ) -> ConnectionPath:
        return ConnectionPath(
            points=(
                (
                    float(source_position[0]),
                    float(source_position[1]),
                ),
                (
                    float(target_position[0]),
                    float(target_position[1]),
                ),
            )
        )
