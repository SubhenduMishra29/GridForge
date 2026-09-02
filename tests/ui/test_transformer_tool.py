"""
GridForge V2
===========

File:
    tests/ui/test_transformer_tool.py

Purpose:
    Define the TransformerTool presentation and interaction contract.

Author:
    Subhendu Mishra
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ui.tools.transformer_tool import TransformerTool


def make_tool():
    controller = MagicMock()
    command_manager = MagicMock()
    selection_manager = MagicMock()
    snap_system = MagicMock()
    renderer_registry = MagicMock()
    return TransformerTool(
        controller=controller,
        command_manager=command_manager,
        selection_manager=selection_manager,
        snap_system=snap_system,
        renderer_registry=renderer_registry,
    ), snap_system


def test_transformer_tool_metadata_and_lifecycle():
    tool, _ = make_tool()

    assert tool.tool_id == "transformer"
    assert tool.name == "Transformer"
    assert tool.description == "Place a transformer on the SLD canvas."

    tool.activate()
    assert tool.is_active is True
    assert tool.get_state()["position"] is None
    assert tool.get_state()["preview_active"] is False

    tool.deactivate()
    assert tool.is_active is False


def test_mouse_press_captures_snapped_transformer_position():
    tool, snap_system = make_tool()
    snap_system.snap.return_value = SimpleNamespace(position=(120.0, 240.0))

    tool.activate()

    consumed = tool.mouse_press(SimpleNamespace(position=(117.0, 237.0)))

    assert consumed is True
    assert tool.get_state()["position"] == (120.0, 240.0)
    assert tool.get_state()["preview_active"] is True
    snap_system.snap.assert_called_once_with(
        (117.0, 237.0),
        allow_grid=True,
        allow_object=True,
    )


def test_mouse_release_refuses_unconfirmed_core_mutation():
    tool, snap_system = make_tool()
    snap_system.snap.return_value = SimpleNamespace(position=(120.0, 240.0))

    tool.activate()

    with pytest.raises(
        RuntimeError,
        match="No CreateTransformer command is currently exposed",
    ):
        tool.mouse_release(SimpleNamespace(position=(120.0, 240.0)))

    assert tool.get_state()["position"] == (120.0, 240.0)


def test_escape_cancels_transient_transformer_placement():
    tool, snap_system = make_tool()
    snap_system.snap.return_value = SimpleNamespace(position=(120.0, 240.0))

    tool.activate()
    tool.mouse_press(SimpleNamespace(position=(120.0, 240.0)))

    assert tool.key_press(SimpleNamespace(key=lambda: "Escape")) is True
    assert tool.get_state()["position"] is None
    assert tool.get_state()["preview_active"] is False
