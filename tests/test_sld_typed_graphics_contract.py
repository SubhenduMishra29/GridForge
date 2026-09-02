# ============================================================
# File: tests/test_sld_typed_graphics_contract.py
# GridForge V2 — Unified Typed SLD Graphics Contract Tests
# Author: Subhendu Mishra
# ============================================================

"""Contract tests for typed graphics on the unified SLD projection path."""

from __future__ import annotations

import inspect

from ui.canvas import sld_canvas_render_system
from ui.items.bus_item import BusItem
from ui.items.line_item import LineItem


def test_bus_item_has_no_authoritative_core_model_contract() -> None:
    """BusItem must be constructible from presentation data only."""
    parameters = inspect.signature(BusItem.__init__).parameters

    assert "model" not in parameters


def test_line_item_has_no_controller_or_core_line_contract() -> None:
    """LineItem must consume renderer-neutral visual data only."""
    parameters = inspect.signature(LineItem.__init__).parameters

    assert "controller" not in parameters
    assert "line" not in parameters


def test_sld_canvas_render_system_realizes_typed_graphics_items() -> None:
    """The unified SLD render boundary must own typed-item realization."""
    source = inspect.getsource(sld_canvas_render_system.SLDCanvasRenderSystem)

    assert "BusItem" in source
    assert "LineItem" in source
    assert "SLDCanvasSnapshot" in source
