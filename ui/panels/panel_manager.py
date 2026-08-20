# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/panel_manager.py
#
# Purpose:
#     Controls runtime panel instances.
#
# Architectural Role:
#     Runtime lifecycle manager between panel registry and the
#     eventual Qt docking layer.
#
# Responsibilities:
#     - instantiate panels;
#     - show/hide panels;
#     - activate/deactivate panels;
#     - destroy panels;
#     - query runtime panel state.
#
# Does NOT:
#     - construct QDockWidget;
#     - manipulate MainWindow;
#     - perform rendering.
#
# ============================================================

"""
GridForge V2 — Panel Manager.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from .panel_instance import PanelInstance
from .panel_registry import PanelRegistry


class PanelManager:
    """
    Runtime lifecycle manager for V2 panels.
    """

    def __init__(
        self,
        registry: PanelRegistry,
    ) -> None:
        if registry is None:
            raise ValueError(
                "registry must not be None"
            )

        self._registry = registry

        self._instances: Dict[
            str,
            PanelInstance,
        ] = {}

        self._active_panel_id: Optional[
            str
        ] = None

    @property
    def active_panel_id(self) -> Optional[str]:
        return self._active_panel_id

    @property
    def active_panel(
        self,
    ) -> Optional[PanelInstance]:
        if self._active_panel_id is None:
            return None

        return self._instances.get(
            self._active_panel_id
        )

    def create(
        self,
        panel_id: str,
    ) -> PanelInstance:
        existing = self._instances.get(
            panel_id
        )

        if existing is not None:
            return existing

        descriptor = self._registry.require(
            panel_id
        )

        panel = descriptor.factory()

        instance = PanelInstance(
            descriptor,
            panel,
        )

        instance.create()

        self._instances[
            panel_id
        ] = instance

        return instance

    def show(
        self,
        panel_id: str,
    ) -> PanelInstance:
        instance = self.create(panel_id)
        instance.show()
        return instance

    def hide(
        self,
        panel_id: str,
    ) -> PanelInstance:
        instance = self.require(panel_id)
        instance.hide()
        return instance

    def activate(
        self,
        panel_id: str,
    ) -> PanelInstance:
        instance = self.create(panel_id)

        if (
            self._active_panel_id is not None
            and self._active_panel_id != panel_id
        ):
            previous = self._instances.get(
                self._active_panel_id
            )

            if previous is not None:
                previous.deactivate()

        instance.activate()

        self._active_panel_id = panel_id

        return instance

    def destroy(
        self,
        panel_id: str,
    ) -> PanelInstance:
        instance = self.require(panel_id)

        instance.destroy()

        del self._instances[
            panel_id
        ]

        if self._active_panel_id == panel_id:
            self._active_panel_id = None

        return instance

    def get(
        self,
        panel_id: str,
    ) -> Optional[PanelInstance]:
        return self._instances.get(
            panel_id
        )

    def require(
        self,
        panel_id: str,
    ) -> PanelInstance:
        instance = self.get(panel_id)

        if instance is None:
            raise KeyError(panel_id)

        return instance

    def instances(
        self,
    ) -> Iterable[PanelInstance]:
        return tuple(
            self._instances.values()
        )

    def clear(self) -> None:
        for instance in self._instances.values():
            instance.destroy()

        self._instances.clear()
        self._active_panel_id = None

    def __len__(self) -> int:
        return len(self._instances)
