# ============================================================
# File: ui/plugins/main_toolbar_plugin.py
# GridForge V2 — Main Toolbar Plugin
# ============================================================
"""
Main toolbar UI plugin.

The plugin integrates MainToolbar into the application
composition layer.

Responsibilities
----------------
MainToolbarPlugin:

    - registers the main toolbar as a UI plugin;
    - creates the MainToolbar;
    - inserts it into the main window.

It does NOT:

    - own application-level tool selection;
    - implement toolbar actions;
    - modify the Core model;
    - perform electrical calculations;
    - manage commands;
    - manage toolbar lifecycle outside Qt ownership.

Plugin Registry
---------------
The plugin is registered in the "ui" namespace using the stable
identifier:

    "main_toolbar"

Qt Architecture
---------------
MainToolbar itself is responsible for its Qt implementation.
This plugin only composes it into the main window.
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
    UI composition plugin for the GridForge main toolbar.
    """

    # ========================================================
    # ORDER
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
        Create and install the main toolbar.

        Parameters
        ----------
        main_window:
            GridForge main application window.

        controller:
            Application controller.

        Returns
        -------
        tuple[str, MainToolbar]
            UI component type and created toolbar.

        Notes
        -----
        Controller is accepted as part of the standard UI plugin
        build contract. MainToolbar itself determines whether it
        requires the controller.
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


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "MainToolbarPlugin",
]
