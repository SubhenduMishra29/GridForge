# ============================================================
# File: tests/ui/tools/test_line_tool_engineering_configuration.py
# GridForge V2 — Line Tool Engineering Configuration Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ui.tools.line_tool import LineTool


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


def test_line_tool_uses_ui_entered_parameters_in_canonical_command():
    application = FakeApplication()
    snap = FakeSnapSystem()
    controller = object()
    tool = LineTool(
        controller=controller,
        application=application,
        selection_manager=object(),
        snap_system=snap,
    )
    tool.set_engineering_parameters(
        resistance_ohm=0.2,
        reactance_ohm=0.4,
        shunt_susceptance_siemens=0.001,
        rate_mva=100.0,
    )
    tool.activate()

    tool.mouse_press((0.0, 0.0))
    snap.current_id = "bus-2"
    assert tool.mouse_press((10.0, 0.0)) is True

    command = application.commands[-1]
    assert command.command_type == "model.create_line"
    assert command.payload["resistance_ohm"] == 0.2
    assert command.payload["reactance_ohm"] == 0.4
    assert command.payload["shunt_susceptance_siemens"] == 0.001
    assert command.payload["rate_mva"] == 100.0


def test_line_tool_rejects_missing_engineering_parameters():
    tool = LineTool(
        controller=object(),
        application=FakeApplication(),
        selection_manager=object(),
        snap_system=FakeSnapSystem(),
    )
    tool.activate()
    tool.on_mouse_press((0.0, 0.0))
    tool.get_snap_system().current_id = "bus-2"

    with pytest.raises(RuntimeError, match="Line engineering parameters"):
        tool.on_mouse_press((10.0, 0.0))


def test_line_tool_does_not_read_engineering_parameters_from_controller():
    class ControllerWithForbiddenElectricalState:
        line_parameters = {
            "r": 1.0,
            "x": 2.0,
            "rate_mva": 3.0,
        }

    application = FakeApplication()
    snap = FakeSnapSystem()
    tool = LineTool(
        controller=ControllerWithForbiddenElectricalState(),
        application=application,
        selection_manager=object(),
        snap_system=snap,
    )
    tool.activate()
    tool.on_mouse_press((0.0, 0.0))
    snap.current_id = "bus-2"

    with pytest.raises(RuntimeError, match="Line engineering parameters"):
        tool.on_mouse_press((10.0, 0.0))
