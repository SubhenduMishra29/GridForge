# ============================================================
# GridForge V2 — Canvas Package
# ============================================================
"""GridForge V2 Canvas subsystem.

The canvas owns the viewport, scene, coordinate conversion, grid,
navigation, transient interaction routing, and preview graphics.

Permanent SLD graphics realization is composed by the application root and
injected into CanvasPlugin. CanvasPlugin consumes that externally owned
service; it does not construct or own the SLD render system.

The canonical SLD path is:

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

Within the final presentation boundary, semantic SLD node realization is:

    SLDCanvasNode
        ↓
    SemanticPresentationRealization
        ↓
    PresentationSelection
        ↓
    SLDGraphicsItemFactory
        ↓
    QGraphicsItem

Ownership boundaries
--------------------
The canvas does not own Core electrical truth, electrical calculations,
application command execution, topology rules, or persistence of
transient preview graphics. SLD semantic realization remains renderer-neutral
until concrete construction at SLDGraphicsItemFactory.

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
