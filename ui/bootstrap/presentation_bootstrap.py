# ============================================================
# File: ui/bootstrap/presentation_bootstrap.py
# GridForge V2 — Presentation Bootstrap Boundary
# Author: Subhendu Mishra
# ============================================================
"""Compose shared presentation registries and read-only SLD boundaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ui.canvas.semantic_presentation_realization import SemanticPresentationRealization
from ui.canvas.sld_graphics_item_factory import SLDGraphicsItemFactory
from ui.equipment.equipment_registry import EquipmentRegistry
from ui.equipment.symbol.built_in_symbol_catalogue import register_builtin_symbols
from ui.equipment.symbol.symbol_factory import SymbolFactory
from ui.equipment.symbol.symbol_registry import SymbolRegistry
from ui.sld.sld_read_synchronizer import SLDReadSynchronizer
from ui.workspace.workspace_manager import WorkspaceManager


@dataclass
class PresentationBootstrap:
    """Own one coherent presentation composition graph."""

    workspace_manager: WorkspaceManager
    application: Any = None
    sld_read_synchronizer: SLDReadSynchronizer | None = None
    shell: Any = None
    equipment_registry: EquipmentRegistry = field(default_factory=EquipmentRegistry.create_default)
    symbol_registry: SymbolRegistry = field(default_factory=SymbolRegistry)
    symbol_factory: SymbolFactory | None = None
    semantic_realization: SemanticPresentationRealization | None = None
    sld_graphics_item_factory: SLDGraphicsItemFactory | None = None

    def __post_init__(self) -> None:
        if not self.symbol_registry.symbol_ids():
            register_builtin_symbols(self.symbol_registry)
        self.symbol_factory = self.symbol_factory or SymbolFactory(self.symbol_registry)
        self.semantic_realization = self.semantic_realization or SemanticPresentationRealization(
            self.equipment_registry, self.symbol_registry
        )
        self.sld_graphics_item_factory = self.sld_graphics_item_factory or SLDGraphicsItemFactory(
            self.symbol_registry
        )

    @classmethod
    def create(cls, workspace_manager: WorkspaceManager | None = None, application: Any = None,
               sld_read_synchronizer: SLDReadSynchronizer | None = None) -> "PresentationBootstrap":
        bootstrap = cls(workspace_manager=workspace_manager or WorkspaceManager(), application=application,
                        sld_read_synchronizer=sld_read_synchronizer)
        bootstrap._synchronize_application_boundary()
        return bootstrap

    def attach_application(self, application: Any) -> None:
        if application is None:
            raise TypeError("application must not be None")
        self.application = application
        self._synchronize_application_boundary()

    def detach_application(self) -> Any:
        application = self.application
        self.application = None
        self._synchronize_application_boundary()
        return application

    def attach_sld_read_synchronizer(self, synchronizer: SLDReadSynchronizer) -> None:
        if not isinstance(synchronizer, SLDReadSynchronizer):
            raise TypeError("synchronizer must be an SLDReadSynchronizer")
        self.sld_read_synchronizer = synchronizer
        self._synchronize_application_boundary()

    def detach_sld_read_synchronizer(self) -> SLDReadSynchronizer | None:
        synchronizer = self.sld_read_synchronizer
        if synchronizer is not None:
            synchronizer.detach_application()
        self.sld_read_synchronizer = None
        return synchronizer

    def require_application(self) -> Any:
        if self.application is None:
            raise RuntimeError("Presentation Application facade is not configured")
        return self.application

    def attach_shell(self, shell: Any) -> None:
        self.shell = shell

    def detach_shell(self) -> Any:
        shell = self.shell
        self.shell = None
        return shell

    def _synchronize_application_boundary(self) -> None:
        if self.sld_read_synchronizer is None:
            return
        if self.application is None:
            self.sld_read_synchronizer.detach_application()
        else:
            self.sld_read_synchronizer.attach_application(self.application)


__all__ = ["PresentationBootstrap"]
