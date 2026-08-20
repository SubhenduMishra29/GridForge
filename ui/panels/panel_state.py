# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/panel_state.py
#
# Purpose:
#     Stores persistent logical state for a panel.
#
# Architectural Role:
#     Keeps panel state independent from the actual Qt dock widget.
#
# Responsibilities:
#     - visibility;
#     - active state;
#     - floating state;
#     - dock area;
#     - geometry metadata;
#     - serialization.
#
# Does NOT:
#     - manipulate Qt widgets;
#     - perform docking itself.
#
# ============================================================

"""
GridForge V2 — Panel State.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class PanelState:
    """
    Persistent logical panel state.
    """

    visible: bool = True

    active: bool = False

    floating: bool = False

    area: str = "right"

    geometry: Dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.area:
            raise ValueError(
                "area must not be empty"
            )

        if self.geometry is None:
            self.geometry = {}

    def show(self) -> None:
        self.visible = True

    def hide(self) -> None:
        self.visible = False
        self.active = False

    def activate(self) -> None:
        self.visible = True
        self.active = True

    def deactivate(self) -> None:
        self.active = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "visible": self.visible,
            "active": self.active,
            "floating": self.floating,
            "area": self.area,
            "geometry": dict(
                self.geometry or {}
            ),
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> "PanelState":
        return cls(
            visible=bool(
                data.get(
                    "visible",
                    True,
                )
            ),
            active=bool(
                data.get(
                    "active",
                    False,
                )
            ),
            floating=bool(
                data.get(
                    "floating",
                    False,
                )
            ),
            area=str(
                data.get(
                    "area",
                    "right",
                )
            ),
            geometry=dict(
                data.get(
                    "geometry",
                    {},
                )
            ),
        )
