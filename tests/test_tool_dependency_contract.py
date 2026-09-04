# ============================================================
# GridForge V2 — Tool Dependency Contract Tests
# ============================================================

"""Regression tests for the presentation-only tool dependency boundary."""

from __future__ import annotations

from ui.tools.breaker_tool import BreakerTool
from ui.tools.default_tool_registry import create_default_tool_factories
from ui.tools.transformer_tool import TransformerTool


def test_default_factories_construct_model_placement_tools_without_renderer_registry() -> None:
    factories = create_default_tool_factories(
        controller=object(),
        command_manager=None,
        selection_manager=object(),
        snap_system=object(),
    )

    transformer = factories["transformer"]()
    breaker = factories["breaker"]()

    assert isinstance(transformer, TransformerTool)
    assert isinstance(breaker, BreakerTool)
    assert transformer.get_state()["has_command_manager"] is False
    assert breaker.get_state()["has_command_manager"] is False
