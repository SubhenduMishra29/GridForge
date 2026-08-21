# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/panel_state.py
#
# Purpose:
#     Stores runtime logical state for a panel.
#
# Architectural Role:
#     Keeps panel lifecycle state independent from Qt widgets
#     and independent from Workspace placement.
#
# Responsibilities:
#     - visibility;
#     - active state;
#     - serialization of lifecycle state.
#
# Does NOT:
#     - define dock area;
#     - define floating placement;
#     - define workspace geometry;
#     - perform docking;
#     - manipulate Qt widgets.
#
# Workspace placement ownership
# -----------------------------
#
# WorkspacePlacement / WorkspaceLayout own:
#
#     - area;
#     - visibility as workspace placement;
#     - group;
#     - ordering;
#     - floating placement;
#     - layout-specific placement data.
#
# PanelState represents runtime panel lifecycle state after
# creation/activation, not workspace policy.
#
# ============================================================

"""
GridForge V2 — Panel State.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PanelState:
    """
    Runtime logical state of a panel.

    This state deliberately contains no workspace placement.
    """

    visible: bool = True

    active: bool = False

    def show(self) -> None:
        """Mark the panel as visible."""
        self.visible = True

    def hide(self) -> None:
        """
        Mark the panel as hidden.

        A hidden panel cannot remain active.
        """
        self.visible = False
        self.active = False

    def activate(self) -> None:
        """
        Activate the panel.

        Activation implies visibility at the lifecycle level.
        """
        self.visible = True
        self.active = True

    def deactivate(self) -> None:
        """Deactivate the panel."""
        self.active = False

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize runtime lifecycle state.
        """
        return {
            "visible": self.visible,
            "active": self.active,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "PanelState":
        """
        Restore runtime lifecycle state.

        Missing values use the canonical defaults.
        """

        if not isinstance(data, dict):
            raise TypeError(
                "data must be a dictionary"
            )

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
        )
