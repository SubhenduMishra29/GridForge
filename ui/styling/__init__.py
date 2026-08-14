# ============================================================
# File: ui/styling/__init__.py
# GridForge V2 — Styling Package
# ============================================================

"""
GridForge UI styling package.

This package contains presentation-level styling resources
used by the GridForge UI.

Current resources
-----------------
stylesheet.qss

Architecture
------------
The styling package is responsible only for UI appearance.

It does NOT:

    - own application state;
    - modify Core;
    - implement commands;
    - manage tools;
    - perform rendering;
    - manage docking;
    - perform electrical calculations;
    - implement business logic.

The QSS stylesheet styles Qt widgets.

Electrical/canvas graphics remain the responsibility of the
GridForge rendering subsystem.

No theme manager or style manager is introduced at this stage.
"""

__all__: list[str] = []
