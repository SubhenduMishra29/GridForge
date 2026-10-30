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
    ) -> None:
        breaker_id = str(breaker_id)
        self.breaker_states[breaker_id] = bool(closed)
        for equipment_id in affected_equipment_ids:
            self.equipment_states[str(equipment_id)] = bool(closed)
        self._advance_revision()

    def apply_breaker_failure_backup(
        self,
        failed_breaker_id: str,
        backup_breaker_ids: Iterable[str],
    ) -> tuple[str, ...]:
        """Open explicitly mapped backup breakers in this study's detached state.

        The timer event is only a backup-clearing request: the primary breaker
        must still be closed when the timer expires. All target identifiers are
        validated before any state is changed, so an invalid mapping cannot
        leave a partially cleared backup set. This method never mutates the
        authoritative project Network or dispatches Application commands.
        """
        primary_id = str(failed_breaker_id).strip()
        if not primary_id:
            raise ValueError("failed_breaker_id must be a non-empty string.")
        targets = tuple(str(item).strip() for item in backup_breaker_ids)
        if not targets:
            raise ValueError("At least one explicit backup breaker is required.")
        if any(not item for item in targets):
            raise ValueError("Backup breaker identifiers must be non-empty strings.")
        if len(set(targets)) != len(targets):
            raise ValueError("Backup breaker identifiers must be unique.")
        if primary_id in targets:
            raise ValueError("The failed primary breaker cannot be its own backup target.")

        missing = tuple(
            item for item in (primary_id, *targets)
            if item not in self.breaker_states
        )
        if missing:
            raise KeyError(
                "Breaker-failure mapping references breakers absent from the "
                f"transient snapshot: {', '.join(missing)}"
            )

        # A primary breaker that opened before timer expiry has cleared the
        # fault path; the backup operation is therefore cancelled as a no-op.
        if not self.breaker_states[primary_id]:
            return ()

        changed = tuple(item for item in targets if self.breaker_states[item])
        if not changed:
            return ()

        for breaker_id in changed:
            self.breaker_states[breaker_id] = False
        self._advance_revision()
        return changed

    def set_equipment(self, equipment_id: str, conducting: bool) -> None:
        self.equipment_states[str(equipment_id)] = bool(conducting)
        self._advance_revision()

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
            active_fault=self.active_fault,
            topology_revision=self.topology_revision,
        )

    def _advance_revision(self) -> None:
        self.topology_revision = (self.topology_revision or 0) + 1


__all__ = ["TransientEventState"]
