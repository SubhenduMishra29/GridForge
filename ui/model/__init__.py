# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/model/__init__.py
#
# Purpose:
#     Package boundary for the GridForge V2 UI-side logical
#     document models.
#
# Architectural Role:
#     Exposes the public model-layer API without requiring callers
#     to depend on the internal module layout.
#
# Current Primary Model:
#
#     SLDModel
#
# Detailed Working:
#
#     UI Controller / SLD Controller
#                |
#                v
#          ui.model
#                |
#                v
#             SLDModel
#                |
#        +-------+-------+
#        |               |
#        v               v
# EquipmentManager  ConnectionManager
#
# The model package remains completely Qt-independent.
#
# Does NOT:
#     - create Qt widgets;
#     - create QGraphicsItems;
#     - render;
#     - process mouse/keyboard events;
#     - perform electrical calculations.
#
# Architectural Boundary:
#
#     ui.model
#         = logical UI/document state
#
#     ui.canvas
#         = visual representation and interaction
#
#     ui.controllers
#         = orchestration
#
#     core
#         = electrical/network computation
#
# ============================================================

"""
GridForge V2 — UI Model Package.

Public entry point for logical SLD document models.
"""

from .sld_model import SLDModel


__all__ = [
    "SLDModel",
]
