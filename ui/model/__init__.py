# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/model/__init__.py
#
# Author:
#     Subhendu Mishra
#
# Purpose:
#     Transitional package boundary retained while the obsolete
#     UI-side logical SLD model is removed.
#
# Architectural Status:
#     This package no longer owns SLDModel or authoritative logical
#     document state.
#
#     Electrical truth belongs to the Core Domain.
#     Controlled mutation belongs to the Application layer.
#     Presentation state is supplied through the Projection layer.
#
# Responsibilities:
#     - provide a stable package boundary during migration;
#     - avoid exporting obsolete UI document models;
#     - remain independent of Qt and presentation widgets.
#
# Does NOT:
#     - define SLDModel;
#     - own Project state;
#     - own Document state;
#     - own electrical/network state;
#     - create QGraphicsItems;
#     - create Qt widgets;
#     - render presentation content;
#     - process UI interaction.
#
# Correct Presentation Flow:
#
#     Core / Application
#             |
#             v
#       Projection Layer
#             |
#             +----> SLD
#             |
#             +----> Canvas
#             |
#             +----> Panels
#             |
#             +----> Tables / Reports
#
# Migration Note:
#     The former ui.model.sld_model module has been intentionally
#     removed. Do not recreate it. New presentation-state models
#     belong to the formal Projection architecture.
#
# ============================================================

"""GridForge V2 — transitional UI model package.

The former ``SLDModel`` export has been intentionally removed.

The ``ui.model`` package does not own an independent logical
representation of the electrical network. Authoritative electrical
state belongs to Core, while presentation state belongs to the
Projection layer.
"""

__all__: list[str] = []
