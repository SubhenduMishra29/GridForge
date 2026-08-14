# ============================================================
# File: ui/renderers/__init__.py
# GridForge V2 — Renderer Package
# ============================================================
"""
GridForge V2 renderer package.

The renderer layer converts authoritative application/Core
objects into graphical presentation state.

Architecture
------------

    Core / Application State
              │
              ▼
        RendererRegistry
              │
              ▼
           Renderer
              │
              ▼
          Graphics Item
              │
              ▼
           GridScene

Renderer Responsibilities
--------------------------
Renderers may:

    - create graphical projections;
    - update existing graphical projections;
    - remove obsolete projections;
    - apply visual presentation;
    - synchronize geometry from authoritative state.

Renderers must NOT:

    - own Core model state;
    - mutate Core model objects;
    - implement tools;
    - implement selection ownership;
    - implement snapping;
    - implement navigation;
    - perform electrical calculations;
    - determine electrical topology.

Renderer Registry
-----------------
Concrete renderer registration is handled by:

    ui.core.renderer_registry

This package exposes renderer classes when they exist.

The package intentionally does not instantiate renderers or
perform automatic registration. Renderer discovery/loading is
an explicit application concern.

Qt Architecture
---------------
Concrete renderers must import Qt classes only through:

    ui.core.qt
"""

from __future__ import annotations


__all__: list[str] = []
