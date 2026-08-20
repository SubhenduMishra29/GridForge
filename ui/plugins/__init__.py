"""
GridForge V2
============

Package:
    ui.plugins

Purpose
-------
Public package interface for the GridForge V2 UI plugin infrastructure.

Architectural role
------------------
This package initializer exposes the finalized public plugin API.

It does NOT:

    - discover plugins;
    - scan packages;
    - import plugins for registration side effects;
    - construct plugin instances;
    - initialize or shut down plugins;
    - create PluginContext;
    - resolve dependencies;
    - orchestrate lifecycle;
    - own plugin runtime state.

Runtime responsibilities remain separated:

    PluginLoader
        explicit concrete-plugin import and construction

    PluginRegistry
        plugin registration and instance ownership

    PluginManager
        dependency resolution and lifecycle orchestration

    PluginContext
        initialization dependency carrier

    PluginStateStore
        canonical observable plugin runtime state

Concrete composition plugins are explicitly exposed through this
package API. Importing ``ui.plugins`` does not perform registration
or lifecycle operations.
"""

from __future__ import annotations


# ============================================================
# CONTRACT
# ============================================================

from .plugin_contract import (
    Plugin,
    plugin_id_of,
    supports_plugin_contract,
    validate_plugin,
)


# ============================================================
# CONTEXT
# ============================================================

from .plugin_context import (
    PluginContext,
)


# ============================================================
# EVENTS
# ============================================================

from .plugin_events import (
    PluginErrorEvent,
    PluginEvent,
    PluginEventSource,
    PluginEventType,
    event_to_dict,
    is_failure_event,
    is_lifecycle_event,
    is_terminal_event,
    plugin_defined,
    plugin_disabled,
    plugin_enabled,
    plugin_failed,
    plugin_initialize_requested,
    plugin_initialized,
    plugin_initializing,
    plugin_load_requested,
    plugin_loaded,
    plugin_reset,
    plugin_shutdown,
    plugin_shutdown_requested,
    plugin_shutting_down,
    plugin_unload_requested,
    plugin_unloaded,
)


# ============================================================
# LOADER
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
# REGISTRY
# ============================================================

from .plugin_registry import (
    PluginRegistry,
)


# ============================================================
# MANAGER
# ============================================================

from .plugin_manager import (
    PluginManager,
)


# ============================================================
# STATE
# ============================================================

from .plugin_state import (
    PluginStateStore,
)


# ============================================================
# CONCRETE COMPOSITION PLUGINS
# ============================================================

from .canvas_plugin import (
    CanvasPlugin,
    create_canvas_plugin,
)

from .panels_plugin import (
    PanelsPlugin,
    create_panels_plugin,
)

from .toolbar_plugin import (
    ToolbarActionSpec,
    ToolbarPlugin,
    create_toolbar_plugin,
    default_tool_actions,
)

from .status_plugin import (
    StatusPlugin,
    create_status_plugin,
)


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    # Contract
    "Plugin",
    "plugin_id_of",
    "supports_plugin_contract",
    "validate_plugin",

    # Context
    "PluginContext",

    # Events
    "PluginErrorEvent",
    "PluginEvent",
    "PluginEventSource",
    "PluginEventType",
    "event_to_dict",
    "is_failure_event",
    "is_lifecycle_event",
    "is_terminal_event",
    "plugin_defined",
    "plugin_disabled",
    "plugin_enabled",
    "plugin_failed",
    "plugin_initialize_requested",
    "plugin_initialized",
    "plugin_initializing",
    "plugin_load_requested",
    "plugin_loaded",
    "plugin_reset",
    "plugin_shutdown",
    "plugin_shutdown_requested",
    "plugin_shutting_down",
    "plugin_unload_requested",
    "plugin_unloaded",

    # Loader
    "DEFAULT_PLUGIN_CLASSES",
    "DEFAULT_PLUGIN_FACTORIES",
    "DEFAULT_PLUGIN_IMPLEMENTATIONS",
    "DEFAULT_PLUGIN_MODULES",
    "LoadedPlugin",
    "PluginImplementation",
    "PluginLoader",
    "create_default_plugin_loader",
    "load_default_plugins",

    # Registry
    "PluginRegistry",

    # Manager
    "PluginManager",

    # State
    "PluginStateStore",

    # Concrete composition plugins
    "CanvasPlugin",
    "create_canvas_plugin",
    "PanelsPlugin",
    "create_panels_plugin",
    "ToolbarActionSpec",
    "ToolbarPlugin",
    "create_toolbar_plugin",
    "default_tool_actions",
    "StatusPlugin",
    "create_status_plugin",
]
