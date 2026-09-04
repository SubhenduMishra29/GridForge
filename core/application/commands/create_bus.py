# ============================================================
# File: core/application/commands/create_bus.py
# GridForge V2 — Create Bus Application Command
# Author: Subhendu Mishra
# ============================================================

"""Compatibility import surface for the canonical CreateBusCommand."""

from __future__ import annotations

from .model_commands import CREATE_BUS, CreateBusCommand

__all__ = ["CREATE_BUS", "CreateBusCommand"]
