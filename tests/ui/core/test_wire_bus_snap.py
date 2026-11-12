from __future__ import annotations

from ui.core.qt import QGraphicsScene, QPointF
from ui.core.snap_system import SnapIntent, SnapSystem, SnapType
from ui.items.bus_item import BusItem


def test_wire_snap_accepts_click_anywhere_along_bus_bar_and_returns_stable_slot():
    scene = QGraphicsScene()
    bus = BusItem("BUS-001")
    scene.addItem(bus)
    snap_system = SnapSystem(scene=scene, tolerance=10.0)
    snap_system.register_item(bus)

    result = snap_system.snap(
        QPointF(47.0, 3.0),
        allow_grid=False,
        allow_object=True,
        intent=SnapIntent.WIRE_START,
        tolerance=5.0,
    )

    assert result.snap_type is SnapType.OBJECT
    assert result.object_id == "BUS-001"
    assert result.bus_id == "BUS-001"
    assert result.attachment_id == "attachment-6"
    assert result.position == bus.attachment_position("attachment-6")
    assert result.distance == 3.0


def test_wire_snap_rejects_pointer_outside_bus_bar_hit_radius():
    scene = QGraphicsScene()
    bus = BusItem("BUS-001")
    scene.addItem(bus)
    snap_system = SnapSystem(scene=scene, tolerance=10.0)
    snap_system.register_item(bus)

    result = snap_system.snap(
        QPointF(0.0, 16.0),
        allow_grid=False,
        allow_object=True,
        intent=SnapIntent.WIRE_START,
        tolerance=5.0,
    )

    assert result.snap_type is SnapType.NONE


def test_wire_snap_uses_per_event_tolerance_without_mutating_default():
    scene = QGraphicsScene()
    bus = BusItem("BUS-001")
    scene.addItem(bus)
    snap_system = SnapSystem(scene=scene, tolerance=10.0)
    snap_system.register_item(bus)

    result = snap_system.snap(
        QPointF(0.0, 12.0),
        allow_grid=False,
        allow_object=True,
        intent=SnapIntent.WIRE_TARGET,
        tolerance=14.0,
    )

    assert result.snap_type is SnapType.OBJECT
    assert snap_system.tolerance == 10.0
