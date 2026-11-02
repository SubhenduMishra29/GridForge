"""Detached transient-study event scheduling helpers."""

from __future__ import annotations

from typing import Any, Iterable

from core.solver.dynamics.events import EventManager, SimulationEvent

from .transient_event_state import TransientEventState


def schedule_breaker_open(
    manager: EventManager,
    state: TransientEventState,
    time: float,
    breaker_id: str,
    *,
    affected_equipment_ids: Iterable[str] = (),
    event_id: str,
    priority: int = 0,
) -> SimulationEvent:
    return manager.add(
        time,
        lambda: state.set_breaker(breaker_id, False, affected_equipment_ids),
        event_id=event_id,
        event_type="breaker_open",
        priority=priority,
        metadata={"breaker_id": str(breaker_id)},
    )


def schedule_breaker_close(
    manager: EventManager,
    state: TransientEventState,
    time: float,
    breaker_id: str,
    *,
    affected_equipment_ids: Iterable[str] = (),
    event_id: str,
    priority: int = 0,
) -> SimulationEvent:
    return manager.add(
        time,
        lambda: state.set_breaker(breaker_id, True, affected_equipment_ids),
        event_id=event_id,
        event_type="breaker_close",
        priority=priority,
        metadata={"breaker_id": str(breaker_id)},
    )


def schedule_equipment_state(manager: EventManager, state: TransientEventState, time: float, equipment_id: str, conducting: bool, *, event_id: str, priority: int = 0) -> SimulationEvent:
    return manager.add(time, lambda: state.set_equipment(equipment_id, conducting), event_id=event_id, event_type="equipment_state", priority=priority, metadata={"equipment_id": str(equipment_id), "conducting": bool(conducting)})


def schedule_fault_apply(manager: EventManager, state: TransientEventState, time: float, fault: Any, *, event_id: str, priority: int = 0) -> SimulationEvent:
    return manager.add(time, lambda: state.apply_fault(fault), event_id=event_id, event_type="fault_apply", priority=priority)


def schedule_fault_clear(manager: EventManager, state: TransientEventState, time: float, *, event_id: str, priority: int = 0) -> SimulationEvent:
    return manager.add(time, state.clear_fault, event_id=event_id, event_type="fault_clear", priority=priority)


__all__ = [
    "schedule_breaker_open",
    "schedule_breaker_close",
    "schedule_equipment_state",
    "schedule_fault_apply",
    "schedule_fault_clear",
]
