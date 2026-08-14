# ============================================================
# File: ui/plugins/tools/basic_tools_plugin.py
# GridForge V2 — Basic Tools UI Plugin
# ============================================================

"""
Basic canvas-tool toolbar integration.

Responsibilities
----------------
- Obtain the already-created main toolbar.
- Add the standard GridForge canvas tools.
- Route tool selection through Controller.

This plugin does NOT:
    - create tool instances;
    - manage tool lifecycle;
    - implement tool behavior;
    - directly access ToolManager;
    - modify Core;
    - perform canvas interaction.

Controller remains the application-level tool-selection owner.
"""

from __future__ import annotations

from typing import Any

from ui.core.plugin_registry import register_plugin


@register_plugin("ui", "basic_tools")
class BasicToolsPlugin:
    """
    Adds the standard canvas tools to MainToolbar.
    """

    order = 20

    def build(
        self,
        main_window: Any,
        controller: Any,
    ) -> None:
        """
        Inject standard tools into the main toolbar.
        """

        if main_window is None:
            raise ValueError(
                "main_window must not be None."
            )

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        toolbar = main_window.get_component(
            "toolbar"
        )

        if toolbar is None:
            raise RuntimeError(
                "Main toolbar is not available. "
                "MainToolbarPlugin must be built before "
                "BasicToolsPlugin."
            )

        add_tool = getattr(
            toolbar,
            "add_tool",
            None,
        )

        if not callable(add_tool):
            raise TypeError(
                "Main toolbar must provide add_tool()."
            )

        # ----------------------------------------------------
        # Select
        # ----------------------------------------------------

        add_tool(
            "Select",
            lambda: controller.set_tool("select"),
            "select",
        )

        # ----------------------------------------------------
        # Bus
        # ----------------------------------------------------

        add_tool(
            "Bus",
            lambda: controller.set_tool("bus"),
            "bus",
        )

        # ----------------------------------------------------
        # Line
        # ----------------------------------------------------

        add_tool(
            "Line",
            lambda: controller.set_tool("line"),
            "line",
        )

        return None


__all__ = [
    "BasicToolsPlugin",
]
