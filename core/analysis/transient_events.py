"""Detached transient-study event scheduling helpers."""

from __future__ import annotations

import math
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


def schedule_breaker_failure_backup(
    manager: EventManager,
    state: TransientEventState,
    trip_time: float,
    failed_breaker_id: str,
    backup_breaker_ids: Iterable[str],
    *,
    delay: float,
    event_id: str,
    priority: int = 0,
) -> SimulationEvent:
    """Schedule explicit 50BF backup clearing in detached study state.

    trip_time is the time of the primary breaker trip request. At timer
    expiry, the event checks whether the primary breaker is still closed.
    If it is, every explicitly configured backup breaker is opened as one
    validated state update. If the primary breaker has opened, the event is
    a no-op.

    This is the solver-side timer/backup-event primitive, not a complete ANSI
    50BF relay model: current supervision, breaker auxiliary-contact
    acquisition, setting groups, zone engineering, and project configuration
    remain outside this function. Backup targets are never inferred from
    network adjacency. The callback only mutates the study-owned detached
    TransientEventState; it must not call CommandManager or mutate Core.
    """
    if not isinstance(manager, EventManager):
        raise TypeError("manager must be an EventManager.")
    if not isinstance(state, TransientEventState):
        raise TypeError("state must be a TransientEventState.")

    try:
        start = float(trip_time)
        timer = float(delay)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("trip_time and delay must be finite numeric values.") from exc
    if not math.isfinite(start) or start < 0.0:
        raise ValueError("trip_time must be finite and non-negative.")
    if not math.isfinite(timer) or timer <= 0.0:
        raise ValueError("delay must be finite and greater than zero.")
    expiry = start + timer
    if not math.isfinite(expiry):
        raise ValueError("breaker-failure timer expiry must be finite.")

    primary_id = str(failed_breaker_id).strip()
    if not primary_id:
        raise ValueError("failed_breaker_id must be a non-empty string.")
    targets = tuple(str(item).strip() for item in backup_breaker_ids)
    if not targets or any(not item for item in targets):
        raise ValueError("At least one non-empty backup breaker ID is required.")
    if len(set(targets)) != len(targets):
        raise ValueError("Backup breaker IDs must be unique.")
    if primary_id in targets:
        raise ValueError("The failed primary breaker cannot be its own backup target.")

    missing = tuple(
        item for item in (primary_id, *targets)
        if item not in state.breaker_states
    )
    if missing:
        raise KeyError(
            "Breaker-failure mapping references breakers absent from the "
            f"transient snapshot: {', '.join(missing)}"
        )

    return manager.add(
        expiry,
        lambda: state.apply_breaker_failure_backup(primary_id, targets),
        event_id=event_id,
        event_type="breaker_failure_backup_clear",
        description=f"ANSI 50BF backup clearing for {primary_id}",
        priority=priority,
        metadata={
            "failed_breaker_id": primary_id,
            "backup_breaker_ids": targets,
            "trip_time": start,
            "delay": timer,
            "timer_expiry": expiry,
        },
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
    "schedule_breaker_failure_backup",
    "schedule_equipment_state",
    "schedule_fault_apply",
    "schedule_fault_clear",
]
