"""Detached transient-study event state and mutation boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from core.analysis.transient_network import DetachedTransientNetworkState


@dataclass
class TransientEventState:
    """Mutable state owned exclusively by one transient study execution."""

    snapshot: DetachedTransientNetworkState
    breaker_states: dict[str, bool]
    equipment_states: dict[str, bool]
    active_fault: object | None = None
    topology_revision: int | None = None

    @classmethod
    def from_snapshot(cls, snapshot: DetachedTransientNetworkState) -> "TransientEventState":
        return cls(snapshot, dict(snapshot.breaker_states), dict(snapshot.equipment_states), snapshot.active_fault, snapshot.topology_revision)

    def set_breaker(
        self,
        breaker_id: str,
        closed: bool,
        affected_equipment_ids: Iterable[str] = (),
    ) -> dict[str, object]:
        breaker_id = str(breaker_id)
        previous_state = self.breaker_states.get(breaker_id)
        previous_machine_states = {
            machine_id: self.is_machine_connected(machine_id)
            for machine_id, path in self.snapshot.machine_connection_paths.items()
            if breaker_id in path
        }
        self.breaker_states[breaker_id] = bool(closed)
        for equipment_id in affected_equipment_ids:
            self.equipment_states[str(equipment_id)] = bool(closed)
        self._advance_revision()
        return self._switch_transition_record(
            switch_id=breaker_id,
            previous_state=previous_state,
            new_state=bool(closed),
            previous_machine_states=previous_machine_states,
        )

    def set_equipment(self, equipment_id: str, conducting: bool) -> dict[str, object]:
        key = str(equipment_id)
        previous_state = self.breaker_states.get(key, self.equipment_states.get(key))
        previous_machine_states = {
            machine_id: self.is_machine_connected(machine_id)
            for machine_id, path in self.snapshot.machine_connection_paths.items()
            if key in path
        }
        self.equipment_states[key] = bool(conducting)
        if key in self.breaker_states:
            self.breaker_states[key] = bool(conducting)
        self._advance_revision()
        return self._switch_transition_record(
            switch_id=key,
            previous_state=previous_state,
            new_state=bool(conducting),
            previous_machine_states=previous_machine_states,
        )

    def is_machine_connected(self, machine_id: str) -> bool:
        key = str(machine_id)
        try:
            path = self.snapshot.machine_connection_paths[key]
        except KeyError as exc:
            raise ValueError(f"Dynamic machine '{key}' has no validated detached connection path.") from exc
        return all(self.breaker_states.get(switch_id, False) for switch_id in path)

    def machines_for_switch(self, switch_id: str) -> tuple[str, ...]:
        key = str(switch_id)
        return tuple(
            machine_id
            for machine_id, path in self.snapshot.machine_connection_paths.items()
            if key in path
        )

    def _switch_transition_record(
        self,
        *,
        switch_id: str,
        previous_state: bool | None,
        new_state: bool,
        previous_machine_states: dict[str, bool],
    ) -> dict[str, object]:
        machine_transitions = {
            machine_id: {
                "switching_path": self.snapshot.machine_connection_paths[machine_id],
                "connected_before": previous_state_for_machine,
                "connected_after": self.is_machine_connected(machine_id),
            }
            for machine_id, previous_state_for_machine in previous_machine_states.items()
        }
        return {
            "switch_id": switch_id,
            "previous_switch_state": previous_state,
            "new_switch_state": new_state,
            "machine_transitions": machine_transitions,
            "network_revision": self.topology_revision,
        }

    def apply_fault(self, fault: object) -> None:
        if self.active_fault is not None:
            raise ValueError("A transient fault is already active.")
        self.active_fault = fault
        self._advance_revision()

    def clear_fault(self) -> None:
        if self.active_fault is None:
            raise ValueError("Cannot clear a transient fault when no fault is active.")
        self.active_fault = None
        self._advance_revision()

    def is_conducting(self, equipment_id: str, default: bool = True) -> bool:
        return self.equipment_states.get(str(equipment_id), default)

    def detached_view(self) -> DetachedTransientNetworkState:
        return DetachedTransientNetworkState(
            bus_ids=self.snapshot.bus_ids,
            branches=self.snapshot.branches,
            transformers=self.snapshot.transformers,
            shunts=self.snapshot.shunts,
            breaker_states=dict(self.breaker_states),
            equipment_states=dict(self.equipment_states),
            machine_connection_paths=self.snapshot.machine_connection_paths,
            machine_rotor_policies=self.snapshot.machine_rotor_policies,
            active_fault=self.active_fault,
            topology_revision=self.topology_revision,
        )

    def _advance_revision(self) -> None:
        self.topology_revision = (self.topology_revision or 0) + 1


__all__ = ["TransientEventState"]
