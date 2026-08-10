"""
Core package initializer

Purpose:
--------
- Ensures all core systems are discoverable
- Triggers auto-registration side effects (tools, renderers)
- Provides clean import surface

IMPORTANT:
----------
Importing modules here ensures decorators like:
    @register_tool
    @register_renderer

are executed at startup.
"""

# ------------------------------------------------------
# Expose main classes (clean imports)
# ------------------------------------------------------
from .controller import Controller
from .tool_registry import register_tool, create_tool
from .renderer_registry import register_renderer, get_renderer

# ------------------------------------------------------
# Force registration of plugins
# ------------------------------------------------------
# These imports are REQUIRED so decorators execute

import ui.tools.select_tool
import ui.tools.bus_tool
import ui.tools.line_tool

import ui.renderers.bus_renderer
import ui.renderers.line_renderer
