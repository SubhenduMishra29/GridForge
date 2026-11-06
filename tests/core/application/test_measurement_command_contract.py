# ============================================================
# File: tests/core/application/test_measurement_command_contract.py
# GridForge V2 — GF-AUD-205 Measurement Command Contract Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

import importlib.util

from core.application.commands import (
    CREATE_CAPACITIVE_VOLTAGE_TRANSFORMER,
    CREATE_CURRENT_TRANSFORMER,
    CreateCapacitiveVoltageTransformerCommand,
    CreateCurrentTransformerCommand,
)


def test_measurement_transformer_commands_have_one_authoritative_module() -> None:
    assert importlib.util.find_spec(
        "core.application.commands.measurement_transformer_commands"
    ) is None


def test_authoritative_current_transformer_command_uses_endpoint_references() -> None:
    command = CreateCurrentTransformerCommand(
        transformer_id="CT-1",
        p1_endpoint=None,
        p2_endpoint=None,
        s1_endpoint=None,
        s2_endpoint=None,
    )

    assert command.command_type == CREATE_CURRENT_TRANSFORMER
    assert command.payload["transformer_id"] == "CT-1"


def test_authoritative_cvt_command_uses_the_same_command_module() -> None:
    command = CreateCapacitiveVoltageTransformerCommand(transformer_id="CVT-1")

    assert command.command_type == CREATE_CAPACITIVE_VOLTAGE_TRANSFORMER
    assert command.payload["transformer_id"] == "CVT-1"
