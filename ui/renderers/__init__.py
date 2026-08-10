"""
Renderers package

Purpose:
--------
Contains renderer classes that convert model objects into QGraphicsItems.

Examples:
---------
- BusRenderer
- LineRenderer

Important:
----------
Renderers are auto-registered via:
    @register_renderer("type")

Registration is triggered from:
    ui/core/__init__.py

So we DO NOT import renderers here.
"""

# Optional: explicit exports
__all__ = [
    "bus_renderer",
    "line_renderer",
]
