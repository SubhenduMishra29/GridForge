# ============================================================
# File: tests/core/protection/test_function_catalog.py
# GridForge V2 — Protection Function Catalog Tests
# Author: Subhendu Mishra
# ============================================================

"""Headless tests for the canonical protection-function catalog.

Tests are authored but intentionally not executed in this phase.
"""

from core.protection.distance import DistanceRelay
from core.protection.directional import DirectionalRelay
from core.protection.function_catalog import (
    ProtectionFunctionStatus,
    get_protection_function,
    list_protection_functions,
)
from core.protection.overcurrent import (
    IECOvercurrentRelay,
    InstantaneousOvercurrentRelay,
)


def test_catalog_exposes_all_requested_ansi_functions() -> None:
    assert set(list_protection_functions()) == {
        "50", "51", "50N", "51N", "27", "59", "46", "49", "67", "87", "21",
    }


def test_catalog_marks_existing_implemented_functions_canonically() -> None:
    assert get_protection_function("50").status is ProtectionFunctionStatus.IMPLEMENTED
    assert get_protection_function("50").implementation is InstantaneousOvercurrentRelay
    assert get_protection_function("51").status is ProtectionFunctionStatus.IMPLEMENTED
    assert get_protection_function("51").implementation is IECOvercurrentRelay
    assert get_protection_function("67").status is ProtectionFunctionStatus.IMPLEMENTED
    assert get_protection_function("67").implementation is DirectionalRelay
    assert get_protection_function("21").status is ProtectionFunctionStatus.IMPLEMENTED
    assert get_protection_function("21").implementation is DistanceRelay


def test_catalog_does_not_fabricate_unimplemented_functions() -> None:
    for code in ("50N", "51N", "27", "59", "46", "49", "87"):
        specification = get_protection_function(code)
        assert specification.status is ProtectionFunctionStatus.NOT_IMPLEMENTED
        assert specification.implementation is None


def test_catalog_normalizes_function_code() -> None:
    assert get_protection_function(" 51 ").code == "51"


def test_unknown_function_code_is_rejected() -> None:
    try:
        get_protection_function("999")
    except KeyError as exc:
        assert "999" in str(exc)
    else:
        raise AssertionError("Unknown ANSI function code must be rejected.")
