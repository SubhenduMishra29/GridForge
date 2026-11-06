# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/connections/__init__.py
#
# Purpose:
#     Public API boundary for the current V2 SLD connection
#     presentation/interaction subsystem.
#
# Architectural Role:
#     Exposes logical connection state, transient preview state,
#     structural validation, terminal lookup, and renderer-neutral
#     routing.
#
# Does NOT:
#     - own electrical topology;
#     - mutate Core directly;
#     - expose a TopologyAdapter;
#     - expose a ConnectionManager;
#     - render Qt graphics.
# ============================================================

"""GridForge V2 — current SLD connection presentation subsystem."""

from .connection import Connection
from .connection_preview import ConnectionPreview
from .connection_router import ConnectionRouter
from .connection_validator import ConnectionValidator
from .terminal_resolver import TerminalResolver

__all__ = [
    "Connection",
    "ConnectionPreview",
    "ConnectionRouter",
    "ConnectionValidator",
    "TerminalResolver",
]
