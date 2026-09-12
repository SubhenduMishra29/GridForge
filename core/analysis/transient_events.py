"""Event scheduling helpers for detached transient studies."""

from __future__ import annotations

from typing import Iterable

from core.solver.dynamics.events import EventManager, SimulationEvent

from .transient_event_state import TransientEventState
from .transient_fault import TransientFault


def schedule_breaker_open(
    manager: EventManager,
    state: TransientEventState,
    time: float,
    breaker_id: str,
    event_id: str,
    affected_equipment_ids: Iterable[str] = (),
) -> SimulationEvent:
    affected = tuple(str(item) for item in affected_equipment_ids)
    return manager.add(
        time,
        lambda: state.set_breaker(breaker_id, False, affected),
        event_id=event_id,
        event_type="breaker_open",
    )


def schedule_breaker_close(
    manager: EventManager,
    state: TransientEventState,
    time: float,
    breaker_id: str,
    event_id: str,
    affected_equipment_ids: Iterable[str] = (),
) -> SimulationEvent:
    affected = tuple(str(item) for item in affected_equipment_ids)
    return manager.add(
        time,
        lambda: state.set_breaker(breaker_id, True, affected),
        event_id=event_id,
        event_type="breaker_close",
    )


def schedule_equipment_state(
    manager: EventManager,
    state: TransientEventState,
    time: float,
    equipment_id: str,
    conducting: bool,
    event_id: str,
) -> SimulationEvent:
    return manager.add(
        time,
        lambda: state.set_equipment(equipment_id, conducting),
        event_id=event_id,
        event_type="equipment_state",
    )


def schedule_fault_apply(
    manager: EventManager,
    state: TransientEventState,
    time: float,
    fault: TransientFault,
    event_id: str,
) -> SimulationEvent:
    return manager.add(
        time,
        lambda: state.apply_fault(fault),
        event_id=event_id,
        event_type="fault_apply",
    )


def schedule_fault_clear(
    manager: EventManager,
    state: TransientEventState,
    time: float,
    event_id: str,
) -> SimulationEvent:
    return manager.add(
        time,
        state.clear_fault,
        event_id=event_id,
        event_type="fault_clear",
    )


__all__ = [
    "schedule_breaker_open",
    "schedule_breaker_close",
    "schedule_equipment_state",
    "schedule_fault_apply",
    "schedule_fault_clear",
]
