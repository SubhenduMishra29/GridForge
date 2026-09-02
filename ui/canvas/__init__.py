# ============================================================
# File: ui/canvas/__init__.py
# GridForge V2 — Canvas Package
# Author: Subhendu Mishra
# ============================================================
"""GridForge V2 Canvas subsystem.

The canvas owns the viewport, scene, coordinate conversion, grid,
navigation, transient interaction routing, and preview graphics.

Permanent SLD graphics realization is deliberately outside the generic
Canvas composition boundary and is owned by CanvasPlugin through the
single SLD projection path:

    Core/Application
        ↓
    SLD projection/read model
        ↓
    SLDDocument / SLDLayout
        ↓
    SLDCanvasProjection
        ↓
    SLDCanvasSnapshot
        ↓
    SLDCanvasRenderSystem
        ↓
    QGraphicsScene

Ownership boundaries
--------------------
The canvas does not own Core electrical truth, electrical calculations,
application command execution, topology rules, or persistence of
transient preview graphics.

Qt boundary
-----------
All Qt dependencies used by canvas modules pass through ``ui.core.qt``.
Canvas modules must not import PySide6 or PyQt directly.

Public API
----------
Canvas modules are intentionally not re-exported from this initializer.
Consumers import concrete components from their owning modules.
"""

from __future__ import annotations

__all__: list[str] = []
