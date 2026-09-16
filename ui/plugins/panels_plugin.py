# ============================================================
# GridForge V2
# ============================================================
# File: ui/plugins/panels_plugin.py
# Author: Subhendu Mishra
# ============================================================

"""GridForge V2 — Panels Plugin.

Qt presentation/composition boundary for dockable application panels.
Workspace placement and visibility policy remain external.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from ui.core.qt import QDockWidget, QMainWindow, QObject, QWidget
from ui.plugins.plugin_context import PluginContext


@dataclass(frozen=True, slots=True)
class PanelSpec:
    panel_id: str
    title: str
    widget: QWidget | None = None
    closable: bool = True
    movable: bool = True
    floatable: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.panel_id, str) or not self.panel_id.strip():
            raise ValueError("panel_id must be a non-empty string.")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be a non-empty string.")
        if self.widget is not None and not isinstance(self.widget, QWidget):
            raise TypeError("widget must be QWidget or None.")
        for name, value in (("closable", self.closable), ("movable", self.movable), ("floatable", self.floatable)):
            if not isinstance(value, bool):
                raise TypeError(f"{name} must be bool.")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")


class PanelsPlugin(QObject):
    """Create and own panel widgets and their existing docks."""

    plugin_id = "panels"
    plugin_name = "Panels"
    plugin_version = "1.0"
    plugin_description = "GridForge application panel and dock composition."
    plugin_dependencies: tuple[str, ...] = ()
    plugin_optional = False

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._context: PluginContext | None = None
        self._panels: dict[str, QWidget] = {}
        self._dock_widgets: dict[str, QDockWidget] = {}
        self._panel_specs: dict[str, PanelSpec] = {}
        self._initialized = False

    @property
    def context(self) -> PluginContext | None: return self._context
    @property
    def widget(self) -> QWidget | None: return None
    @property
    def initialized(self) -> bool: return self._initialized
    @property
    def dock_widgets(self) -> tuple[QDockWidget, ...]: return tuple(self._dock_widgets.values())
    @property
    def panel_ids(self) -> tuple[str, ...]: return tuple(self._panels.keys())
    @property
    def panel_specs(self) -> Mapping[str, PanelSpec]: return dict(self._panel_specs)

    def initialize(self, context: PluginContext) -> None:
        if not isinstance(context, PluginContext): raise TypeError("PanelsPlugin requires PluginContext.")
        if self._initialized:
            if self._context is not context: raise RuntimeError("PanelsPlugin is already initialized with a different PluginContext.")
            return
        if not isinstance(context.main_window, QMainWindow): raise TypeError("PluginContext.main_window must be QMainWindow.")
        self._context = context; self._initialized = True
        try:
            from ui.panels.default_panels import compose_default_panel_specs
            for spec in compose_default_panel_specs(): self.add_panel(spec)
        except Exception:
            self._dock_widgets.clear(); self._panels.clear(); self._panel_specs.clear(); self._context = None; self._initialized = False; raise

    def shutdown(self) -> None:
        if not self._initialized: return
        for dock in tuple(self._dock_widgets.values()): self._remove_dock(dock)
        self._dock_widgets.clear(); self._panels.clear(); self._panel_specs.clear(); self._context = None; self._initialized = False

    def add_panel(self, spec: PanelSpec) -> QWidget:
        self._require_initialized()
        if not isinstance(spec, PanelSpec): raise TypeError("spec must be a PanelSpec.")
        if spec.panel_id in self._panels: raise ValueError(f"Panel already registered: {spec.panel_id!r}")
        widget = spec.widget if spec.widget is not None else QWidget()
        widget.setObjectName(f"GridForgePanel_{spec.panel_id}")
        dock = QDockWidget(spec.title, self._main_window); dock.setObjectName(spec.panel_id); dock.setWidget(widget); dock.setFeatures(self._dock_features(spec))
        self._panels[spec.panel_id] = widget; self._dock_widgets[spec.panel_id] = dock; self._panel_specs[spec.panel_id] = spec
        return widget

    def remove_panel(self, panel_id: str) -> QWidget | None:
        self._require_initialized()
        if not isinstance(panel_id, str): raise TypeError("panel_id must be a string.")
        widget = self._panels.pop(panel_id, None); dock = self._dock_widgets.pop(panel_id, None); self._panel_specs.pop(panel_id, None)
        if dock is not None: self._remove_dock(dock)
        return widget

    def get_panel(self, panel_id: str) -> QWidget | None:
        self._require_initialized()
        if not isinstance(panel_id, str): raise TypeError("panel_id must be a string.")
        return self._panels.get(panel_id)

    def get_dock(self, panel_id: str) -> QDockWidget | None:
        self._require_initialized()
        if not isinstance(panel_id, str): raise TypeError("panel_id must be a string.")
        return self._dock_widgets.get(panel_id)

    def get_panel_spec(self, panel_id: str) -> PanelSpec | None:
        self._require_initialized()
        if not isinstance(panel_id, str): raise TypeError("panel_id must be a string.")
        return self._panel_specs.get(panel_id)

    def panels(self) -> Mapping[str, QWidget]: return dict(self._panels)
    def docks(self) -> Mapping[str, QDockWidget]: return dict(self._dock_widgets)

    def _require_initialized(self) -> None:
        if not self._initialized: raise RuntimeError("PanelsPlugin is not initialized.")

    @property
    def _main_window(self) -> QMainWindow:
        self._require_initialized(); context = self._context
        if context is None or not isinstance(context.main_window, QMainWindow): raise RuntimeError("PanelsPlugin has no valid QMainWindow context.")
        return context.main_window

    @staticmethod
    def _dock_features(spec: PanelSpec) -> QDockWidget.DockWidgetFeature:
        features = QDockWidget.DockWidgetFeature.NoDockWidgetFeatures
        if spec.closable: features |= QDockWidget.DockWidgetFeature.DockWidgetClosable
        if spec.movable: features |= QDockWidget.DockWidgetFeature.DockWidgetMovable
        if spec.floatable: features |= QDockWidget.DockWidgetFeature.DockWidgetFloatable
        return features

    def _remove_dock(self, dock: QDockWidget) -> None:
        if not isinstance(dock, QDockWidget): return
        if self._context is not None and isinstance(self._context.main_window, QMainWindow): self._context.main_window.removeDockWidget(dock)
        dock.setParent(None); dock.deleteLater()


def create_panels_plugin() -> PanelsPlugin:
    """Construct the canonical PanelsPlugin without lifecycle initialization."""
    return PanelsPlugin()


__all__ = ["PanelSpec", "PanelsPlugin", "create_panels_plugin"]
