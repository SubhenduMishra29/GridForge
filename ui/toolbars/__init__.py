# ============================================================
# File: ui/toolbars/__init__.py
# GridForge V2 — UI Toolbars Package
# ============================================================

"""
GridForge V2 UI toolbar package.

This package contains presentation-level toolbar components.

Toolbar components:

    MainToolbar
        Main application toolbar used as the presentation
        container for actions injected by UI plugins.

Architecture
------------

    UI Plugin / Controller
            │
            ▼
       Toolbar Component
            │
            ▼
          QAction

Toolbar components do NOT:

    - own tool logic;
    - create tool instances;
    - own ToolManager;
    - modify the Core model;
    - execute Core mutations;
    - perform electrical calculations;
    - perform rendering;
    - perform plugin discovery.

Plugin registration and composition remain outside this
package.

Qt Architecture
---------------

Individual toolbar modules import Qt classes through:

    ui.core.qt

This package initializer does not import Qt directly.
"""

from __future__ import annotations

from ui.toolbars.main_toolbar import MainToolbar


__all__ = [
    "MainToolbar",
]
