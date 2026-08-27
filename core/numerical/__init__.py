"""
GridForge V2
Author: Subhendu Mishra

File:
    core/numerical/__init__.py

Purpose:
    Public package boundary for GridForge numerical representations.

Architectural Boundary:
    This package contains numerical representations and numerical state
    containers. It does not own physical equipment, network topology,
    study semantics, UI, persistence, or solver algorithms.

Frozen Principle:
    Model      → physical/domain objects
    Network    → topology
    Study      → calculation meaning/formulation
    Numerical  → numerical representation/state
    Solver     → computation
    Results    → calculated outputs
"""

from .state import BusState, DynamicState


__all__ = [
    "BusState",
    "DynamicState",
]
