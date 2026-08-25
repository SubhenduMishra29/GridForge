# ============================================================
# File: core/application/__init__.py
# GridForge V2 — Headless Application Layer
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 — Headless Application Layer.

This package contains the headless Application infrastructure
that sits between external consumers and the GridForge Core.

The Application layer is responsible for:

    * command contracts;
    * command dispatch;
    * application services;
    * transactions;
    * undo/redo history;
    * endpoint-reference resolution;
    * application composition.

The Application layer does NOT own:

    * Core electrical state;
    * SLD state;
    * UI state;
    * Qt objects;
    * canvas objects;
    * renderers.

The canonical external mutation path is:

    Application.execute(command)

The public Application facade is intentionally thin.
"""

from __future__ import annotations

from .application import Application


__all__ = [
    "Application",
]
