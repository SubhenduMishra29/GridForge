from __future__ import annotations

from dataclasses import dataclass

from ui.core.qt import QPointF
import ui.core.snap_system as snap_module
from ui.core.snap_system import SnapIntent, SnapSystem, SnapType


class _Scene:
    def items(self):
        return ()


@dataclass
class _CandidateItem:
    object_id: str
    _scene: object
    candidates: tuple[dict, ...]
    bounds: tuple[float, float, float, float]

    def scene(self):
        return self._scene

    def snap_points(self):
        return self.candidates

    def mapFromScene(self, point):
        return point

    def contains(self, point):
        left, top, right, bottom = self.bounds
        return left <= point.x() <= right and top <= point.y() <= bottom


class _BusCandidate(_CandidateItem):
    pass


class _EquipmentCandidate(_CandidateItem):
    pass


def _system(monkeypatch, item):
    monkeypatch.setattr(snap_module, "BusItem", _BusCandidate)
    monkeypatch.setattr(snap_module, "EquipmentItem", _EquipmentCandidate)
    system = SnapSystem(scene=item._scene, tolerance=10.0)
    system.register_item(item)
    return system


def test_wire_click_inside_bus_bar_resolves_nearest_declared_attachment(monkeypatch):
    scene = _Scene()
    bus = _BusCandidate(
        "BUS-001",
        scene,
        (
            {"position": QPointF(0, 0), "object_id": "BUS-001", "bus_id": "BUS-001", "attachment_id": "attachment-0"},
            {"position": QPointF(100, 0), "object_id": "BUS-001", "bus_id": "BUS-001", "attachment_id": "attachment-1"},
        ),
        (0, -5, 100, 5),
    )
    system = _system(monkeypatch, bus)

    result = system.snap(QPointF(78, 2), allow_grid=False, allow_object=True, intent=SnapIntent.WIRE_START)

    assert result.snap_type is SnapType.OBJECT
    assert result.object_id == "BUS-001"
    assert result.attachment_id == "attachment-1"
    assert result.position == QPointF(100, 0)


def test_wire_click_inside_equipment_body_resolves_nearest_declared_terminal(monkeypatch):
    scene = _Scene()
    equipment = _EquipmentCandidate(
        "CB-001",
        scene,
        (
            {"position": QPointF(0, 0), "object_id": "CB-001", "terminal_id": "CB-001:line", "terminal_name": "line"},
            {"position": QPointF(100, 0), "object_id": "CB-001", "terminal_id": "CB-001:load", "terminal_name": "load"},
        ),
        (0, -20, 100, 20),
    )
    system = _system(monkeypatch, equipment)

    result = system.snap(QPointF(91, 5), allow_grid=False, allow_object=True, intent=SnapIntent.WIRE_TARGET)

    assert result.snap_type is SnapType.OBJECT
    assert result.object_id == "CB-001"
    assert result.terminal_name == "load"
    assert result.position == QPointF(100, 0)


def test_wire_hit_fallback_does_not_accept_click_outside_symbol_shape(monkeypatch):
    scene = _Scene()
    equipment = _EquipmentCandidate(
        "CB-001",
        scene,
        ({"position": QPointF(0, 0), "object_id": "CB-001", "terminal_id": "CB-001:line", "terminal_name": "line"},),
        (-10, -10, 10, 10),
    )
    system = _system(monkeypatch, equipment)

    result = system.snap(QPointF(40, 40), allow_grid=False, allow_object=True, intent=SnapIntent.WIRE_TARGET)

    assert result.snap_type is SnapType.NONE


def test_non_wire_snap_keeps_endpoint_tolerance_contract(monkeypatch):
    scene = _Scene()
    equipment = _EquipmentCandidate(
        "CB-001",
        scene,
        ({"position": QPointF(0, 0), "object_id": "CB-001", "terminal_id": "CB-001:line", "terminal_name": "line"},),
        (-10, -10, 10, 10),
    )
    system = _system(monkeypatch, _EquipmentCandidate, equipment)

    result = system.snap(QPointF(8, 8), allow_grid=False, allow_object=True, intent=SnapIntent.PLACE)

    assert result.snap_type is SnapType.NONE


def test_clicked_device_shape_takes_precedence_over_nearby_bus_anchor(monkeypatch):
    scene = _Scene()
    bus = _BusCandidate(
        "BUS-001",
        scene,
        ({"position": QPointF(48, 0), "object_id": "BUS-001", "bus_id": "BUS-001", "attachment_id": "attachment-0"},),
        (0, -5, 40, 5),
    )
    equipment = _EquipmentCandidate(
        "CB-001",
        scene,
        ({"position": QPointF(100, 0), "object_id": "CB-001", "terminal_id": "CB-001:line", "terminal_name": "line"},),
        (50, -20, 110, 20),
    )
    monkeypatch.setattr(snap_module, "BusItem", _BusCandidate)
    monkeypatch.setattr(snap_module, "EquipmentItem", _EquipmentCandidate)
    system = SnapSystem(scene=scene, tolerance=10.0)
    system.register_item(bus)
    system.register_item(equipment)

    result = system.snap(QPointF(55, 2), allow_grid=False, allow_object=True, intent=SnapIntent.WIRE_TARGET)

    assert result.snap_type is SnapType.OBJECT
    assert result.object_id == "CB-001"
    assert result.terminal_name == "line"


def test_bus_attachment_midpoint_uses_stable_declared_order(monkeypatch):
    scene = _Scene()
    bus = _BusCandidate(
        "BUS-001",
        scene,
        (
            {"position": QPointF(0, 0), "object_id": "BUS-001", "bus_id": "BUS-001", "attachment_id": "attachment-0"},
            {"position": QPointF(100, 0), "object_id": "BUS-001", "bus_id": "BUS-001", "attachment_id": "attachment-1"},
        ),
        (0, -5, 100, 5),
    )
    system = _system(monkeypatch, bus)

    result = system.snap(QPointF(50, 0), allow_grid=False, allow_object=True, intent=SnapIntent.WIRE_START)

    assert result.snap_type is SnapType.OBJECT
    assert result.attachment_id == "attachment-0"
