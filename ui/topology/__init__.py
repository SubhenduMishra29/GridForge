# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/topology/__init__.py
#
# Purpose:
#     Public package boundary for the GridForge V2 SLD topology
#     subsystem.
#
# Architectural Role:
#     Exposes the topology validation API without requiring
#     callers to depend on the internal module structure.
#
# Current Public Components:
#
#     TopologyValidator
#         Performs non-mutating validation of proposed logical
#         SLD connections.
#
#     TopologyValidationResult
#         Structured result describing whether a topology
#         operation is valid.
#
#     TopologyValidationCode
#         Stable machine-readable validation reason.
#
# Detailed Working:
#
#     Tool / Controller
#             |
#             v
#     ui.topology
#             |
#             v
#     TopologyValidator
#             |
#       +-----+------+
#       |            |
#       v            v
# EquipmentManager  ConnectionManager
#       |            |
#       +-----+------+
#             |
#             v
#     TopologyValidationResult
#             |
#       +-----+------+
#       |            |
#       v            v
#     accept       reject
#
# Architectural Boundary:
#
#     This package validates UI/document topology rules.
#
#     It does NOT:
#
#         - create Qt objects;
#         - render the SLD;
#         - route graphical connections;
#         - perform power-flow calculations;
#         - own Core network state.
#
#     Core electrical validation and simulation remain outside the
#     UI topology package.
#
# Future Extensions:
#
#     Additional topology policies may later be exposed here for:
#
#         - terminal cardinality;
#         - bus connectivity;
#         - equipment compatibility;
#         - voltage-domain compatibility;
#         - connection constraints;
#         - topology diagnostics.
#
#     Such policies should remain explicit and independently
#     testable.
#
# ============================================================

"""
GridForge V2 — SLD Topology Package.

Public API for UI-side topology validation.
"""

from .topology_validator import (
    TopologyValidationCode,
    TopologyValidationResult,
    TopologyValidator,
)


__all__ = [
    "TopologyValidationCode",
    "TopologyValidationResult",
    "TopologyValidator",
]
