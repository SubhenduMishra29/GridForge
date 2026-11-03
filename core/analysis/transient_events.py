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
    affected = tuple(str(item) for item in affected_equipment_ids)
    return manager.add(
        time,
        lambda: state.set_breaker(breaker_id, False, affected),
        event_id=event_id,
        event_type="breaker_open",
        priority=priority,
        metadata={
            "breaker_id": str(breaker_id),
            "affected_equipment_ids": affected,
            "machine_ids": state.machines_for_switch(breaker_id),
            "machine_connection_paths": {
                machine_id: state.snapshot.machine_connection_paths[machine_id]
                for machine_id in state.machines_for_switch(breaker_id)
            },
        },
        revision_reader=lambda: state.topology_revision,
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
    affected = tuple(str(item) for item in affected_equipment_ids)
    return manager.add(
        time,
        lambda: state.set_breaker(breaker_id, True, affected),
        event_id=event_id,
        event_type="breaker_close",
        priority=priority,
        metadata={
            "breaker_id": str(breaker_id),
            "affected_equipment_ids": affected,
            "machine_ids": state.machines_for_switch(breaker_id),
            "machine_connection_paths": {
                machine_id: state.snapshot.machine_connection_paths[machine_id]
                for machine_id in state.machines_for_switch(breaker_id)
            },
        },
        revision_reader=lambda: state.topology_revision,
    )


def schedule_equipment_state(manager: EventManager, state: TransientEventState, time: float, equipment_id: str, conducting: bool, *, event_id: str, priority: int = 0) -> SimulationEvent:
    key = str(equipment_id)
    machine_ids = state.machines_for_switch(key)
    return manager.add(
        time,
        lambda: state.set_equipment(key, conducting),
        event_id=event_id,
        event_type="equipment_state",
        priority=priority,
        metadata={
            "equipment_id": key,
            "conducting": bool(conducting),
            "machine_ids": machine_ids,
            "machine_connection_paths": {
                machine_id: state.snapshot.machine_connection_paths[machine_id]
                for machine_id in machine_ids
            },
        },
        revision_reader=lambda: state.topology_revision,
    )


def schedule_fault_apply(manager: EventManager, state: TransientEventState, time: float, fault: Any, *, event_id: str, priority: int = 0) -> SimulationEvent:
    return manager.add(
        time,
        lambda: state.apply_fault(fault),
        event_id=event_id,
        event_type="fault_apply",
        priority=priority,
        metadata={
            "fault_id": str(getattr(fault, "fault_id", "")) or None,
            "fault_bus_id": str(getattr(fault, "bus_id", "")) or None,
            "fault_type": type(fault).__name__,
        },
        revision_reader=lambda: state.topology_revision,
    )


def schedule_fault_clear(manager: EventManager, state: TransientEventState, time: float, *, event_id: str, priority: int = 0) -> SimulationEvent:
    return manager.add(
        time,
        state.clear_fault,
        event_id=event_id,
        event_type="fault_clear",
        priority=priority,
        revision_reader=lambda: state.topology_revision,
    )


__all__ = [
    "schedule_breaker_open",
    "schedule_breaker_close",
    "schedule_equipment_state",
    "schedule_fault_apply",
    "schedule_fault_clear",
]
