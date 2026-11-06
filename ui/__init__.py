"""
GridForge V2 — UI Package
==========================

Package
-------
ui

Purpose
-------
Top-level package for the GridForge V2 user interface.

Architectural Role
------------------
The ``ui`` package contains the presentation and interaction layer.

The package initializer intentionally performs no UI composition and
does not import concrete UI components.

UI composition is performed explicitly by the application composition
root and the UI plugin system.

Dependency Boundary
-------------------

    Application
        |
        v
    ui.main_window
        |
        v
    UI Plugin System
        |
        +---- Canvas
        +---- Panels
        +---- Toolbar
        +---- Status
        +---- Tools

Design Rules
------------
- No concrete UI component imports from this package initializer.
- No Qt widget construction.
- No application startup.
- No Core/domain mutation.
- No tool creation.
- No plugin registration.
- No rendering.
- No simulation or analysis.

Keeping this module intentionally minimal prevents importing the
entire UI subsystem merely by importing ``ui``.
"""

from __future__ import annotations

__all__: list[str] = []
