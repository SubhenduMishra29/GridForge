# ============================================================
# File: tests/test_semantic_presentation_realization.py
# GridForge V2 — Semantic Presentation Realization Tests
# Author: Subhendu Mishra
# ============================================================

"""Contract tests for semantic SLD presentation realization."""

from __future__ import annotations

import pytest

from ui.canvas.semantic_presentation_realization import (
    PresentationSelection,
    SemanticPresentationRealization,
)
from ui.canvas.sld_canvas_projection import SLDCanvasNode


def test_supported_element_type_produces_presentation_selection() -> None:
    realization = SemanticPresentationRealization()
    node = SLDCanvasNode(
        node_id="bus-1",
        equipment_id="bus-1",
        x=10.0,
        y=20.0,
        properties={"element_type": "buses"},
    )

    selection = realization.realize(node)

    assert isinstance(selection, PresentationSelection)
    assert selection != "buses"


def test_unsupported_element_type_fails_explicitly() -> None:
    realization = SemanticPresentationRealization()
    node = SLDCanvasNode(
        node_id="unknown-1",
        equipment_id="unknown-1",
        x=10.0,
        y=20.0,
        properties={"element_type": "unsupported-element"},
    )

    with pytest.raises(ValueError, match="unsupported-element"):
        realization.realize(node)
