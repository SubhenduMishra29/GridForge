from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from core.application.services.insertion_contract import INSERTION_CONTRACTS
from ui.canvas.symbol_preview_item import SymbolPreviewItem
from ui.core.qt import QApplication, QGraphicsEllipseItem, QGraphicsLineItem, Qt
from ui.equipment.symbol.symbol_definition import SymbolDefinition
from ui.tools.electrical_insertion_tool import ElectricalInsertionTool


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    return app if app is not None else QApplication([])


class RecordingPainter:
    def __init__(self):
        self.brush = None
        self.pen = None

    def setRenderHint(self, *_args):
        pass

    def setBrush(self, brush):
        self.brush = brush

    def setFont(self, *_args):
        pass

    def setPen(self, pen):
        self.pen = pen

    def drawLine(self, *_args):
        pass


class FakePreviewLayer:
    def __init__(self):
        self.items = {}

    def clear_owner(self, owner):
        self.items.pop(owner, None)

    def add_items_for_owner(self, owner, items):
        self.items[owner] = tuple(items)


class FakeSymbolRegistry:
    def __init__(self, definition):
        self.definition = definition

    def require(self, _equipment_type):
        return self.definition


def _breaker_definition():
    return SymbolDefinition(
        symbol_id="preview-breaker",
        display_name="Preview Breaker",
        width=20.0,
        height=12.0,
        terminal_anchors={"from": (-10.0, 0.0), "to": (10.0, 0.0)},
        primitives=({"kind": "line", "x1": -8.0, "y1": 0.0, "x2": 8.0, "y2": 0.0},),
    )


def test_insertion_symbol_preview_is_solid_and_translucent(qapp):
    definition = _breaker_definition()
    item = SymbolPreviewItem(
        definition,
        position=(15.0, 20.0),
        terminal_names=INSERTION_CONTRACTS["breaker"].terminal_mapping,
        element_type="breaker",
        preview_opacity=0.55,
    )

    painter = RecordingPainter()
    item.paint(painter, None)

    assert item.opacity() == pytest.approx(0.55)
    assert painter.brush.style() == Qt.BrushStyle.SolidPattern
    assert painter.pen.style() == Qt.PenStyle.SolidLine


def test_insertion_preview_has_translucent_route_halves_and_terminal_markers(qapp):
    definition = _breaker_definition()
    layer = FakePreviewLayer()
    tool = ElectricalInsertionTool(
        controller=SimpleNamespace(),
        application=object(),
        selection_manager=object(),
        snap_system=object(),
        preview_layer=layer,
        symbol_registry=FakeSymbolRegistry(definition),
    )
    tool.begin("breaker", orientation=0.0)
    target = {
        "closest_point": (15.0, 20.0),
        "source": (0.0, 20.0),
        "target": (30.0, 20.0),
        "route": ((10.0, 20.0), (20.0, 20.0)),
        "segment_index": 1,
    }

    tool._show_preview(target)

    items = layer.items[tool._preview_owner]
    lines = [item for item in items if isinstance(item, QGraphicsLineItem)]
    markers = [item for item in items if isinstance(item, QGraphicsEllipseItem)]
    symbols = [item for item in items if isinstance(item, SymbolPreviewItem)]

    assert len(lines) == 6
    assert all(item.pen().style() == Qt.PenStyle.SolidLine for item in lines)
    assert all(item.opacity() == pytest.approx(0.62) for item in lines)
    assert len(markers) == 2
    assert all(item.pen().style() == Qt.PenStyle.SolidLine for item in markers)
    assert all(item.opacity() == pytest.approx(0.78) for item in markers)
    assert len(symbols) == 1
    assert symbols[0].opacity() == pytest.approx(0.55)

    marker_centers = {
        (
            round(item.rect().center().x(), 6),
            round(item.rect().center().y(), 6),
        )
        for item in markers
    }
    assert marker_centers == {(5.0, 20.0), (25.0, 20.0)}
