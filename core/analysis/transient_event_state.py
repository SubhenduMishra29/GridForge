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
        pre_revision = self.topology_revision
        if closed and breaker_id in self.snapshot.switch_available_states and not self.snapshot.switch_available_states[breaker_id]:
            raise ValueError(
                f"Cannot close switching target '{breaker_id}': it is failed, out of service, "
                "or otherwise unavailable in the captured study snapshot."
            )
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
            pre_event_revision=pre_revision,
        )

    def set_equipment(self, equipment_id: str, conducting: bool) -> dict[str, object]:
        key = str(equipment_id)
        previous_state = self.breaker_states.get(key, self.equipment_states.get(key))
        pre_revision = self.topology_revision
        if conducting and key in self.snapshot.switch_available_states and not self.snapshot.switch_available_states[key]:
            raise ValueError(
                f"Cannot restore switching target '{key}': it is failed, out of service, "
                "or otherwise unavailable in the captured study snapshot."
            )
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
            pre_event_revision=pre_revision,
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
        pre_event_revision: int | None,
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
            "transition_type": "switch_close" if new_state else "switch_open",
            "switch_id": switch_id,
            "previous_switch_state": previous_state,
            "new_switch_state": new_state,
            "switch_available": self.snapshot.switch_available_states.get(switch_id),
            "machine_transitions": machine_transitions,
            "source_topology_revision": self.snapshot.topology_revision,
            "pre_event_revision": pre_event_revision,
            "post_event_revision": self.topology_revision,
            "detached_network_revision": self.topology_revision,
        }

    def apply_fault(self, fault: object) -> dict[str, object]:
        if self.active_fault is not None:
            raise ValueError("A transient fault is already active.")
        pre_revision = self.topology_revision
        self.active_fault = fault
        self._advance_revision()
        return {
            "transition_type": "fault_apply",
            "fault_id": str(getattr(fault, "fault_id", "")) or None,
            "fault_type": str(getattr(getattr(fault, "fault_type", None), "value", getattr(fault, "fault_type", type(fault).__name__))),
            "fault_bus_id": str(getattr(fault, "bus_id", "")) or None,
            "previous_fault_active": False,
            "new_fault_active": True,
            "source_topology_revision": self.snapshot.topology_revision,
            "pre_event_revision": pre_revision,
            "post_event_revision": self.topology_revision,
        }

    def clear_fault(self) -> dict[str, object]:
        if self.active_fault is None:
            raise ValueError("Cannot clear a transient fault when no fault is active.")
        previous_fault = self.active_fault
        pre_revision = self.topology_revision
        self.active_fault = None
        self._advance_revision()
        return {
            "transition_type": "fault_clear",
            "fault_id": str(getattr(previous_fault, "fault_id", "")) or None,
            "fault_type": str(getattr(getattr(previous_fault, "fault_type", None), "value", getattr(previous_fault, "fault_type", type(previous_fault).__name__))),
            "fault_bus_id": str(getattr(previous_fault, "bus_id", "")) or None,
            "previous_fault_active": True,
            "new_fault_active": False,
            "source_topology_revision": self.snapshot.topology_revision,
            "pre_event_revision": pre_revision,
            "post_event_revision": self.topology_revision,
        }

    def is_conducting(self, equipment_id: str, default: bool = True) -> bool:
        return self.equipment_states.get(str(equipment_id), default)

    def detached_view(self) -> DetachedTransientNetworkState:
        return DetachedTransientNetworkState(
            bus_ids=self.snapshot.bus_ids,
            branches=self.snapshot.branches,
            transformers=self.snapshot.transformers,
            shunts=self.snapshot.shunts,
            breaker_states=dict(self.breaker_states),
            switch_available_states=self.snapshot.switch_available_states,
            switch_connections=self.snapshot.switch_connections,
            equipment_states=dict(self.equipment_states),
            machine_connection_paths=self.snapshot.machine_connection_paths,
            machine_rotor_policies=self.snapshot.machine_rotor_policies,
            project_id=self.snapshot.project_id,
            activation_generation=self.snapshot.activation_generation,
            source_revision=self.snapshot.source_revision,
            active_fault=self.active_fault,
            topology_revision=self.topology_revision,
        )

    def _advance_revision(self) -> None:
        self.topology_revision = (self.topology_revision or 0) + 1


__all__ = ["TransientEventState"]
