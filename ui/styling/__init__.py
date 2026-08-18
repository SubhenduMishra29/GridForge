# ============================================================
# File: ui/styling/__init__.py
# GridForge V2 — UI Styling Package
# ============================================================
"""
GridForge V2 UI Styling
=======================

The ``ui.styling`` package contains presentation-level styling
infrastructure for the GridForge graphical interface.

Responsibilities
----------------

    Theme definitions
    Qt stylesheet management
    Styling resource access
    UI visual configuration

Architecture
------------

    UI Components
         │
         ▼
      ui.styling
         │
         ├── Theme
         └── Stylesheet
         
The styling subsystem is presentation infrastructure only.

It does not own:

    - application state
    - engineering state
    - Core models
    - network topology
    - controllers
    - commands
    - tools
    - selection
    - canvas behavior
    - renderers
    - plugins
    - engineering calculations

Qt Boundary
-----------

Qt dependencies must follow the GridForge UI Qt abstraction
boundary where applicable.

Styling must not introduce direct dependencies on the
engineering Core.
"""

from __future__ import annotations

from .theme import (
    DEFAULT_THEME,
    Theme,
    ThemeManager,
)

__all__ = [
    "DEFAULT_THEME",
    "Theme",
    "ThemeManager",
]
