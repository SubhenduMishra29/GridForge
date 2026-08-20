# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/sld/sld_model.py
#
# Purpose:
#     UI-side structural model for the GridForge Single Line
#     Diagram (SLD) subsystem.
#
# Architectural Role:
#     SLD is a first-class GridForge V2 UI capability. This file
#     defines the document-level visual structure represented by
#     the SLD without introducing Qt, rendering, or electrical
#     calculation responsibilities.
#
# Responsibilities:
#     - represent SLD nodes/equipment references;
#     - represent SLD connections;
#     - maintain stable UI identifiers;
#     - maintain logical positions;
#     - maintain UI/document properties;
#     - provide serialization boundaries.
#
# Does NOT:
#     - perform electrical calculations;
#     - execute power-flow/short-circuit/other analysis;
#     - create Qt graphics objects;
#     - render symbols;
#     - process mouse/keyboard events;
#     - replace the Core electrical network model.
#
# Relationship:
#
#     SLDDocument
#          |
#          v
#      SLDModel
#       /    \
#      v      v
#    Nodes  Connections
#       |
#       v
#    Canvas / Items / Renderers
#
# Important Boundary:
#     The SLD model is a UI/document representation. The Core
#     remains authoritative for electrical-engine data and
#     calculations. Synchronization will be introduced through
#     the appropriate controller/adapter layer.
#
# ============================================================
