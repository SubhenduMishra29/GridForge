# ============================================================
# File: ui/items/__init__.py
# GridForge V2 — Graphics Items Package
# ============================================================
"""
GridForge V2 graphics-item projection package.

Purpose
-------
The ``ui.items`` package contains Qt graphics objects that
project authoritative application/Core objects onto the
canvas.

Architecture
------------

    Core / Application Model
              │
              ▼
        Renderer Layer
              │
              ▼
          ui.items
         ┌────┴────┐
         ▼         ▼
      BusItem   LineItem
         │         │
         └────┬────┘
              ▼
         GridScene
              │
              ▼
        GraphicsView

Ownership
---------
Graphics items are visual projections.

They do NOT own:

    - Core model state;
    - application selection state;
    - electrical topology;
    - tool lifecycle;
    - snapping policy;
    - navigation;
    - electrical calculations.

Selection
---------
Persistent application selection is owned by Controller.

Graphics-item selection state is only a visual projection of
the authoritative application selection.

Identity
--------
Graphics items representing application objects expose:

    object_id

The object ID identifies the corresponding authoritative
application/Core object.

Qt Architecture
---------------
All Qt dependencies must pass through:

    ui.core.qt

Concrete item implementations are imported here so the
package provides a stable public API.

Public API
----------
    BusItem
    LineItem
"""

from __future__ import annotations

from ui.items.bus_item import BusItem
from ui.items.line_item import LineItem


__all__ = [
    "BusItem",
    "LineItem",
]
