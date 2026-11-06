# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/panel_registry.py
#
# Purpose:
#     Stores panel descriptors.
#
# Architectural Role:
#     Definition/registration layer for all V2 panels.
#
# Responsibilities:
#     - register panel descriptors;
#     - retrieve descriptors;
#     - enumerate descriptors;
#     - prevent duplicate IDs.
#
# Does NOT:
#     - create panel instances;
#     - manage visibility;
#     - create Qt docks.
#
# ============================================================

"""
GridForge V2 — Panel Registry.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from .panel_descriptor import PanelDescriptor


class PanelRegistry:
    """
    Registry of available V2 panel types.
    """

    def __init__(self) -> None:
        self._descriptors: Dict[
            str,
            PanelDescriptor,
        ] = {}

    def register(
        self,
        descriptor: PanelDescriptor,
    ) -> None:
        if descriptor.panel_id in self._descriptors:
            raise ValueError(
                f"Panel already registered: "
                f"{descriptor.panel_id}"
            )

        self._descriptors[
            descriptor.panel_id
        ] = descriptor

    def unregister(
        self,
        panel_id: str,
    ) -> PanelDescriptor:
        descriptor = self._descriptors.pop(
            panel_id,
            None,
        )

        if descriptor is None:
            raise KeyError(panel_id)

        return descriptor

    def get(
        self,
        panel_id: str,
    ) -> Optional[PanelDescriptor]:
        return self._descriptors.get(
            panel_id
        )

    def require(
        self,
        panel_id: str,
    ) -> PanelDescriptor:
        descriptor = self.get(panel_id)

        if descriptor is None:
            raise KeyError(panel_id)

        return descriptor

    def descriptors(
        self,
    ) -> Iterable[PanelDescriptor]:
        return tuple(
            self._descriptors.values()
        )

    def clear(self) -> None:
        self._descriptors.clear()

    def __len__(self) -> int:
        return len(self._descriptors)
