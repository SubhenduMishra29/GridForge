# ============================================================
# File: ui/controllers/__init__.py
# GridForge V2 — UI Controllers Package
# ============================================================
"""
GridForge V2 UI controllers package.

Controllers coordinate UI/application behavior while keeping
Qt-specific presentation code separated from Core domain logic.

Concrete controllers are imported explicitly by application
composition/bootstrap code.

This package initializer intentionally performs no automatic
controller discovery or registration.
"""

from __future__ import annotations

__all__: list[str] = []
