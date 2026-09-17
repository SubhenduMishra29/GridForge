"""Deferred architecture-contract tests for Control and Protection remediation.

Author: Subhendu Mishra

These tests are intentionally added without execution in this remediation
phase. They document the contracts that must be verified when the test suite
is enabled.
"""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from core.application.control_dispatch import ControlCommandTranslator
from core.application.control_signal_mapping import (
    ControlSignalBinding,
    ControlSignalDestination,
    ControlSignalMapping,
    ControlSignalSource,
)
from core.application.read_service import ReadService
from core.control.decision import ControlActionType, ControlDecision, ControlTargetType


def test_control_decision_accepts_supported_non_breaker_targets():
    decision = ControlDecision(
        control_id="motor-start",
        action_type=ControlActionType.START,
        target_equipment_id="M1",
        target_equipment_type=ControlTargetType.MOTOR.value,
        reason="start command",
        simulation_time=2.0,
    )

    assert decision.target_equipment_type == "motor"
    assert decision.action_type is ControlActionType.START


def test_control_dispatch_translates_switch_intent_to_existing_semantic_command():
    decision = ControlDecision(
        control_id="switch-open",
        action_type=ControlActionType.OPEN,
        target_equipment_id="SW1",
        target_equipment_type=ControlTargetType.SWITCH.value,
        reason="open command",
        simulation_time=3.0,
    )

    command = ControlCommandTranslator.to_command(decision)

    assert command.command_type == "model.open_switch"
    assert command.payload["switch_id"] == "SW1"


def test_control_dispatch_translates_motor_start_to_canonical_update_contract():
    decision = ControlDecision(
        control_id="motor-start",
        action_type=ControlActionType.START,
        target_equipment_id="M1",
        target_equipment_type=ControlTargetType.MOTOR.value,
        reason="start command",
        simulation_time=4.0,
    )

    command = ControlCommandTranslator.to_command(decision)

    assert command.command_type == "model.update_motor"
    assert command.payload == {"motor_id": "M1", "rated_mva": None, "rated_kv": None,
                               "power_factor": None, "p": None, "q": None,
                               "efficiency": None, "slip": None,
                               "starting_current_pu": None, "running": True,
                               "in_service": None, "name": None}


def test_control_signal_mapping_is_deterministic_and_resolves_read_models():
    source = ControlSignalSource("core", "breaker", "B1", "closed")
    destination = ControlSignalDestination("CTRL1", "CONTACT1", "IN")
    mapping = ControlSignalMapping((ControlSignalBinding(source, destination),))

    read_service = Mock(spec=ReadService)
    read_service.element.return_value = SimpleNamespace(attributes={"closed": True})

    result = mapping.resolve(read_service)

    assert result.external_inputs == {"CONTACT1": {"IN": True}}
    assert result.bindings == mapping.bindings
    read_service.element.assert_called_once_with("breaker", "B1")


def test_control_signal_mapping_rejects_duplicate_destinations():
    destination = ControlSignalDestination("CTRL1", "CONTACT1", "IN")
    first = ControlSignalBinding(ControlSignalSource("core", "breaker", "B1", "closed"), destination)
    second = ControlSignalBinding(ControlSignalSource("core", "switch", "S1", "closed"), destination)

    with pytest.raises(ValueError, match="one canonical engineering source"):
        ControlSignalMapping((first, second))
