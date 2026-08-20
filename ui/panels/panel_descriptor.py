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
#     - panel area;
#     - singleton behavior;
#     - default visibility;
#     - factory function.
#
# Does NOT:
#     - construct Qt widgets;
#     - own panel state;
#     - render content.
#
# ============================================================

"""
GridForge V2 — Panel Descriptor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from .panel_base import PanelBase


PanelFactory = Callable[[], PanelBase]


@dataclass(frozen=True)
class PanelDescriptor:
    """
    Registration metadata for a panel.
    """

    panel_id: str
    title: str

    factory: PanelFactory

    area: str = "right"

    singleton: bool = True

    visible_by_default: bool = True

    closable: bool = True

    movable: bool = True

    floatable: bool = True

    def __post_init__(self) -> None:
        if not self.panel_id:
            raise ValueError(
                "panel_id must not be empty"
            )

        if not self.title:
            raise ValueError(
                "title must not be empty"
            )

        if not callable(self.factory):
            raise TypeError(
                "factory must be callable"
            )

        if not self.area:
            raise ValueError(
                "area must not be empty"
            )
