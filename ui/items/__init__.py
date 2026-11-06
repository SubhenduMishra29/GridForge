# ============================================================
# File: ui/items/__init__.py
# GridForge V2 — Graphics Items Package
# Author: Subhendu Mishra
# ============================================================
"""
GridForge V2 Graphics Items
===========================

The ``ui.items`` package contains presentation-layer graphics
objects used to realize renderer-neutral SLD projections on the
Qt canvas. Graphics items are projections only; they do not own
electrical truth or application mutation.

Architecture
------------

    SLD Document / Presentation Model
                  │
                  ▼
         SLDCanvasProjection
                  │
                  ▼
          SLDCanvasSnapshot
                  │
                  ▼
       SLDCanvasRenderSystem
             ┌────┴────┐
             ▼         ▼
          BusItem   LineItem
             │         │
             └────┬────┘
                  ▼
            QGraphicsScene

This is the unified SLD graphics realization path. There is no
independent renderer registry, renderer loader, or legacy
RenderSystem between application/Core state and graphics items.

Architectural Role
------------------
Graphics items are visual projections only.

They provide the Qt graphics representation required by the SLD
canvas while remaining downstream of the renderer-neutral
projection boundary.

Graphics items must never become an alternative source of
engineering truth.


Ownership
---------
The ``ui.items`` package does NOT own:

    - engineering model state;
    - authoritative application state;
    - electrical topology;
    - command history;
    - tool lifecycle;
    - snapping policy;
    - navigation state;
    - engineering calculations.

Graphics-item geometry, appearance, selection display, and other
transient visual state are presentation concerns. Persistent SLD
graphical state belongs to the SLD presentation/document model,
not to a graphics item as the sole authority.


Model Boundary
--------------
Concrete graphics items consume stable identity and presentation
/read-side data supplied by the SLD graphics realization path.

They must not retain authoritative Core model objects or
Controllers as an input contract merely to render themselves.

Graphics items must never directly mutate Core state. Authoritative
engineering mutations follow the command boundary:

    user intent
         │
         ▼
      Command
         │
         ▼
    Application
         │
         ▼
        Core

The graphics item remains downstream of that boundary.


Selection
---------
Qt graphics-item selection represents visual state only.

Persistent or application-level selection remains owned by the
appropriate presentation/controller selection infrastructure.

The item layer may display selection state but must not become the
authoritative selection store.


Identity
--------
Graphics items expose a stable ``object_id`` identifying the
projected presentation object. Identity is a reference into the
projection/read-side model; the item does not become the owner of
that engineering object.


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
        Specialized visual projection for an SLD bus node.

    LineItem
        Specialized visual projection for an SLD connection.


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

    SLD read-side / presentation data
              │
              ▼
    SLDCanvasRenderSystem
              │
              ▼
        graphics item
              │
              ▼
       QGraphicsScene

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
