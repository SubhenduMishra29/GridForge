# ============================================================
# GridForge V2 — Tool Dependency Contract Tests
# ============================================================

"""Regression tests for the presentation-only tool dependency boundary."""

from __future__ import annotations

from ui.tools.breaker_tool import BreakerTool
from ui.tools.default_tool_registry import create_default_tool_factories
from ui.tools.transformer_tool import TransformerTool


def test_default_factories_construct_model_placement_tools_without_command_manager() -> None:
    application = object()
    controller = object()
    selection_manager = object()
    snap_system = object()

    factories = create_default_tool_factories(
        controller=controller,
        application=application,
        selection_manager=selection_manager,
        snap_system=snap_system,
    )

    transformer = factories["transformer"]()
    breaker = factories["breaker"]()

    assert isinstance(transformer, TransformerTool)
    assert isinstance(breaker, BreakerTool)
    assert transformer.application is application
    assert transformer.controller is controller
    assert transformer.selection_manager is selection_manager
    assert transformer.snap_system is snap_system
    assert breaker.application is application
    assert breaker.controller is controller
    assert breaker.selection_manager is selection_manager
    assert breaker.snap_system is snap_system
    assert transformer.get_state()["has_command_manager"] is False
    assert breaker.get_state()["has_command_manager"] is False
