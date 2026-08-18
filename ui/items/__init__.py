# ============================================================
# File: ui/items/__init__.py
# GridForge V2 — Graphics Items Package
# ============================================================
"""
GridForge V2 Graphics Items
===========================

The ``ui.items`` package contains presentation-layer graphics
objects used to project authoritative GridForge application
objects onto the canvas.

Architecture
------------

    GridForge Core / Application Model
                  │
                  ▼
             Controller
                  │
                  ▼
             Renderers
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


Architectural Role
------------------
Graphics items are visual projections only.

They provide the Qt graphics representation required by the
canvas layer while remaining subordinate to authoritative
application/Core state.

Graphics items must not become an alternative source of
engineering truth.


Ownership
---------
The ``ui.items`` package does NOT own:

    - engineering model state;
    - application state;
    - persistent selection state;
    - electrical topology;
    - command history;
    - tool lifecycle;
    - snapping policy;
    - navigation state;
    - engineering calculations.


Model Boundary
--------------
Graphics items may retain references to authoritative model
objects for presentation purposes.

Those references are projections.

Graphics items must never directly mutate Core state.

Any authoritative mutation must pass through the appropriate
application/controller/command path.


Selection
---------
Qt graphics-item selection represents visual state only.

Persistent application selection remains owned by the
Controller and SelectionManager.

The item layer may display selection state but must not become
the authoritative selection store.


Identity
--------
Graphics items representing authoritative application objects
expose a stable ``object_id`` corresponding to the projected
application/Core object.


Base Item
---------
``BaseItem`` defines the common presentation contract shared by
GridForge graphics items.

Concrete graphics items may additionally inherit from the
appropriate Qt graphics primitive when specialized geometry is
required.

For example:

    BaseItem
        │
        ├── BusItem
        │
        └── LineItem


Qt Architecture
---------------
All Qt dependencies must pass through:

    ui.core.qt

No concrete item may import PySide6, PyQt5, or PyQt6 directly.

The package initializer itself must not introduce additional Qt
dependencies.


Current Concrete Items
----------------------

    BaseItem
        Common graphics-item presentation contract.

    BusItem
        Visual projection of an authoritative Bus.

    LineItem
        Visual projection of an authoritative Line.


Future Vision
-------------
The package is intentionally extensible.

Future graphics items may represent additional GridForge
engineering objects such as:

    - transformers;
    - generators;
    - loads;
    - shunts;
    - breakers;
    - switches;
    - CT/PT equipment;
    - protection devices;
    - measurement devices;
    - substations;
    - other supported electrical equipment.

New item types must preserve the same architectural boundary:

    authoritative model
            │
            ▼
        application
            │
            ▼
         renderer
            │
            ▼
       graphics item

No graphics item should become an engineering-domain object.


Public API
----------
The package exports the common BaseItem contract together with
the currently supported concrete visual items.
"""

from __future__ import annotations

from ui.items.base_item import BaseItem
from ui.items.bus_item import BusItem
from ui.items.line_item import LineItem


__all__ = [
    "BaseItem",
    "BusItem",
    "LineItem",
]
