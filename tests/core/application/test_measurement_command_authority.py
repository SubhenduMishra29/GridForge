# ============================================================
# File: tests/core/application/test_measurement_command_authority.py
# GridForge V2 — GF-AUD-205 Measurement Command Authority Tests
# Author: Subhendu Mishra
# ============================================================

from pathlib import Path

from core.application.commands.measurement_commands import (
    CreateCurrentTransformerCommand,
    CreateCapacitiveVoltageTransformerCommand,
)


def test_measurement_commands_are_imported_from_canonical_module() -> None:
    assert CreateCurrentTransformerCommand.__module__ == "core.application.commands.measurement_commands"
    assert CreateCapacitiveVoltageTransformerCommand.__module__ == "core.application.commands.measurement_commands"


def test_duplicate_measurement_transformer_module_is_absent() -> None:
    path = Path(__file__).parents[3] / "core" / "application" / "commands" / "measurement_transformer_commands.py"
    assert not path.exists()
