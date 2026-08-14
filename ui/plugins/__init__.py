# ============================================================
# File: ui/plugins/__init__.py
# GridForge V2 — Plugin Package
# ============================================================

"""
GridForge UI plugin package.

Importing this package loads the built-in UI plugins so their
registration decorators execute automatically.

Plugin discovery/loading remains separate from the registry
itself.
"""

from ui.plugins.toolbar_plugin import MainToolbarPlugin
from ui.plugins.properties_plugin import PropertiesPlugin
from ui.plugins.layers_plugin import LayersPlugin
from ui.plugins.status_plugin import StatusPlugin

__all__ = [
    "MainToolbarPlugin",
    "PropertiesPlugin",
    "LayersPlugin",
    "StatusPlugin",
]
