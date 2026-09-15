# ============================================================
# File: tests/core/application/test_protection_execution.py
# GridForge V2 — Protection Application Boundary Tests
# Author: Subhendu Mishra
# ============================================================

from uuid import UUID

import pytest

from core.application.commands.breaker_commands import TripBreakerCommand
from core.application.protection_execution import ProtectionExecutionService
from core.application.results import ApplicationResult
from core.protection.decision import ProtectionDecision


def _decision(*, trip: bool) -> ProtectionDecision:
    return ProtectionDecision(
        relay_id="R1",
        element_id="OC50",
        function_code="50",
        pickup=trip,
        operate=trip,
        trip_request=trip,
        valid=True,
    )


def test_actionable_decision_is_translated_to_existing_trip_command() -> None:
    calls = []

    def execute(command):
        calls.append(command)
        return ApplicationResult.success_result(message="tripped")

    service = ProtectionExecutionService(execute, breaker_resolver=lambda _: "BRK-1")
    result = service.execute([_decision(trip=True)])

    assert len(result.trip_commands) == 1
    assert isinstance(result.trip_commands[0], TripBreakerCommand)
    assert result.trip_commands[0].payload["breaker_id"] == "BRK-1"
    assert calls == [result.trip_commands[0]]


def test_non_actionable_decision_never_creates_trip_command() -> None:
    calls = []
    service = ProtectionExecutionService(calls.append, breaker_resolver=lambda _: "BRK-1")

    result = service.execute([_decision(trip=False)])

    assert result.trip_commands == ()
    assert calls == []


def test_trip_requires_explicit_breaker_resolution() -> None:
    service = ProtectionExecutionService(lambda command: ApplicationResult.success_result())

    result = service.execute([_decision(trip=True)])

    assert result.trip_commands == ()
    assert "no explicit breaker resolver" in result.diagnostics[0]


def test_trip_execution_failure_is_reported_without_bypassing_application() -> None:
    def execute(command):
        raise RuntimeError("command failure")

    service = ProtectionExecutionService(execute, breaker_resolver=lambda _: "BRK-1")
    result = service.execute([_decision(trip=True)])

    assert len(result.trip_commands) == 1
    assert result.application_results == ()
    assert "execution failed" in result.diagnostics[0]


def test_decision_input_is_strictly_typed() -> None:
    service = ProtectionExecutionService(lambda command: ApplicationResult.success_result())

    with pytest.raises(TypeError, match="ProtectionDecision"):
        service.execute([object()])
