# ============================================================
# File: core/protection/thermal/__init__.py
# GridForge V2 — Thermal Protection
# Author: Subhendu Mishra
# ============================================================

"""Canonical thermal protection-function package."""

from core.protection.thermal.thermal_overload_relay import (
    ThermalOverloadRelay,
    ThermalOverloadSettings,
)

__all__ = ["ThermalOverloadRelay", "ThermalOverloadSettings"]
