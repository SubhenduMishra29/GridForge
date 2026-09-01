# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/panels/panel_manager.py
#
# Author:
#     Subhendu Mishra
#
# Purpose:
#     Controls runtime panel instances.
#
# Architectural Role:
#     Runtime lifecycle manager between PanelRegistry and the
#     eventual workspace / Qt presentation layer.
#
# Responsibilities:
#     - instantiate panels through PanelDescriptor.factory;
#     - maintain runtime PanelInstance objects;
#     - show/hide panels;
#     - activate/deactivate panels;
#     - destroy panels;
#     - query runtime panel state.
#
# Does NOT:
#     - implement a separate factory subsystem;
#     - construct QDockWidget;
#     - manipulate MainWindow;
#     - own workspace placement or layout;
#     - own Project / Document / Core state;
#     - perform rendering.
#
# Construction boundary:
#     PanelRegistry
#         -> PanelDescriptor
#         -> descriptor.factory()
#         -> PanelInstance
#
# PanelFactory is only the callable contract declared by
# PanelDescriptor. PanelManager is the single runtime owner that
# invokes that contract.
# ============================================================

"""GridForge V2 — runtime panel lifecycle manager."""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from .panel_instance import PanelInstance
from .panel_registry import PanelRegistry


class PanelManager:
    """Manage runtime panel instances without owning their placement."""

    def __init__(self, registry: PanelRegistry) -> None:
        if registry is None:
            raise ValueError("registry must not be None")

        self._registry = registry
        self._instances: Dict[str, PanelInstance] = {}
        self._active_panel_id: Optional[str] = None

    @property
    def active_panel_id(self) -> Optional[str]:
        """Return the currently active panel ID, if any."""
        return self._active_panel_id

    @property
    def active_panel(self) -> Optional[PanelInstance]:
        """Return the currently active runtime instance, if any."""
        if self._active_panel_id is None:
            return None
        return self._instances.get(self._active_panel_id)

    def create(self, panel_id: str) -> PanelInstance:
        """Create and register one runtime panel instance.

        The descriptor's callable factory is the only construction
        mechanism. PanelManager does not know concrete panel classes.
        """
        existing = self._instances.get(panel_id)
        if existing is not None:
            return existing

        descriptor = self._registry.require(panel_id)
        panel = descriptor.factory()

        instance = PanelInstance(descriptor, panel)
        instance.create()
        self._instances[panel_id] = instance
        return instance

    def show(self, panel_id: str) -> PanelInstance:
        """Create if necessary and show a panel."""
        instance = self.create(panel_id)
        instance.show()
        return instance

    def hide(self, panel_id: str) -> PanelInstance:
        """Hide an existing panel."""
        instance = self.require(panel_id)
        instance.hide()
        return instance

    def activate(self, panel_id: str) -> PanelInstance:
        """Activate a panel and deactivate the previously active panel."""
        instance = self.create(panel_id)

        if self._active_panel_id is not None and self._active_panel_id != panel_id:
            previous = self._instances.get(self._active_panel_id)
            if previous is not None:
                previous.deactivate()

        instance.activate()
        self._active_panel_id = panel_id
        return instance

    def destroy(self, panel_id: str) -> PanelInstance:
        """Destroy and remove an existing runtime panel instance."""
        instance = self.require(panel_id)
        instance.destroy()
        del self._instances[panel_id]

        if self._active_panel_id == panel_id:
            self._active_panel_id = None

        return instance

    def get(self, panel_id: str) -> Optional[PanelInstance]:
        """Return an existing runtime instance, if present."""
        return self._instances.get(panel_id)

    def require(self, panel_id: str) -> PanelInstance:
        """Return an existing runtime instance or raise ``KeyError``."""
        instance = self.get(panel_id)
        if instance is None:
            raise KeyError(panel_id)
        return instance

    def instances(self) -> Iterable[PanelInstance]:
        """Return a stable snapshot of runtime panel instances."""
        return tuple(self._instances.values())

    def clear(self) -> None:
        """Destroy all runtime instances and clear active state."""
        for instance in self._instances.values():
            instance.destroy()

        self._instances.clear()
        self._active_panel_id = None

    def __len__(self) -> int:
        return len(self._instances)
