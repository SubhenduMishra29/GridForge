# ============================================================
# File: tests/ui/tools/test_equipment_tool_command_paths.py
# GridForge V2 — Equipment Tool Command Path Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from types import SimpleNamespace

from ui.tools.cable_tool import CableTool
from ui.tools.transformer_tool import TransformerTool


class FakeApplication:
    def __init__(self) -> None:
        self.commands = []

    def execute(self, command):
        self.commands.append(command)
        return "accepted"


class FakeSnapSystem:
    def __init__(self) -> None:
        self.current_id = "bus-1"

    def snap(self, position, *, allow_grid, allow_object):
        return SimpleNamespace(
            position=position,
            object_id=self.current_id,
            source=type("BusItem", (), {})(),
            snap_type=SimpleNamespace(name="OBJECT"),
        )


class FakeSelectionManager:
    pass


def test_cable_tool_executes_create_cable_command_through_application():
    application = FakeApplication()
    snap = FakeSnapSystem()
    tool = CableTool(
        controller=object(),
        application=application,
        selection_manager=FakeSelectionManager(),
        snap_system=snap,
    )
    tool.set_engineering_parameters(length_km=1.5, r1_ohm_per_km=0.2, x1_ohm_per_km=0.1)
    tool.activate()

    tool.mouse_press((0.0, 0.0))
    snap.current_id = "bus-2"
    assert tool.mouse_press((10.0, 0.0)) is True

    command = application.commands[-1]
    assert command.command_type == "model.create_cable"
    assert command.payload["endpoint_from"].object_id == "bus-1"
    assert command.payload["endpoint_to"].object_id == "bus-2"
    assert command.payload["length_km"] == 1.5


def test_transformer_tool_executes_create_transformer_command_through_application():
    application = FakeApplication()
    snap = FakeSnapSystem()
    tool = TransformerTool(
        controller=object(),
        application=application,
        selection_manager=FakeSelectionManager(),
        snap_system=snap,
    )
    tool.set_engineering_parameters(r=0.01, x=0.08, impedance_basis="from_side_nominal_voltage")
    tool.activate()

    tool.mouse_press((0.0, 0.0))
    snap.current_id = "bus-2"
    assert tool.mouse_press((10.0, 0.0)) is True

    command = application.commands[-1]
    assert command.command_type == "model.create_transformer"
    assert command.payload["endpoint_from"].object_id == "bus-1"
    assert command.payload["endpoint_to"].object_id == "bus-2"
    assert command.payload["r"] == 0.01
    assert command.payload["x"] == 0.08
