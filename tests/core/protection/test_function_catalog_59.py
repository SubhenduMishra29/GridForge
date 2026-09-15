# ============================================================
# File: tests/core/protection/test_function_catalog_59.py
# GridForge V2 — ANSI 59 Function Catalog Tests
# Author: Subhendu Mishra
# ============================================================

from core.protection.function_catalog import (
    ProtectionFunctionStatus,
    get_protection_function,
)
from core.protection.voltage import OverVoltageRelay, UnderVoltageRelay


def test_catalog_resolves_59_to_canonical_overvoltage_relay() -> None:
    specification = get_protection_function("59")

    assert specification.status is ProtectionFunctionStatus.IMPLEMENTED
    assert specification.implementation is OverVoltageRelay


def test_catalog_resolves_27_to_canonical_undervoltage_relay() -> None:
    specification = get_protection_function("27")

    assert specification.status is ProtectionFunctionStatus.IMPLEMENTED
    assert specification.implementation is UnderVoltageRelay
