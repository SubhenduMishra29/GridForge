# ============================================================
# File: tests/ui/core/test_selection_manager.py
# GridForge V2 — SelectionManager Contract Tests
# ============================================================

from __future__ import annotations

import pytest

from ui.core.selection_manager import SelectionManager


# ============================================================
# TEST DOUBLES
# ============================================================


class FakeController:
    """Minimal Controller contract used by SelectionManager tests."""

    def __init__(self):
        self.selected_ids = []
        self.select_calls = []
        self.clear_selection_calls = 0

    def select(self, object_id, multi=False):
        self.select_calls.append(
            (object_id, multi)
        )

        if multi:
            if object_id not in self.selected_ids:
                self.selected_ids.append(object_id)
        else:
            if self.selected_ids == [object_id]:
                return

            self.selected_ids = [object_id]

    def clear_selection(self):
        self.clear_selection_calls += 1
        self.selected_ids.clear()


class FakeItem:
    """Minimal graphics-item projection contract."""

    def __init__(
        self,
        object_id=None,
        selected=False,
    ):
        self.object_id = object_id
        self.selected = selected
        self.set_selected_calls = []

    def setSelected(self, value):
        self.set_selected_calls.append(value)
        self.selected = value


class FakeScene:
    """Minimal scene contract used by SelectionManager."""

    def __init__(self, items=None):
        self._items = list(items or [])
        self.items_calls = 0

    def items(self):
        self.items_calls += 1
        return list(self._items)


class BrokenScene:
    """Scene-like object without the required items() API."""


class FakeControllerWithoutSelect:
    selected_ids = []


class FakeControllerWithoutSelectedIds:
    def select(self, object_id, multi=False):
        pass


class FakeControllerWithoutClear:
    def __init__(self):
        self.selected_ids = []

    def select(self, object_id, multi=False):
        pass


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def controller():
    return FakeController()


@pytest.fixture
def manager(controller):
    return SelectionManager(controller)


# ============================================================
# CONSTRUCTION
# ============================================================


def test_requires_controller():
    with pytest.raises(ValueError):
        SelectionManager(None)


def test_requires_controller_select():
    with pytest.raises(TypeError):
        SelectionManager(
            FakeControllerWithoutSelect()
        )


def test_requires_controller_selected_ids():
    with pytest.raises(TypeError):
        SelectionManager(
            FakeControllerWithoutSelectedIds()
        )


def test_accepts_controller_without_scene(controller):
    manager = SelectionManager(controller)

    assert manager.controller is controller
    assert manager.scene is None


def test_accepts_initial_scene(controller):
    scene = FakeScene()

    manager = SelectionManager(
        controller,
        scene,
    )

    assert manager.controller is controller
    assert manager.scene is scene


# ============================================================
# AUTHORITATIVE SELECTION
# ============================================================


def test_initial_selected_ids_are_empty(manager):
    assert manager.get_selected_ids() == ()


def test_selected_ids_property_returns_snapshot(
    controller,
):
    controller.selected_ids = ["a", "b"]

    manager = SelectionManager(controller)

    result = manager.selected_ids

    assert result == ("a", "b")
    assert isinstance(result, tuple)


def test_get_selected_ids_returns_snapshot(
    controller,
):
    controller.selected_ids = ["a", "b"]

    manager = SelectionManager(controller)

    result = manager.get_selected_ids()

    assert result == ("a", "b")
    assert isinstance(result, tuple)


def test_selected_ids_does_not_expose_controller_list(
    controller,
):
    controller.selected_ids = ["a"]

    manager = SelectionManager(controller)

    result = manager.selected_ids

    controller.selected_ids.append("b")

    assert result == ("a",)
    assert manager.selected_ids == ("a", "b")


def test_none_selected_ids_is_normalized_to_empty_tuple(
    controller,
):
    controller.selected_ids = None

    manager = SelectionManager(controller)

    assert manager.get_selected_ids() == ()


def test_has_selection_false_initially(manager):
    assert manager.has_selection() is False


def test_has_selection_reflects_controller(
    controller,
):
    manager = SelectionManager(controller)

    controller.selected_ids = ["bus-1"]

    assert manager.has_selection() is True


def test_is_selected_returns_false_for_none(
    controller,
):
    controller.selected_ids = ["bus-1"]

    manager = SelectionManager(controller)

    assert manager.is_selected(None) is False


def test_is_selected_reflects_controller(
    controller,
):
    controller.selected_ids = [
        "bus-1",
        "line-1",
    ]

    manager = SelectionManager(controller)

    assert manager.is_selected("bus-1") is True
    assert manager.is_selected("line-1") is True
    assert manager.is_selected("bus-2") is False


# ============================================================
# SELECTION MUTATION
# ============================================================


def test_select_delegates_to_controller(
    controller,
):
    manager = SelectionManager(controller)

    manager.select(
        "bus-1",
        multi=False,
    )

    assert controller.select_calls == [
        ("bus-1", False)
    ]


def test_select_multi_delegates_to_controller(
    controller,
):
    manager = SelectionManager(controller)

    manager.select(
        "bus-1",
        multi=True,
    )

    assert controller.select_calls == [
        ("bus-1", True)
    ]


def test_select_single_delegates_with_multi_false(
    controller,
):
    manager = SelectionManager(controller)

    manager.select_single("bus-1")

    assert controller.select_calls == [
        ("bus-1", False)
    ]


def test_add_to_selection_delegates_with_multi_true(
    controller,
):
    manager = SelectionManager(controller)

    manager.add_to_selection("bus-1")

    assert controller.select_calls == [
        ("bus-1", True)
    ]


def test_select_rejects_none(
    manager,
):
    with pytest.raises(ValueError):
        manager.select(None)


@pytest.mark.parametrize(
    "value",
    [
        None,
        0,
        1,
        "",
        "true",
        [],
        {},
    ],
)
def test_select_rejects_non_bool_multi(
    manager,
    value,
):
    with pytest.raises(TypeError):
        manager.select(
            "bus-1",
            multi=value,
        )


def test_select_does_not_modify_selection_directly(
    controller,
):
    controller.selected_ids = ["existing"]

    manager = SelectionManager(controller)

    manager.select(
        "new",
        multi=True,
    )

    # Selection changes only because FakeController.select()
    # changed it.
    assert controller.select_calls == [
        ("new", True)
    ]


# ============================================================
# CLEAR
# ============================================================


def test_clear_delegates_to_controller(
    controller,
):
    controller.selected_ids = [
        "bus-1",
        "line-1",
    ]

    manager = SelectionManager(controller)

    manager.clear()

    assert controller.clear_selection_calls == 1
    assert controller.selected_ids == []


def test_clear_requires_controller_clear_selection():
    controller = FakeControllerWithoutClear()

    manager = SelectionManager(controller)

    with pytest.raises(TypeError):
        manager.clear()


# ============================================================
# GRAPHICS SYNCHRONIZATION
# ============================================================


def test_sync_graphics_without_scene_is_noop(
    controller,
):
    manager = SelectionManager(controller)

    manager.sync_graphics()

    assert manager.scene is None


def test_sync_graphics_uses_attached_scene(
    controller,
):
    first = FakeItem("bus-1")
    second = FakeItem("line-1")

    controller.selected_ids = ["bus-1"]

    scene = FakeScene([
        first,
        second,
    ])

    manager = SelectionManager(
        controller,
        scene,
    )

    manager.sync_graphics()

    assert first.selected is True
    assert second.selected is False


def test_sync_graphics_reads_controller_as_authority(
    controller,
):
    item = FakeItem(
        "bus-1",
        selected=False,
    )

    controller.selected_ids = ["bus-1"]

    scene = FakeScene([item])

    manager = SelectionManager(
        controller,
        scene,
    )

    manager.sync_graphics()

    assert item.selected is True

    controller.selected_ids.clear()

    manager.sync_graphics()

    assert item.selected is False


def test_sync_graphics_deselects_items_not_in_controller(
    controller,
):
    first = FakeItem(
        "bus-1",
        selected=True,
    )

    second = FakeItem(
        "line-1",
        selected=True,
    )

    controller.selected_ids = ["bus-1"]

    scene = FakeScene([
        first,
        second,
    ])

    manager = SelectionManager(
        controller,
        scene,
    )

    manager.sync_graphics()

    assert first.selected is True
    assert second.selected is False


def test_sync_graphics_deselects_items_without_object_id(
    controller,
):
    item = FakeItem(
        object_id=None,
        selected=True,
    )

    controller.selected_ids = ["bus-1"]

    scene = FakeScene([item])

    manager = SelectionManager(
        controller,
        scene,
    )

    manager.sync_graphics()

    assert item.selected is False


def test_sync_graphics_ignores_items_without_set_selected(
    controller,
):
    class NonSelectableItem:
        object_id = "bus-1"

    controller.selected_ids = ["bus-1"]

    scene = FakeScene([
        NonSelectableItem()
    ])

    manager = SelectionManager(
        controller,
        scene,
    )

    manager.sync_graphics()


def test_sync_graphics_accepts_explicit_scene(
    controller,
):
    attached_item = FakeItem("attached")
    explicit_item = FakeItem("explicit")

    controller.selected_ids = ["explicit"]

    attached_scene = FakeScene([
        attached_item
    ])

    explicit_scene = FakeScene([
        explicit_item
    ])

    manager = SelectionManager(
        controller,
        attached_scene,
    )

    manager.sync_graphics(
        scene=explicit_scene
    )

    assert attached_item.selected is False
    assert explicit_item.selected is True


def test_sync_graphics_requires_items_method(
    controller,
):
    manager = SelectionManager(
        controller,
        BrokenScene(),
    )

    with pytest.raises(TypeError):
        manager.sync_graphics()


def test_reconcile_delegates_to_sync_graphics(
    controller,
):
    item = FakeItem("bus-1")

    controller.selected_ids = ["bus-1"]

    scene = FakeScene([item])

    manager = SelectionManager(
        controller,
        scene,
    )

    manager.reconcile()

    assert item.selected is True


# ============================================================
# ITEM LOOKUP
# ============================================================


def test_get_item_for_id_without_scene_returns_none(
    manager,
):
    assert manager.get_item_for_id("bus-1") is None


def test_get_item_for_id_none_returns_none(
    manager,
):
    assert manager.get_item_for_id(None) is None


def test_get_item_for_id_returns_matching_item(
    controller,
):
    first = FakeItem("bus-1")
    second = FakeItem("line-1")

    scene = FakeScene([
        first,
        second,
    ])

    manager = SelectionManager(
        controller,
        scene,
    )

    assert manager.get_item_for_id("line-1") is second


def test_get_item_for_id_returns_none_when_missing(
    controller,
):
    scene = FakeScene([
        FakeItem("bus-1")
    ])

    manager = SelectionManager(
        controller,
        scene,
    )

    assert manager.get_item_for_id("missing") is None


def test_get_item_for_id_requires_items_method(
    controller,
):
    manager = SelectionManager(
        controller,
        BrokenScene(),
    )

    with pytest.raises(TypeError):
        manager.get_item_for_id("bus-1")


def test_get_item_for_id_uses_explicit_scene(
    controller,
):
    attached_item = FakeItem("attached")
    explicit_item = FakeItem("explicit")

    manager = SelectionManager(
        controller,
        FakeScene([attached_item]),
    )

    result = manager.get_item_for_id(
        "explicit",
        scene=FakeScene([explicit_item]),
    )

    assert result is explicit_item


# ============================================================
# MULTIPLE ITEM LOOKUP
# ============================================================


def test_get_items_for_ids_none_is_rejected(
    manager,
):
    with pytest.raises(ValueError):
        manager.get_items_for_ids(None)


def test_get_items_for_ids_without_scene_returns_empty(
    manager,
):
    assert manager.get_items_for_ids(
        ["bus-1"]
    ) == ()


def test_get_items_for_ids_empty_input_returns_empty(
    controller,
):
    scene = FakeScene([
        FakeItem("bus-1")
    ])

    manager = SelectionManager(
        controller,
        scene,
    )

    assert manager.get_items_for_ids([]) == ()


def test_get_items_for_ids_returns_matching_items(
    controller,
):
    first = FakeItem("bus-1")
    second = FakeItem("line-1")
    third = FakeItem("transformer-1")

    scene = FakeScene([
        first,
        second,
        third,
    ])

    manager = SelectionManager(
        controller,
        scene,
    )

    result = manager.get_items_for_ids(
        ["transformer-1", "bus-1"]
    )

    assert result == (
        first,
        third,
    )


def test_get_items_for_ids_preserves_scene_order(
    controller,
):
    first = FakeItem("bus-1")
    second = FakeItem("line-1")
    third = FakeItem("bus-2")

    scene = FakeScene([
        first,
        second,
        third,
    ])

    manager = SelectionManager(
        controller,
        scene,
    )

    result = manager.get_items_for_ids(
        ["bus-2", "bus-1"]
    )

    assert result == (
        first,
        third,
    )


def test_get_items_for_ids_requires_items_method(
    controller,
):
    manager = SelectionManager(
        controller,
        BrokenScene(),
    )

    with pytest.raises(TypeError):
        manager.get_items_for_ids(
            ["bus-1"]
        )


# ============================================================
# SELECTED GRAPHICS ITEMS
# ============================================================


def test_get_selected_items_uses_controller_selection(
    controller,
):
    bus = FakeItem("bus-1")
    line = FakeItem("line-1")

    controller.selected_ids = ["line-1"]

    scene = FakeScene([
        bus,
        line,
    ])

    manager = SelectionManager(
        controller,
        scene,
    )

    assert manager.get_selected_items() == (
        line,
    )


def test_get_selected_items_without_scene_returns_empty(
    controller,
):
    controller.selected_ids = ["bus-1"]

    manager = SelectionManager(controller)

    assert manager.get_selected_items() == ()


def test_get_selected_items_does_not_use_graphics_selection_as_authority(
    controller,
):
    selected_graphically = FakeItem(
        "bus-1",
        selected=True,
    )

    controller.selected_ids = []

    scene = FakeScene([
        selected_graphically
    ])

    manager = SelectionManager(
        controller,
        scene,
    )

    assert manager.get_selected_items() == ()


# ============================================================
# SCENE MANAGEMENT
# ============================================================


def test_set_scene_attaches_scene(
    manager,
):
    scene = FakeScene()

    manager.set_scene(scene)

    assert manager.scene is scene


def test_set_scene_can_clear_scene(
    manager,
):
    scene = FakeScene()

    manager.set_scene(scene)
    manager.set_scene(None)

    assert manager.scene is None


def test_get_scene_returns_attached_scene(
    controller,
):
    scene = FakeScene()

    manager = SelectionManager(
        controller,
        scene,
    )

    assert manager.get_scene() is scene


# ============================================================
# GRAPHICS RESET
# ============================================================


def test_reset_graphics_without_scene_is_noop(
    controller,
):
    controller.selected_ids = ["bus-1"]

    manager = SelectionManager(controller)

    manager.reset_graphics()

    assert controller.selected_ids == [
        "bus-1"
    ]


def test_reset_graphics_clears_graphics_only(
    controller,
):
    item = FakeItem(
        "bus-1",
        selected=True,
    )

    controller.selected_ids = ["bus-1"]

    scene = FakeScene([item])

    manager = SelectionManager(
        controller,
        scene,
    )

    manager.reset_graphics()

    assert item.selected is False
    assert controller.selected_ids == [
        "bus-1"
    ]


def test_reset_graphics_resets_all_selectable_items(
    controller,
):
    first = FakeItem(
        "bus-1",
        selected=True,
    )

    second = FakeItem(
        "line-1",
        selected=True,
    )

    scene = FakeScene([
        first,
        second,
    ])

    manager = SelectionManager(
        controller,
        scene,
    )

    manager.reset_graphics()

    assert first.selected is False
    assert second.selected is False


def test_reset_graphics_ignores_items_without_set_selected(
    controller,
):
    class NonSelectableItem:
        object_id = "bus-1"

    scene = FakeScene([
        NonSelectableItem()
    ])

    manager = SelectionManager(
        controller,
        scene,
    )

    manager.reset_graphics()


def test_reset_graphics_accepts_explicit_scene(
    controller,
):
    attached = FakeItem(
        "attached",
        selected=True,
    )

    explicit = FakeItem(
        "explicit",
        selected=True,
    )

    manager = SelectionManager(
        controller,
        FakeScene([attached]),
    )

    manager.reset_graphics(
        scene=FakeScene([explicit])
    )

    assert attached.selected is True
    assert explicit.selected is False


def test_reset_graphics_requires_items_method(
    controller,
):
    manager = SelectionManager(
        controller,
        BrokenScene(),
    )

    with pytest.raises(TypeError):
        manager.reset_graphics()


# ============================================================
# DIAGNOSTICS
# ============================================================


def test_get_state_initial(controller):
    manager = SelectionManager(controller)

    assert manager.get_state() == {
        "selected_count": 0,
        "selected_ids": (),
        "has_selection": False,
        "has_scene": False,
    }


def test_get_state_tracks_selection(
    controller,
):
    controller.selected_ids = [
        "bus-1",
        "line-1",
    ]

    manager = SelectionManager(controller)

    assert manager.get_state() == {
        "selected_count": 2,
        "selected_ids": (
            "bus-1",
            "line-1",
        ),
        "has_selection": True,
        "has_scene": False,
    }


def test_get_state_tracks_scene(
    controller,
):
    manager = SelectionManager(
        controller,
        FakeScene(),
    )

    state = manager.get_state()

    assert state["has_scene"] is True


def test_get_state_returns_selection_snapshot(
    controller,
):
    controller.selected_ids = ["bus-1"]

    manager = SelectionManager(controller)

    state = manager.get_state()

    controller.selected_ids.append("line-1")

    assert state["selected_ids"] == (
        "bus-1",
    )
    assert state["selected_count"] == 1


# ============================================================
# REPRESENTATION
# ============================================================


def test_repr_initial(manager):
    result = repr(manager)

    assert "SelectionManager" in result
    assert "selected=0" in result
    assert "scene=False" in result


def test_repr_contains_selection_count(
    controller,
):
    controller.selected_ids = [
        "bus-1",
        "line-1",
    ]

    manager = SelectionManager(controller)

    result = repr(manager)

    assert "selected=2" in result


def test_repr_contains_scene_state(
    controller,
):
    manager = SelectionManager(
        controller,
        FakeScene(),
    )

    result = repr(manager)

    assert "scene=True" in result


# ============================================================
# ARCHITECTURAL BOUNDARIES
# ============================================================


def test_selection_manager_does_not_own_selection_collection(
    controller,
):
    manager = SelectionManager(controller)

    assert not hasattr(
        manager,
        "_selected_ids",
    )


def test_selection_manager_reads_controller_dynamically(
    controller,
):
    manager = SelectionManager(controller)

    controller.selected_ids = ["first"]

    assert manager.selected_ids == ("first",)

    controller.selected_ids = ["second"]

    assert manager.selected_ids == ("second",)


def test_selection_manager_never_reads_scene_selection(
    controller,
):
    class SceneWithSelectedItems(FakeScene):
        def selectedItems(self):
            raise AssertionError(
                "Scene selection must never be authoritative."
            )

    controller.selected_ids = ["bus-1"]

    item = FakeItem(
        "bus-1",
        selected=False,
    )

    manager = SelectionManager(
        controller,
        SceneWithSelectedItems([item]),
    )

    manager.sync_graphics()

    assert item.selected is True


def test_selection_manager_does_not_modify_controller_during_sync(
    controller,
):
    controller.selected_ids = ["bus-1"]

    scene = FakeScene([
        FakeItem("bus-1")
    ])

    manager = SelectionManager(
        controller,
        scene,
    )

    manager.sync_graphics()

    assert controller.selected_ids == [
        "bus-1"
    ]


def test_selection_manager_does_not_modify_controller_during_reset(
    controller,
):
    controller.selected_ids = ["bus-1"]

    scene = FakeScene([
        FakeItem(
            "bus-1",
            selected=True,
        )
    ])

    manager = SelectionManager(
        controller,
        scene,
    )

    manager.reset_graphics()

    assert controller.selected_ids == [
        "bus-1"
    ]


# ============================================================
# OPTIONAL LIFECYCLE-STYLE BEHAVIOR
# ============================================================


def test_controller_remains_authoritative_after_select(
    controller,
):
    manager = SelectionManager(controller)

    manager.select_single("bus-1")

    assert manager.selected_ids == (
        "bus-1",
    )
    assert controller.selected_ids == [
        "bus-1"
    ]


def test_additive_selection_remains_controller_defined(
    controller,
):
    manager = SelectionManager(controller)

    manager.select_single("bus-1")
    manager.add_to_selection("line-1")

    assert manager.selected_ids == (
        "bus-1",
        "line-1",
    )


def test_clear_remains_controller_defined(
    controller,
):
    manager = SelectionManager(controller)

    manager.select_single("bus-1")
    manager.clear()

    assert manager.has_selection() is False
    assert controller.selected_ids == []


# ============================================================
# PUBLIC API
# ============================================================


def test_public_api_exports_selection_manager():
    import ui.core.selection_manager as module

    assert module.__all__ == [
        "SelectionManager"
    ]
