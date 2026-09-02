# ============================================================
# File: core/application/__init__.py
# GridForge V2 — Headless Application Layer
# Author: Subhendu Mishra
# ============================================================

"""Headless Application boundary between consumers and GridForge Core.

The Application layer owns commands, mutation orchestration, transactions,
and read-side snapshot contracts. It does not own electrical truth, SLD/UI
state, Qt objects, canvas objects, or renderers.
"""

from __future__ import annotations

from .application import Application
from .read_models import ElementReadModel, NetworkReadModel
from .read_service import NetworkReadService, ReadService

__all__ = [
    "Application",
    "ElementReadModel",
    "NetworkReadModel",
    "NetworkReadService",
    "ReadService",
]
