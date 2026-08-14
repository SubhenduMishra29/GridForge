# ============================================================
# File: ui/plugins/properties_plugin.py
# GridForge V2 — Properties Panel Plugin
# ============================================================

"""
GridForge V2 — Properties Panel Plugin
======================================

Constructs the Properties panel used by the main application
window.

Responsibilities
----------------
PropertiesPlugin:

    - constructs PropertiesPanel;
    - returns it as a named UI component.

PropertiesPlugin does NOT:

    - own Core model state;
    - modify the Core model;
    - perform property editing logic;
    - manage selection;
    - manage docking;
    - create tool instances;
    - manage ToolManager;
    - perform electrical calculations.

Panel behavior remains owned by PropertiesPanel and the
appropriate controller/model services.

Plugin Registration
-------------------
The plugin registers in the "ui" namespace:

    @register_plugin("ui", "properties")

The registry stores the plugin class. The UI composition layer
is responsible for instantiating and invoking the plugin.
"""

from __future__ import annotations

from typing import Any

from ui.core.plugin_registry import register_plugin
from ui.panels.properties_panel import PropertiesPanel


@register_plugin(
    "ui",
    "properties",
)
class PropertiesPlugin:
    """
    UI plugin responsible for constructing PropertiesPanel.
    """

    # ========================================================
    # PLUGIN ORDER
    # ========================================================

    order = 30

    # ========================================================
    # BUILD
    # ========================================================

    def build(
        self,
        main_window: Any,
        controller: Any,
    ) -> tuple[str, PropertiesPanel]:
        """
        Construct the Properties panel.

        Parameters
        ----------
        main_window:
            GridForge main application window.

        controller:
            GridForge application controller.

        Returns
        -------
        tuple[str, PropertiesPanel]
            Named UI component for the UI composition layer.
        """

        if main_window is None:
            raise ValueError(
                "main_window must not be None."
            )

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        panel = PropertiesPanel()

        return (
            "properties",
            panel,
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "PropertiesPlugin",
]
