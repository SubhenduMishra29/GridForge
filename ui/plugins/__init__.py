"""
GridForge V2
============

Package:
    ui.plugins

Purpose
-------
UI composition plugins for the GridForge application.

Architectural rules
-------------------
- Concrete plugins are intentionally imported explicitly here.
- Plugin discovery/registration remains separate from plugin
  implementation.
- MainWindow consumes plugin interfaces rather than constructing
  application subsystems directly.
- Plugins compose UI components; they do not own authoritative
  Core/domain state.
"""

from __future__ import annotations

from .canvas_plugin import (
    CanvasPlugin,
    CanvasPluginContext,
    create_canvas_plugin,
)

from .panels_plugin import (
    PanelSpec,
    PanelsPlugin,
    PanelsPluginContext,
    create_panels_plugin,
)

from .toolbar_plugin import (
    ToolbarActionSpec,
    ToolbarPlugin,
    ToolbarPluginContext,
    create_toolbar_plugin,
    default_tool_actions,
)

from .status_plugin import (
    StatusPlugin,
    StatusPluginContext,
    StatusSpec,
    create_status_plugin,
    default_statuses,
)


__all__ = [
    # Canvas
    "CanvasPlugin",
    "CanvasPluginContext",
    "create_canvas_plugin",

    # Panels
    "PanelSpec",
    "PanelsPlugin",
    "PanelsPluginContext",
    "create_panels_plugin",

    # Toolbar
    "ToolbarActionSpec",
    "ToolbarPlugin",
    "ToolbarPluginContext",
    "create_toolbar_plugin",
    "default_tool_actions",

    # Status
    "StatusPlugin",
    "StatusPluginContext",
    "StatusSpec",
    "create_status_plugin",
    "default_statuses",
]
