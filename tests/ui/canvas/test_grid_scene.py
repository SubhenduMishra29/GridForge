# ============================================================
# File: tests/ui/canvas/test_grid_scene.py
# GridForge V2 — GridScene Tests
# ============================================================
"""
Tests for ui.canvas.grid_scene.GridScene.

GridScene is a passive QGraphicsScene boundary. These tests
verify scene geometry, graphical projection access, lookup,
selection projection handling, diagnostics, validation, and
reset behavior without introducing Core/domain dependencies.
"""

from __future__ import annotations

import pytest

from ui.canvas.grid_scene import GridScene
from ui.core.qt import (
    QGraphicsRectItem,
    QPointF,
    QRectF,
)


# ============================================================
# CONSTRUCTION
# ============================================================


def test_grid_scene_initial_state(qapp):
    scene = GridScene()

    rect = scene.get_canvas_rect()

    assert rect == GridScene.DEFAULT_SCENE_RECT
    assert scene.get_item_count() == 0
    assert scene.has_content() is False


def test_grid_scene_default_scene_rect_is_independent_copy(qapp):
    scene = GridScene()

    rect = scene.get_canvas_rect()
    rect.setX(1234.0)

    assert scene.get_canvas_rect().x() == -5000.0


# ============================================================
# SCENE RECTANGLE
# ============================================================


def test_set_canvas_rect_updates_scene_geometry(qapp):
    scene = GridScene()

    rect = QRectF(-100.0, -200.0, 500.0, 600.0)

    scene.set_canvas_rect(rect)

    assert scene.get_canvas_rect() == rect
    assert scene.sceneRect() == rect


def test_set_canvas_rect_copies_input(qapp):
    scene = GridScene()

    rect = QRectF(10.0, 20.0, 300.0, 400.0)
    scene.set_canvas_rect(rect)

    rect.setX(9999.0)

    assert scene.get_canvas_rect().x() == 10.0


@pytest.mark.parametrize(
    "rect",
    [
        None,
        QRectF(),
        QRectF(0.0, 0.0, 0.0, 10.0),
        QRectF(0.0, 0.0, 10.0, 0.0),
        QRectF(0.0, 0.0, -10.0, 10.0),
        QRectF(0.0, 0.0, 10.0, -10.0),
    ],
)
def test_set_canvas_rect_rejects_invalid_rectangles(
    qapp,
    rect,
):
    scene = GridScene()

    if rect is None:
        with pytest.raises(ValueError):
            scene.set_canvas_rect(rect)
    else:
        with pytest.raises(ValueError):
            scene.set_canvas_rect(rect)


def test_set_canvas_rect_rejects_non_qrectf(qapp):
    scene = GridScene()

    with pytest.raises(TypeError):
        scene.set_canvas_rect(
            (-100.0, -100.0, 200.0, 200.0)
        )


def test_invalid_canvas_rect_does_not_change_existing_state(qapp):
    scene = GridScene()

    original = scene.get_canvas_rect()

    with pytest.raises(ValueError):
        scene.set_canvas_rect(
            QRectF(0.0, 0.0, 0.0, 100.0)
        )

    assert scene.get_canvas_rect() == original


# ============================================================
# CONTENT / ITEM ACCESS
# ============================================================


def test_scene_item_access(qapp):
    scene = GridScene()

    item = QGraphicsRectItem(
        QRectF(0.0, 0.0, 100.0, 50.0)
    )
    scene.addItem(item)

    assert scene.has_content() is True
    assert scene.get_item_count() == 1
    assert scene.get_items() == (item,)


def test_get_items_returns_snapshot(qapp):
    scene = GridScene()

    item = QGraphicsRectItem(
        QRectF(0.0, 0.0, 10.0, 10.0)
    )
    scene.addItem(item)

    items = scene.get_items()

    assert isinstance(items, tuple)
    assert items == (item,)


def test_get_content_rect_reflects_graphical_content(qapp):
    scene = GridScene()

    item = QGraphicsRectItem(
        QRectF(10.0, 20.0, 100.0, 50.0)
    )
    scene.addItem(item)

    content = scene.get_content_rect()

    assert content.contains(QPointF(10.0, 20.0))
    assert content.width() >= 100.0
    assert content.height() >= 50.0


# ============================================================
# OBJECT-ID LOOKUP
# ============================================================


def test_find_item_by_object_id(qapp):
    scene = GridScene()

    first = QGraphicsRectItem(
        QRectF(0.0, 0.0, 10.0, 10.0)
    )
    second = QGraphicsRectItem(
        QRectF(20.0, 20.0, 10.0, 10.0)
    )

    first.object_id = "BUS-001"
    second.object_id = "LINE-001"

    scene.addItem(first)
    scene.addItem(second)

    assert scene.find_item_by_object_id("BUS-001") is first
    assert scene.find_item_by_object_id("LINE-001") is second


def test_find_item_by_object_id_returns_none_when_missing(qapp):
    scene = GridScene()

    assert scene.find_item_by_object_id("UNKNOWN") is None
    assert scene.find_item_by_object_id(None) is None


def test_find_items_by_object_id_returns_all_matches(qapp):
    scene = GridScene()

    first = QGraphicsRectItem()
    second = QGraphicsRectItem()
    third = QGraphicsRectItem()

    first.object_id = "BUS-001"
    second.object_id = "BUS-001"
    third.object_id = "LINE-001"

    scene.addItem(first)
    scene.addItem(second)
    scene.addItem(third)

    matches = scene.find_items_by_object_id("BUS-001")

    assert len(matches) == 2
    assert set(matches) == {first, second}


def test_find_items_by_object_id_returns_empty_for_missing_id(qapp):
    scene = GridScene()

    assert scene.find_items_by_object_id(None) == ()
    assert scene.find_items_by_object_id("UNKNOWN") == ()


# ============================================================
# GRAPHICAL SELECTION
# ============================================================


def test_clear_graphical_selection(qapp):
    scene = GridScene()

    first = QGraphicsRectItem()
    second = QGraphicsRectItem()

    first.setFlag(
        QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable,
        True,
    )
    second.setFlag(
        QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable,
        True,
    )

    scene.addItem(first)
    scene.addItem(second)

    first.setSelected(True)
    second.setSelected(True)

    assert first.isSelected()
    assert second.isSelected()

    scene.clear_graphical_selection()

    assert first.isSelected() is False
    assert second.isSelected() is False


# ============================================================
# SCENE COORDINATE HELPERS
# ============================================================


@pytest.mark.parametrize(
    "point, expected",
    [
        (QPointF(0.0, 0.0), True),
        (QPointF(-5000.0, -5000.0), True),
        (QPointF(5000.0, 5000.0), True),
        (QPointF(6000.0, 0.0), False),
        (QPointF(0.0, -6000.0), False),
    ],
)
def test_contains_scene_point(qapp, point, expected):
    scene = GridScene()

    assert scene.contains_scene_point(point) is expected


def test_contains_scene_point_rejects_none(qapp):
    scene = GridScene()

    with pytest.raises(ValueError):
        scene.contains_scene_point(None)


def test_contains_scene_point_rejects_invalid_point(qapp):
    scene = GridScene()

    with pytest.raises(TypeError):
        scene.contains_scene_point((0.0, 0.0))


# ============================================================
# CLEAR / RESET
# ============================================================


def test_clear_items_removes_only_graphical_items(qapp):
    scene = GridScene()

    scene.set_canvas_rect(
        QRectF(-100.0, -100.0, 200.0, 200.0)
    )
    scene.addItem(QGraphicsRectItem())

    scene.clear_items()

    assert scene.get_item_count() == 0
    assert scene.get_canvas_rect() == QRectF(
        -100.0,
        -100.0,
        200.0,
        200.0,
    )


def test_reset_scene_clears_items_and_restores_default_rect(qapp):
    scene = GridScene()

    scene.set_canvas_rect(
        QRectF(-100.0, -100.0, 200.0, 200.0)
    )
    scene.addItem(QGraphicsRectItem())

    scene.reset_scene()

    assert scene.get_item_count() == 0
    assert scene.get_canvas_rect() == GridScene.DEFAULT_SCENE_RECT
    assert scene.sceneRect() == GridScene.DEFAULT_SCENE_RECT


# ============================================================
# DIAGNOSTICS / REPRESENTATION
# ============================================================


def test_get_state(qapp):
    scene = GridScene()

    state = scene.get_state()

    assert state["item_count"] == 0
    assert state["has_content"] is False
    assert state["scene_rect"] == GridScene.DEFAULT_SCENE_RECT
    assert isinstance(state["content_rect"], QRectF)


def test_get_state_reflects_content(qapp):
    scene = GridScene()

    scene.addItem(
        QGraphicsRectItem(
            QRectF(0.0, 0.0, 20.0, 30.0)
        )
    )

    state = scene.get_state()

    assert state["item_count"] == 1
    assert state["has_content"] is True


def test_repr_contains_diagnostic_information(qapp):
    scene = GridScene()

    representation = repr(scene)

    assert representation.startswith("GridScene(")
    assert "items=0" in representation
    assert "rect=(" in representation


# ============================================================
# PUBLIC API
# ============================================================


def test_public_api_exports_grid_scene():
    from ui.canvas import grid_scene

    assert "GridScene" in grid_scene.__all__
