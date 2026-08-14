# ============================================================
# File: ui/canvas/__init__.py
# GridForge V2 — Canvas Package
# ============================================================
"""
GridForge V2 Canvas
===================

The ``ui.canvas`` package contains the canvas subsystem of the
GridForge UI.

The canvas is responsible for:

    - QGraphicsView-based canvas presentation;
    - scene ownership;
    - coordinate conversion;
    - grid geometry;
    - navigation;
    - transient interaction routing;
    - transient preview graphics;
    - render orchestration.

Architecture
------------

                    Canvas
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
     GraphicsView  Interaction  RenderSystem
          │         Manager          │
          │           │              │
          ▼           ▼              ▼
       Scene     Tools / Snap    Renderers
          │
          ▼
     Core Projection

Supporting services
-------------------

    CoordinateSystem
        Canonical viewport/scene/grid coordinate boundary.

    GridSystem
        Canvas grid geometry and grid presentation data.

    NavigationController
        Zoom, pan, fit and viewport navigation.

    InteractionManager
        Routes raw canvas input to the active tool.

    PreviewLayer
        Owns transient, non-persistent interaction graphics.

    RenderSystem
        Coordinates permanent graphical projection of the
        application/model state.

Ownership boundaries
--------------------

The canvas does NOT:

    - own the Core domain model;
    - perform electrical calculations;
    - implement application-level commands;
    - own persistent application selection;
    - own concrete tool instances;
    - own application-level tool selection;
    - implement electrical topology rules;
    - persist transient preview graphics.

Core application state remains authoritative outside the canvas.

UI infrastructure dependencies are provided by ``ui.core``.

Qt boundary
-----------

All Qt dependencies used by canvas modules must pass through:

    ui.core.qt

Canvas modules must not import PySide6 or PyQt directly.

Public API
----------

Canvas modules are intentionally not re-exported from this
package initializer.

Consumers should import the required canvas component from its
concrete module, for example:

    from ui.canvas.graphics_view import GraphicsView

This keeps package initialization side-effect free and avoids
implicit dependency loading.
"""

from __future__ import annotations

__all__: list[str] = []
