# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/workspace/viewport_state.py
#
# Purpose:
#     Persistent logical state describing a canvas viewport.
#
# Architectural Role:
#     Keeps viewport state outside QGraphicsView so that viewport
#     state can be restored, serialized and transferred between
#     views.
#
# Responsibilities:
#     - zoom;
#     - center;
#     - rotation;
#     - grid visibility;
#     - snap visibility;
#     - viewport serialization.
#
# Does NOT:
#     - manipulate QGraphicsView directly;
#     - perform coordinate conversion;
#     - render the canvas.
#
# ============================================================

"""
GridForge V2 — Viewport State.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class ViewportState:
    """
    Logical viewport configuration.

    The values are intentionally toolkit-independent.
    """

    center_x: float = 0.0
    center_y: float = 0.0

    zoom: float = 1.0

    rotation: float = 0.0

    grid_visible: bool = True
    snap_visible: bool = True

    def __post_init__(self) -> None:
        if self.zoom <= 0.0:
            raise ValueError(
                "zoom must be greater than zero"
            )

        self.center_x = float(
            self.center_x
        )
        self.center_y = float(
            self.center_y
        )
        self.zoom = float(self.zoom)
        self.rotation = float(
            self.rotation
        )

    def set_center(
        self,
        x: float,
        y: float,
    ) -> None:
        self.center_x = float(x)
        self.center_y = float(y)

    def set_zoom(
        self,
        zoom: float,
    ) -> None:
        if zoom <= 0.0:
            raise ValueError(
                "zoom must be greater than zero"
            )

        self.zoom = float(zoom)

    def reset(self) -> None:
        self.center_x = 0.0
        self.center_y = 0.0
        self.zoom = 1.0
        self.rotation = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "center_x": self.center_x,
            "center_y": self.center_y,
            "zoom": self.zoom,
            "rotation": self.rotation,
            "grid_visible": self.grid_visible,
            "snap_visible": self.snap_visible,
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> "ViewportState":
        return cls(
            center_x=float(
                data.get(
                    "center_x",
                    0.0,
                )
            ),
            center_y=float(
                data.get(
                    "center_y",
                    0.0,
                )
            ),
            zoom=float(
                data.get(
                    "zoom",
                    1.0,
                )
            ),
            rotation=float(
                data.get(
                    "rotation",
                    0.0,
                )
            ),
            grid_visible=bool(
                data.get(
                    "grid_visible",
                    True,
                )
            ),
            snap_visible=bool(
                data.get(
                    "snap_visible",
                    True,
                )
            ),
        )
