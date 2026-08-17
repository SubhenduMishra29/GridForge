"""
GridForge V2
============

Package:
    ui.plugins

Purpose
-------
UI composition plugins and plugin infrastructure for the GridForge
application.

Architectural rules
-------------------
- Concrete plugins are imported explicitly.
- Plugin discovery is never performed here.
- PluginLoader owns concrete implementation loading/construction.
- PluginRegistry owns plugin registration and low-level lifecycle.
- PluginManager owns dependency resolution and lifecycle orchestration.
- PluginContext is supplied during initialization, never construction.
- PluginStateStore owns observable runtime lifecycle state.
- MainWindow consumes plugin composition interfaces rather than
  constructing application subsystems directly.
- Plugins compose UI components; they do not own authoritative
  Core/domain state.
"""

from __future__ import annotations


# ============================================================
# PLUGIN CONTRACT
# ============================================================

from .plugin_contract import (
    BasePlugin,
    PluginContextProtocol,
    PluginContractError,
    PluginLifecycleProtocol,
    PluginMetadata,
    PluginProtocol,
    PluginWidgetProvider,
    is_plugin,
    plugin_dependencies,
    plugin_id,
    plugin_metadata,
    plugin_widget,
    validate_plugin,
)


# ============================================================
# PLUGIN CONTEXT
# ============================================================

from .plugin_context import (
    PluginContext,
)


# ============================================================
# PLUGIN LOADER
# ============================================================

from .plugin_loader import (
    DEFAULT_PLUGIN_CLASSES,
    DEFAULT_PLUGIN_FACTORIES,
    DEFAULT_PLUGIN_IMPLEMENTATIONS,
    DEFAULT_PLUGIN_MODULES,
    LoadedPlugin,
    PluginImplementation,
    PluginLoader,
    create_default_plugin_loader,
    load_default_plugins,
)


# ============================================================
# PLUGIN REGISTRY
# ============================================================

from .plugin_registry import (
    PluginEntry,
    PluginRegistry,
    create_plugin_registry,
)


# ============================================================
# PLUGIN MANAGER
# ============================================================

from .plugin_manager import (
    PluginDefinition,
    PluginManager,
    create_default_plugin_manager,
)


# ============================================================
# PLUGIN STATE
# ============================================================

from .plugin_state import (
    PluginStateStore,
)


# ============================================================
# PLUGIN EVENTS
# ============================================================

from .plugin_events import (
    # Export event symbols defined by plugin_events.py here
    # when they form part of its public API.
)


# ============================================================
# CANVAS PLUGIN
# ============================================================

from .canvas_plugin import (
    CanvasPlugin,
    CanvasPluginContext,
    create_canvas_plugin,
)


# ============================================================
# PANELS PLUGIN
# ============================================================

from .panels_plugin import (
    PanelSpec,
    PanelsPlugin,
    PanelsPluginContext,
    create_panels_plugin,
)


# ============================================================
# TOOLBAR PLUGIN
# ============================================================

from .toolbar_plugin import (
    ToolbarActionSpec,
    ToolbarPlugin,
    ToolbarPluginContext,
    create_toolbar_plugin,
    default_tool_actions,
)


# ============================================================
# STATUS PLUGIN
# ============================================================

from .status_plugin import (
    StatusPlugin,
    StatusPluginContext,
    StatusSpec,
    create_status_plugin,
    default_statuses,
)


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    # --------------------------------------------------------
    # Contract
    # --------------------------------------------------------
    "BasePlugin",
    "PluginContextProtocol",
    "PluginContractError",
    "PluginLifecycleProtocol",
    "PluginMetadata",
    "PluginProtocol",
    "PluginWidgetProvider",
    "is_plugin",
    "plugin_dependencies",
    "plugin_id",
    "plugin_metadata",
    "plugin_widget",
    "validate_plugin",

    # --------------------------------------------------------
    # Context
    # --------------------------------------------------------
    "PluginContext",

    # --------------------------------------------------------
    # Loader
    # --------------------------------------------------------
    "PluginImplementation",
    "LoadedPlugin",
    "PluginLoader",
    "DEFAULT_PLUGIN_IMPLEMENTATIONS",
    "DEFAULT_PLUGIN_MODULES",
    "DEFAULT_PLUGIN_CLASSES",
    "DEFAULT_PLUGIN_FACTORIES",
    "create_default_plugin_loader",
    "load_default_plugins",

    # --------------------------------------------------------
    # Registry
    # --------------------------------------------------------
    "PluginEntry",
    "PluginRegistry",
    "create_plugin_registry",

    # --------------------------------------------------------
    # Manager
    # --------------------------------------------------------
    "PluginDefinition",
    "PluginManager",
    "create_default_plugin_manager",

    # --------------------------------------------------------
    # State
    # --------------------------------------------------------
    "PluginStateStore",

    # --------------------------------------------------------
    # Canvas
    # --------------------------------------------------------
    "CanvasPlugin",
    "CanvasPluginContext",
    "create_canvas_plugin",

    # --------------------------------------------------------
    # Panels
    # --------------------------------------------------------
    "PanelSpec",
    "PanelsPlugin",
    "PanelsPluginContext",
    "create_panels_plugin",

    # --------------------------------------------------------
    # Toolbar
    # --------------------------------------------------------
    "ToolbarActionSpec",
    "ToolbarPlugin",
    "ToolbarPluginContext",
    "create_toolbar_plugin",
    "default_tool_actions",

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------
    "StatusPlugin",
    "StatusPluginContext",
    "StatusSpec",
    "create_status_plugin",
    "default_statuses",
]
