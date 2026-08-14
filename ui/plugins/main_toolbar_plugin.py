# ============================================================
# File: ui/plugins/main_toolbar_plugin.py
# GridForge V2 — Main Toolbar Plugin
# ============================================================

"""
GridForge V2 — Main Toolbar Plugin
==================================

Constructs and attaches the application's main toolbar.

Responsibilities
----------------
MainToolbarPlugin:

    - constructs MainToolbar;
    - attaches it to MainWindow;
    - returns the toolbar as a named UI component.

MainToolbarPlugin does NOT:

    - own tool selection;
    - create tool instances;
    - manage ToolManager;
    - implement tool behavior;
    - modify the Core model;
    - perform canvas interaction;
    - perform electrical calculations.

Tool selection remains the responsibility of Controller.
Tool lifecycle remains the responsibility of ToolManager.

Plugin Registration
-------------------
The plugin registers in the "ui" namespace:

    @register_plugin("ui", "main_toolbar")

The registry stores the plugin class and does not instantiate it.
"""

from __future__ import annotations

from typing import Any

from ui.core.plugin_registry import register_plugin
from ui.toolbars.main_toolbar import MainToolbar


@register_plugin(
    "ui",
    "main_toolbar",
)
class MainToolbarPlugin:
    """
    UI plugin responsible for constructing MainToolbar.
    """

    # ========================================================
    # PLUGIN ORDER
    # ========================================================

    order = 10

    # ========================================================
    # BUILD
    # ========================================================

    def build(
        self,
        main_window: Any,
        controller: Any,
    ) -> tuple[str, MainToolbar]:
        """
        Construct and attach the main application toolbar.

        Parameters
        ----------
        main_window:
            GridForge main application window.

        controller:
            GridForge application controller.

        Returns
        -------
        tuple[str, MainToolbar]
            Named UI component returned to the UI composition
            layer.

        Notes
        -----
        The controller is validated here because the plugin
        participates in the application UI composition contract,
        although this particular plugin does not directly use
        it.
        """

        if main_window is None:
            raise ValueError(
                "main_window must not be None."
            )

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        # ----------------------------------------------------
        # Construct toolbar.
        # ----------------------------------------------------

        toolbar = MainToolbar()

        # ----------------------------------------------------
        # Attach toolbar to MainWindow.
        # ----------------------------------------------------

        main_window.addToolBar(
            toolbar
        )

        # ----------------------------------------------------
        # Return named component.
        #
        # The UI composition layer/MainWindow is responsible
        # for deciding how returned components are stored.
        # ----------------------------------------------------

        return (
            "toolbar",
            toolbar,
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "MainToolbarPlugin",
]
