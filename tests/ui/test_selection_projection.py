from __future__ import annotations

from types import SimpleNamespace

from ui.canvas.mouse_event_adapter import MouseEventAdapter
from ui.core.qt import QPointF
from ui.core.selection_manager import SelectionManager
from ui.projection.selection_projection_coordinator import SelectionProjectionCoordinator
from core.application.events import ElementUpdated
from core.application.read_models import ElementReadModel, NetworkReadModel


class _FakeMouseEvent:
    def __init__(self, position: QPointF, *, button=1, buttons=1, modifiers=0):
        self._position = position
        self._button = button
        self._buttons = buttons
        self._modifiers = modifiers

    def position(self):
        return self._position

    def button(self):
        return self._button

    def buttons(self):
        return self._buttons

    def modifiers(self):
        return self._modifiers


class _FakeView:
    def mapToScene(self, position):
        return QPointF(position.x() + 10, position.y() + 20)


class _FakeItem:
    def __init__(self, object_id=None, parent=None, selectable=True):
        self.object_id = object_id
        self._parent = parent
        self._selectable = selectable

    def parentItem(self):
        return self._parent

    def isVisible(self):
        return True

    def isEnabled(self):
        return True

    def flags(self):
        return self._selectable


class _FakeScene:
    def __init__(self, items):
        self._items = items

    def items(self, _position):
        return tuple(self._items)


class _FakeSignal:
    def __init__(self):
        self.handlers = []

    def connect(self, handler):
        self.handlers.append(handler)

    def disconnect(self, handler):
        self.handlers.remove(handler)

    def emit(self, value):
        for handler in tuple(self.handlers):
            handler(value)


class _FakeBus:
    def __init__(self):
        self.subscriptions = []

    def subscribe(self, event_type, handler):
        self.subscriptions.append((event_type, handler))

    def unsubscribe(self, event_type, handler):
        self.subscriptions.remove((event_type, handler))


class _FakePanel:
    def __init__(self):
        self.target = None

    def set_target(self, target):
        self.target = target

    def clear_target(self):
        self.target = None


def _element(object_id="bus-1"):
    return ElementReadModel(
        object_id=object_id,
        element_type="BUS",
        labels={"name": "Bus 1"},
        connectivity_refs=(),
        attributes={"nominal_voltage_kv": 11.0, "in_service": True},
    )


def test_mouse_adapter_maps_scene_and_resolves_decorative_child():
    selectable = _FakeItem("bus-1", selectable=True)
    decorative = _FakeItem(parent=selectable, selectable=False)
    scene = _FakeScene([decorative])
    adapter = MouseEventAdapter(view=_FakeView(), scene=scene)

    event = adapter.adapt(_FakeMouseEvent(QPointF(2, 3), button=1, buttons=1, modifiers=7))

    assert event.position == QPointF(12, 23)
    assert event.scene_position == QPointF(12, 23)
    assert event.object_id == "bus-1"
    assert event.button == 1
    assert event.buttons == 1
    assert event.modifiers == 7


def test_mouse_adapter_preserves_empty_canvas_as_none():
    adapter = MouseEventAdapter(view=_FakeView(), scene=_FakeScene([]))
    event = adapter.adapt(_FakeMouseEvent(QPointF(2, 3)))
    assert event.object_id is None


def test_selection_manager_emits_changed_and_cleared():
    manager = SelectionManager()
    changed = []
    cleared = []
    manager.selection_changed.connect(changed.append)
    manager.selection_cleared.connect(lambda: cleared.append(True))

    manager.select_single("bus-1")
    manager.add_to_selection("bus-2")
    manager.clear()

    assert changed == [("bus-1",), ("bus-1", "bus-2"), ()]
    assert cleared == [True]


def test_selection_projection_reads_through_application():
    manager = SelectionManager()
    bus = _element()
    network = NetworkReadModel(elements=(bus,))
    bus_service = _FakeBus()
    app = SimpleNamespace(
        event_bus=bus_service,
        read_network=lambda: network,
        read_element=lambda element_type, object_id: bus if (element_type, object_id) == ("BUS", "bus-1") else None,
    )
    panel = _FakePanel()
    coordinator = SelectionProjectionCoordinator(
        selection_manager=manager,
        application=app,
        properties_panel=panel,
    )

    manager.select_single("bus-1")

    assert panel.target is not None
    assert panel.target.object_id == "bus-1"
    assert panel.target.display_type == "BUS"

    for event_type, handler in bus_service.subscriptions:
        if event_type is ElementUpdated:
            handler(ElementUpdated(element_id="bus-1", element_type="BUS"))
            break
    assert panel.target.object_id == "bus-1"

    coordinator.dispose()
