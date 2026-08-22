# ============================================================
# File: tests/core/application/test_errors.py
# GridForge V2 — Application Error Contract Tests
# ============================================================
"""
GridForge V2
============

Test module:
    tests/core/application/test_errors.py

Purpose
-------
Tests the frozen Headless Application error contract.

These tests deliberately verify behavior at the public contract
level rather than implementation details.

The tests establish that:

    * ApplicationError is structured;
    * error codes are stable data;
    * messages remain human-readable data;
    * categories are preserved;
    * severity is preserved;
    * details are supported;
    * causes are retained;
    * errors are immutable;
    * semantic error subclasses provide the expected categories;
    * malformed errors are rejected.

No Qt/UI fixture is required.

This test module must remain completely headless.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.application.errors import (
    ApplicationError,
    DomainError,
    ExecutionError,
    ResourceError,
    ValidationError,
)


class TestApplicationError:
    """Tests for the base ApplicationError contract."""

    def test_basic_error(self) -> None:
        error = ApplicationError(
            code="TEST_ERROR",
            message="Test operation failed.",
        )

        assert error.code == "TEST_ERROR"
        assert error.message == "Test operation failed."
        assert error.category == "application"
        assert error.severity == "error"
        assert error.details is None
        assert error.cause is None

    def test_error_is_an_exception(self) -> None:
        error = ApplicationError(
            code="TEST_ERROR",
            message="Test operation failed.",
        )

        assert isinstance(error, Exception)

    def test_exception_string_is_human_message(self) -> None:
        error = ApplicationError(
            code="TEST_ERROR",
            message="Test operation failed.",
        )

        assert str(error) == "Test operation failed."

    def test_custom_category(self) -> None:
        error = ApplicationError(
            code="CUSTOM_ERROR",
            message="Custom failure.",
            category="custom",
        )

        assert error.category == "custom"

    def test_custom_severity(self) -> None:
        error = ApplicationError(
            code="WARNING_CONDITION",
            message="Operation completed with a warning.",
            severity="warning",
        )

        assert error.severity == "warning"

    def test_structured_details(self) -> None:
        details = {
            "element_id": "bus-001",
            "operation": "connect",
        }

        error = ApplicationError(
            code="ELEMENT_ERROR",
            message="Element operation failed.",
            details=details,
        )

        assert error.details == details
        assert error.details["element_id"] == "bus-001"

    def test_cause_is_preserved(self) -> None:
        cause = RuntimeError("underlying failure")

        error = ApplicationError(
            code="EXECUTION_FAILED",
            message="Operation failed.",
            cause=cause,
        )

        assert error.cause is cause

    def test_error_is_immutable(self) -> None:
        error = ApplicationError(
            code="TEST_ERROR",
            message="Test operation failed.",
        )

        with pytest.raises(FrozenInstanceError):
            error.code = "CHANGED"  # type: ignore[misc]

    def test_empty_code_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            ApplicationError(
                code="",
                message="Failure.",
            )

    def test_whitespace_code_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            ApplicationError(
                code="   ",
                message="Failure.",
            )

    def test_empty_message_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            ApplicationError(
                code="TEST_ERROR",
                message="",
            )

    def test_empty_category_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            ApplicationError(
                code="TEST_ERROR",
                message="Failure.",
                category="",
            )

    def test_empty_severity_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            ApplicationError(
                code="TEST_ERROR",
                message="Failure.",
                severity="",
            )

    def test_invalid_details_are_rejected(self) -> None:
        with pytest.raises(ValueError):
            ApplicationError(
                code="TEST_ERROR",
                message="Failure.",
                details="invalid",  # type: ignore[arg-type]
            )


class TestValidationError:
    """Tests for Application validation failures."""

    def test_category(self) -> None:
        error = ValidationError(
            code="INVALID_INPUT",
            message="Input is invalid.",
        )

        assert error.code == "INVALID_INPUT"
        assert error.category == "validation"
        assert error.severity == "error"

    def test_details(self) -> None:
        error = ValidationError(
            code="INVALID_INPUT",
            message="Input is invalid.",
            details={"field": "voltage"},
        )

        assert error.details == {"field": "voltage"}


class TestDomainError:
    """Tests for domain-rule failures."""

    def test_category(self) -> None:
        error = DomainError(
            code="DOMAIN_RULE_VIOLATION",
            message="The operation violates a domain rule.",
        )

        assert error.category == "domain"


class TestResourceError:
    """Tests for missing/unavailable resources."""

    def test_category(self) -> None:
        error = ResourceError(
            code="ELEMENT_NOT_FOUND",
            message="The requested element does not exist.",
        )

        assert error.category == "resource"


class TestExecutionError:
    """Tests for expected execution failures."""

    def test_category(self) -> None:
        error = ExecutionError(
            code="EXECUTION_FAILED",
            message="The operation failed during execution.",
        )

        assert error.category == "execution"

    def test_cause(self) -> None:
        cause = RuntimeError("Core failure")

        error = ExecutionError(
            code="EXECUTION_FAILED",
            message="The operation failed.",
            cause=cause,
        )

        assert error.cause is cause
