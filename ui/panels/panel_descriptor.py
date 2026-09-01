# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/panel_descriptor.py
#
# Author:
#     Subhendu Mishra
#
# Purpose:
#     Describes a panel before the panel is instantiated.
#
# Architectural Role:
#     Separates immutable panel registration metadata from runtime
#     panel instances. PanelFactory is intentionally a callable type
#     contract, not a separate factory subsystem.
#
# Responsibilities:
#     - stable panel ID;
#     - title;
#     - factory callable contract;
#     - singleton behavior;
#     - default visibility;
#     - presentation capabilities.
#
# Does NOT:
#     - define canonical workspace placement;
#     - own dock area or workspace layout;
#     - construct Qt widgets;
#     - own runtime panel state;
#     - instantiate panels itself;
#     - render content.
#
# Runtime construction boundary:
#
#     PanelRegistry
#         -> PanelManager.create()
#         -> descriptor.factory()
#         -> PanelInstance
#         -> PanelBase
#
# PanelFactory is therefore only the callable contract used by the
# descriptor. A separate ui/panels/panel_factory.py implementation is
# deliberately not part of the architecture.
#
# Placement ownership:
#     WorkspacePlacement / WorkspaceLayout own area, visibility in a
#     workspace, grouping, ordering, and floating placement.
#
# ============================================================

"""GridForge V2 — panel registration descriptor."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .panel_base import PanelBase


# Factory contract only. Runtime invocation belongs to PanelManager.
PanelFactory = Callable[[], PanelBase]


@dataclass(frozen=True)
class PanelDescriptor:
    """Immutable registration metadata for a panel."""

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
            raise TypeError("panel_id must be a string")
        if not self.panel_id.strip():
            raise ValueError("panel_id must not be empty")
        if not isinstance(self.title, str):
            raise TypeError("title must be a string")
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if not callable(self.factory):
            raise TypeError("factory must be callable")
