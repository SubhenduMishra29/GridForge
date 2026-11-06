from __future__ import annotations

import pytest

from ui.core.selection_manager import SelectionManager


class FakeItem:
    def __init__(self, object_id=None, selected=False):
        self.object_id = object_id
        self.selected = selected

    def setSelected(self, value):
        self.selected = value


class FakeScene:
    def __init__(self, items=()):
        self._items = list(items)

    def items(self):
        return list(self._items)


def test_initial_state():
    manager = SelectionManager()
    assert manager.selected_ids == ()
    assert manager.has_selection() is False
    assert manager.get_state()["has_scene"] is False


def test_selection_is_ui_local_and_snapshot():
    manager = SelectionManager()
    manager.select("bus-1")
    manager.add_to_selection("line-1")
    assert manager.selected_ids == ("bus-1", "line-1")
    assert manager.is_selected("bus-1") is True
    assert manager.is_selected("missing") is False


def test_single_selection_replaces_previous_selection():
    manager = SelectionManager()
    manager.select("bus-1")
    manager.select_single("line-1")
    assert manager.selected_ids == ("line-1",)


def test_toggle_selection():
    manager = SelectionManager()
    manager.toggle_selection("bus-1")
    assert manager.selected_ids == ("bus-1",)
    manager.toggle_selection("bus-1")
    assert manager.selected_ids == ()


def test_clear_is_local():
    manager = SelectionManager()
    manager.select("bus-1")
    manager.add_to_selection("line-1")
    manager.clear()
    assert manager.selected_ids == ()
    assert manager.has_selection() is False


def test_invalid_selection_inputs():
    manager = SelectionManager()
    with pytest.raises(ValueError):
        manager.select(None)
    with pytest.raises(TypeError):
        manager.select("bus-1", multi="yes")
    with pytest.raises(ValueError):
        manager.toggle_selection(None)


def test_graphics_projection_uses_selection_manager_authority():
    first = FakeItem("bus-1")
    second = FakeItem("line-1", selected=True)
    manager = SelectionManager(FakeScene([first, second]))
    manager.select("bus-1")
    assert first.selected is True
    assert second.selected is False
    manager.clear()
    assert first.selected is False
    assert second.selected is False


def test_graphics_selection_is_not_authoritative():
    item = FakeItem("bus-1", selected=True)
    manager = SelectionManager(FakeScene([item]))
    assert manager.selected_ids == ()
    assert manager.get_selected_items() == ()


def test_lookup_uses_presentation_scene_only():
    first = FakeItem("bus-1")
    second = FakeItem("line-1")
    manager = SelectionManager(FakeScene([first, second]))
    assert manager.get_item_for_id("line-1") is second
    assert manager.get_item_for_id("missing") is None
    assert manager.get_items_for_ids(["line-1", "bus-1"]) == (first, second)


def test_scene_can_be_bound_after_construction():
    item = FakeItem("bus-1")
    manager = SelectionManager()
    manager.set_scene(FakeScene([item]))
    manager.select("bus-1")
    assert manager.get_scene() is not None
    assert item.selected is True


def test_reset_graphics_does_not_change_semantic_selection():
    item = FakeItem("bus-1", selected=True)
    manager = SelectionManager(FakeScene([item]))
    manager.select("bus-1")
    manager.reset_graphics()
    assert manager.selected_ids == ("bus-1",)
    assert item.selected is False


def test_repr_describes_local_state():
    manager = SelectionManager()
    manager.select("bus-1")
    representation = repr(manager)
    assert "SelectionManager(" in representation
    assert "selected=1" in representation
