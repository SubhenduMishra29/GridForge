# ============================================================
# File: ui/plugins/__init__.py
# GridForge V2 — Plugin Package
# ============================================================

"""
GridForge V2 UI plugin bootstrap.

Purpose
-------
Import built-in plugin modules so their registration decorators
execute during application/plugin initialization.

Architecture
------------
This module is responsible only for plugin-module bootstrap.

It does NOT:

    - maintain the plugin registry;
    - create plugin instances;
    - construct UI components;
    - manage plugin lifecycle;
    - select tools;
    - modify the Core model.

Plugin registration is performed by
ui.core.plugin_registry.

Plugin loading/discovery remains conceptually separate from the
registry itself.
"""

from __future__ import annotations

# ============================================================
# BUILT-IN UI PLUGINS
# ============================================================

from ui.plugins import toolbar_plugin
from ui.plugins import properties_plugin
from ui.plugins import layers_plugin
from ui.plugins import status_plugin

# ============================================================
# BUILT-IN TOOL UI PLUGINS
# ============================================================

from ui.plugins.tools import basic_tools_plugin


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "toolbar_plugin",
    "properties_plugin",
    "layers_plugin",
    "status_plugin",
    "basic_tools_plugin",
]
