# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/connections/__init__.py
#
# Purpose:
#     Public API boundary for the SLD connection subsystem.
#
# Architectural Role:
#     Provides the logical connection layer between SLD equipment
#     terminals.
#
# Responsibilities:
#     - expose logical connections;
#     - expose terminal resolution;
#     - expose structural validation;
#     - expose connection management;
#     - expose routing and preview abstractions;
#     - expose the Core-topology synchronization boundary.
#
# Does NOT:
#     - render connection lines;
#     - create QGraphicsItems;
#     - perform electrical calculations;
#     - directly manipulate Qt scenes.
#
# ============================================================

"""
GridForge V2 — SLD Connection subsystem.

This package defines the UI-level logical connection boundary
for the Single Line Diagram.

Core remains authoritative for electrical topology.
"""

from .connection import Connection
from .connection_manager import ConnectionManager
from .connection_preview import ConnectionPreview
from .connection_router import ConnectionRouter
from .connection_validator import ConnectionValidator
from .terminal_resolver import TerminalResolver
from .topology_adapter import TopologyAdapter

__all__ = [
    "Connection",
    "ConnectionManager",
    "ConnectionPreview",
    "ConnectionRouter",
    "ConnectionValidator",
    "TerminalResolver",
    "TopologyAdapter",
]
