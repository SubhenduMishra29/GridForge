# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/panel_descriptor.py
#
# Purpose:
#     Describes a panel before the panel is instantiated.
#
# Architectural Role:
#     Separates panel registration metadata from runtime panel
#     instances.
#
# Responsibilities:
#     - stable panel ID;
#     - title;
#     - factory function;
#     - singleton behavior;
#     - default visibility;
#     - Qt presentation capabilities.
#
# Does NOT:
#     - define canonical workspace placement;
#     - own dock area;
#     - own workspace layout;
#     - construct Qt widgets;
#     - own runtime panel state;
#     - render content.
#
# Placement ownership
# -------------------
#
# WorkspacePlacement / WorkspaceLayout own:
#
#     - area;
#     - visibility in a workspace;
#     - grouping;
#     - ordering;
#     - floating placement.
#
# PanelDescriptor may describe whether a panel is capable of
# being moved, closed, or floated, but it does not decide where
# the panel is placed.
#
# ============================================================

"""
GridForge V2 — Panel Descriptor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .panel_base import PanelBase


PanelFactory = Callable[[], PanelBase]


@dataclass(frozen=True)
class PanelDescriptor:
    """
    Registration metadata for a panel.

    PanelDescriptor describes the panel itself.

    It deliberately does not contain workspace placement
    information. Active placement belongs to WorkspaceLayout.
    """

    panel_id: str

    title: str

    factory: PanelFactory

    singleton: bool = True

    visible_by_default: bool = True

    closable: bool = True

    movable: bool = True

    floatable: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.panel_id, str):
            raise TypeError(
                "panel_id must be a string"
            )

        if not self.panel_id.strip():
            raise ValueError(
                "panel_id must not be empty"
            )

        if not isinstance(self.title, str):
            raise TypeError(
                "title must be a string"
            )

        if not self.title.strip():
            raise ValueError(
                "title must not be empty"
            )

        if not callable(self.factory):
            raise TypeError(
                "factory must be callable"
            )
