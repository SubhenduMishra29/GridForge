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
#     - expose connection objects;
#     - expose terminal resolution;
#     - expose validation;
#     - expose connection management;
#     - expose routing and preview abstractions;
#     - expose the future Core-topology synchronization boundary.
#
# Does NOT:
#     - render connection lines;
#     - create QGraphicsLineItem objects;
#     - perform power-system calculations;
#     - directly manipulate Qt scenes.
#
# ============================================================

"""
GridForge V2 — SLD Connection subsystem.
"""

from .connection import Connection
from .terminal_resolver import TerminalResolver
from .connection_validator import ConnectionValidator
from .connection_manager import ConnectionManager
from .connection_router import ConnectionRouter
from .connection_preview import ConnectionPreview
from .topology_adapter import TopologyAdapter

__all__ = [
    "Connection",
    "TerminalResolver",
    "ConnectionValidator",
    "ConnectionManager",
    "ConnectionRouter",
    "ConnectionPreview",
    "TopologyAdapter",
]
