# ============================================================
# File: ui/core/__init__.py
# GridForge V2 — UI Core Package
# ============================================================
"""
GridForge V2 UI Core
====================

The ``ui.core`` package contains the framework-level services
shared by the GridForge UI.

Core responsibilities
---------------------

    Qt abstraction
    Application/UI Controller
    Command management
    Plugin registration
    Panel registration
    Renderer registration
    Selection management
    Tool management
    Snap management

Architecture
------------

    UI Components
         │
         ▼
      ui.core
         │
         ├── Controller
         ├── CommandManager
         ├── PluginRegistry
         ├── PanelRegistry
         ├── RendererRegistry
         ├── SelectionManager
         ├── ToolManager
         └── SnapSystem

The core UI services provide infrastructure and coordination.
They do not own the electrical domain model.

Qt Boundary
-----------

All Qt dependencies used by UI modules must pass through:

    ui.core.qt

Concrete UI modules must not import PySide6 or PyQt directly.
"""

from __future__ import annotations

__all__: list[str] = []
