# ============================================================
# File: tests/ui/test_bus_creation_command_contract.py
# GridForge V2 — Bus Creation Command Boundary Tests
# ============================================================

from __future__ import annotations

from types import SimpleNamespace

from core.application.commands.model_commands import CreateBusCommand
from ui.tools.bus_tool import BusTool


class _CommandManager:
    def __init__(self) -> None:
        self.commands = []

    def execute(self, command):
        self.commands.append(command)
        return command


class _SnapSystem:
    def snap(self, position, *, allow_grid, allow_object):
        return SimpleNamespace(position=(100.0, 200.0))


def test_create_bus_command_matches_authoritative_bus_contract():
    command = CreateBusCommand(
        bus_id="bus-1",
        name="Bus 1",
        nominal_voltage_kv=11.0,
        voltage_pu=1.0,
        angle_deg=0.0,
        frequency_hz=50.0,
        in_service=True,
    )

    assert command.payload == {
        "bus_id": "bus-1",
        "name": "Bus 1",
        "nominal_voltage_kv": 11.0,
        "voltage_pu": 1.0,
        "angle_deg": 0.0,
        "frequency_hz": 50.0,
        "in_service": True,
    }


def test_bus_tool_submits_authoritative_create_bus_command_on_release():
    command_manager = _CommandManager()
    tool = BusTool(
        controller=object(),
        command_manager=command_manager,
        selection_manager=object(),
        snap_system=_SnapSystem(),
    )
    tool.activate()

    handled = tool.on_mouse_release({"position": (100.0, 200.0)})

    assert handled is True
    assert len(command_manager.commands) == 1

    command = command_manager.commands[0]
    assert isinstance(command, CreateBusCommand)
    assert command.command_type == "model.create_bus"
    assert command.payload["bus_id"]
    assert command.payload["name"] == "Bus"
    assert command.payload["nominal_voltage_kv"] == 0.0
    assert command.payload["voltage_pu"] == 1.0
    assert command.payload["angle_deg"] == 0.0
    assert command.payload["frequency_hz"] == 50.0
    assert command.payload["in_service"] is True
    assert "voltage" not in command.payload
    assert "angle" not in command.payload
