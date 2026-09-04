# ============================================================
# File: tests/test_sld_graphics_item_factory.py
# GridForge V2 — SLD Graphics Item Factory Tests
# Author: Subhendu Mishra
# ============================================================

"""Tests for the presentation-only SLD graphics item factory."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ui.canvas.semantic_presentation_realization import PresentationSelection
from ui.canvas.sld_canvas_projection import SLDCanvasConnection, SLDCanvasNode
from ui.canvas.sld_graphics_item_factory import SLDGraphicsItemFactory
from ui.items.bus_item import BusItem
from ui.items.line_item import LineItem
from ui.core.qt import QPointF


def test_create_node_returns_bus_item_for_bus_selection() -> None:
    factory = SLDGraphicsItemFactory()
    node = SLDCanvasNode(
        node_id="bus-1",
        equipment_id="equipment-1",
        x=10.0,
        y=20.0,
        properties={"element_type": "buses"},
    )
    selection = PresentationSelection("bus")

    item = factory.create_node(node, selection)

    assert isinstance(item, BusItem)
    assert item.object_id == "bus-1"
    assert item.get_scene_position() == (10.0, 20.0)


def test_factory_rejects_missing_presentation_selection() -> None:
    factory = SLDGraphicsItemFactory()
    node = SLDCanvasNode(
        node_id="bus-1",
        equipment_id="equipment-1",
        x=10.0,
        y=20.0,
        properties={"element_type": "buses"},
    )

    with pytest.raises(TypeError, match="selection must be a PresentationSelection"):
        factory.create_node(node)


def test_factory_rejects_unsupported_presentation_selection() -> None:
    factory = SLDGraphicsItemFactory()
    node = SLDCanvasNode(
        node_id="bus-1",
        equipment_id="equipment-1",
        x=10.0,
        y=20.0,
        properties={"element_type": "buses"},
    )

    with pytest.raises(ValueError, match="Unsupported presentation representation"):
        factory.create_node(node, PresentationSelection("unsupported"))


def test_create_connection_returns_line_item() -> None:
    factory = SLDGraphicsItemFactory()
    connection = SLDCanvasConnection(
        connection_id="line-1",
        source_node_id="bus-1",
        target_node_id="bus-2",
        properties={},
    )
    source = QPointF(10.0, 20.0)
    target = QPointF(40.0, 50.0)

    item = factory.create_connection(connection, source, target)

    assert isinstance(item, LineItem)
    assert item.object_id == "line-1"


def test_factory_rejects_invalid_node_descriptor() -> None:
    factory = SLDGraphicsItemFactory()
    selection = PresentationSelection("bus")

    with pytest.raises(TypeError, match="node must be an SLDCanvasNode"):
        factory.create_node(SimpleNamespace(node_id="bus-1"), selection)


def test_factory_rejects_invalid_connection_descriptor() -> None:
    factory = SLDGraphicsItemFactory()

    with pytest.raises(TypeError, match="connection must be an SLDCanvasConnection"):
        factory.create_connection(SimpleNamespace(connection_id="line-1"), QPointF(), QPointF())
