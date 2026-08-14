# ui/items/__init__.py
"""
GridForge V2 — Graphics Items Package
=====================================

Purpose
-------
Contains the QGraphicsItem implementations used by the GridForge
canvas to represent authoritative Core/domain objects.

Examples
--------
- BusItem
- LineItem

Architecture
------------
Graphics items are presentation/interaction objects.

They may:
    - represent Core objects visually
    - maintain UI-specific graphical state
    - participate in Qt graphics interaction
    - communicate with the application/controller boundary

They must not:
    - become the authoritative source of engineering state
    - perform engineering calculations
    - independently mutate Core state
    - own electrical topology
    - replace the Command/Core mutation boundary

Renderer Relationship
---------------------
Concrete renderers create graphics items:

    Core Model
        |
        v
    Renderer
        |
        v
    Graphics Item

The RenderSystem and RendererRegistry do not need to know the
concrete graphics-item implementations.

Import Policy
-------------
This package initializer intentionally performs no concrete item
imports and no registration side effects.

Concrete items are imported by their owning renderer or by other
explicit UI infrastructure when required.
"""

__all__: list[str] = []
