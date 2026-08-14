# ============================================================
# File: ui/plugins/main_toolbar_plugin.py
# GridForge V2 — Main Toolbar Plugin
# ============================================================

"""
Main toolbar UI plugin.

Responsibilities
----------------
- Construct the application's main toolbar.
- Attach it to MainWindow.
- Expose the toolbar through the UI composition result.

This plugin does NOT:
    - own tool selection;
    - modify Core;
    - create tool instances;
    - implement tool behavior.

Tool registration belongs to the tool/plugin infrastructure.
"""

from __future__ import annotations

from typing import Any

from ui.core.plugin_registry import register_plugin
from ui.toolbars.main_toolbar import MainToolbar


@register_plugin("ui", "main_toolbar")
class MainToolbarPlugin:
    """
    UI plugin responsible for constructing MainToolbar.
    """

    order = 10

    def build(
        self,
        main_window: Any,
        controller: Any,
    ) -> tuple[str, MainToolbar]:
        """
        Build and attach the main toolbar.
        """

        if main_window is None:
            raise ValueError(
                "main_window must not be None."
            )

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        toolbar = MainToolbar()

        main_window.addToolBar(
            toolbar
        )

        return (
            "toolbar",
            toolbar,
        )


__all__ = [
    "MainToolbarPlugin",
]
