from __future__ import annotations

import pytest

from ui.canvas.semantic_presentation_realization import PresentationSelection, SemanticPresentationRealization
from ui.canvas.sld_canvas_projection import SLDCanvasNode
from ui.equipment.equipment_registry import EquipmentRegistry
from ui.equipment.symbol.built_in_symbol_catalogue import register_builtin_symbols
from ui.equipment.symbol.symbol_registry import SymbolRegistry


def _realization():
    equipment = EquipmentRegistry.create_default()
    symbols = SymbolRegistry()
    register_builtin_symbols(symbols)
    return SemanticPresentationRealization(equipment, symbols)


def test_supported_element_type_produces_canonical_presentation_selection():
    selection = _realization().realize(SLDCanvasNode("bus-1", "bus-1", 10.0, 20.0, {"element_type": "BUS"}))
    assert isinstance(selection, PresentationSelection)
    assert selection.semantic_type == "BUS"
    assert selection.equipment_type == "bus"
    assert selection.symbol_id == "bus"
    assert selection.symbol_instance is not None


def test_unsupported_element_type_fails_explicitly():
    node = SLDCanvasNode("unknown-1", "unknown-1", 10.0, 20.0, {"element_type": "unsupported-element"})
    with pytest.raises((KeyError, ValueError)):
        _realization().realize(node)
