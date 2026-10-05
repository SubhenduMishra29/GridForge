# ============================================================
# File: core/application/revision_service.py
# GridForge V2 — Project Revision / Dirty-State Service
# Author: Subhendu Mishra
# ============================================================

"""Authoritative Application-owned project revision tracking."""

from __future__ import annotations

from dataclasses import dataclass

from .command import Command
from .revision import ProjectRevision


@dataclass(frozen=True, slots=True)
class _RevisionTransition:
    before: ProjectRevision
    after: ProjectRevision


class RevisionService:
    """Own the authoritative in-memory revision state for the active project."""

    _MUTATING_COMMAND_PREFIXES = ("model.", "control.", "protection.", "application.", "connectivity.", "draft.", "network.")
    _TOPOLOGY_COMMANDS = frozenset({
        "model.connect_terminal", "model.disconnect_terminal", "model.reconnect_terminal",
        "connectivity.create_simple_wire", "connectivity.remove_simple_wire",
        "network.commit_draft", "model.create_bus", "model.delete_bus", "model.create_line", "model.delete_line",
        "model.create_transformer", "model.delete_transformer",
        "model.create_cable", "model.update_cable", "model.delete_cable",
        "model.create_switch", "model.update_switch", "model.delete_switch",
        "model.open_switch", "model.close_switch",
        "model.put_switch_in_service", "model.take_switch_out_of_service",
        "model.create_disconnector", "model.update_disconnector", "model.delete_disconnector",
        "model.open_disconnector", "model.close_disconnector",
        "model.put_disconnector_in_service", "model.take_disconnector_out_of_service",
        "model.create_fuse", "model.update_fuse", "model.delete_fuse",
        "model.blow_fuse", "model.reset_fuse",
        "model.put_fuse_in_service", "model.take_fuse_out_of_service",
        "model.create_breaker", "model.delete_breaker",
        "model.open_breaker", "model.close_breaker", "model.trip_breaker",
        "model.put_breaker_in_service", "model.take_breaker_out_of_service",
    })
    _TOPOLOGY_STATE_FIELDS = frozenset({"closed", "in_service", "tripped", "blown", "status", "endpoint", "endpoint_from", "endpoint_to", "endpoint_a", "endpoint_b"})
    _TOPOLOGY_UPDATE_COMMANDS = frozenset({
        "model.update_bus", "model.update_grid", "model.update_generator", "model.update_synchronous_machine", "model.update_load", "model.update_motor", "model.update_shunt", "model.update_capacitor", "model.update_reactor", "model.update_solar", "model.update_battery", "model.update_current_transformer", "model.update_capacitive_voltage_transformer", "model.update_pt", "model.update_relay", "model.update_line", "model.update_cable", "model.update_transformer", "model.update_breaker",
        "model.update_switch",
        "model.update_disconnector",
        "model.update_fuse",
    })

    def __init__(self) -> None:
        self._current = ProjectRevision()
        self._persisted_state = self._current
        self._undo: list[_RevisionTransition] = []
        self._redo: list[_RevisionTransition] = []
        self._persisted_generation = 0

    @property
    def revision(self) -> ProjectRevision:
        return self._current

    @property
    def is_dirty(self) -> bool:
        """Return whether model/topology/presentation state differs from persisted state.

        Validation is read-only and never changes revision counters. An
        unresolved SLD equipment reference is therefore a validation
        diagnostic, not a second dirty-state authority.
        """
        return self._current != self._persisted_state

    def snapshot_state(self) -> tuple[
        ProjectRevision,
        ProjectRevision,
        tuple[_RevisionTransition, ...],
        tuple[_RevisionTransition, ...],
        int,
    ]:
        """Capture all revision state needed by an activation rollback."""
        return (
            self._current,
            self._persisted_state,
            tuple(self._undo),
            tuple(self._redo),
            self._persisted_generation,
        )

    def restore_state(self, state: tuple[
        ProjectRevision,
        ProjectRevision,
        tuple[_RevisionTransition, ...],
        tuple[_RevisionTransition, ...],
        int,
    ]) -> None:
        """Restore a previously captured activation revision state."""
        if not isinstance(state, tuple) or len(state) != 5:
            raise TypeError("Invalid revision transaction state.")
        current, persisted, undo, redo, generation = state
        if not isinstance(current, ProjectRevision) or not isinstance(persisted, ProjectRevision):
            raise TypeError("Invalid revision snapshots.")
        if not isinstance(undo, tuple) or not all(isinstance(item, _RevisionTransition) for item in undo):
            raise TypeError("Invalid undo history snapshot.")
        if not isinstance(redo, tuple) or not all(isinstance(item, _RevisionTransition) for item in redo):
            raise TypeError("Invalid redo history snapshot.")
        if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
            raise ValueError("persisted generation must be a non-negative integer.")
        self._current = current
        self._persisted_state = persisted
        self._undo = list(undo)
        self._redo = list(redo)
        self._persisted_generation = generation

    def mark_persisted(self) -> ProjectRevision:
        """Mark the current project state as successfully persisted."""
        self._persisted_generation += 1
        self._current = ProjectRevision(
            model_revision=self._current.model_revision,
            topology_revision=self._current.topology_revision,
            presentation_revision=self._current.presentation_revision,
            persisted_revision=self._persisted_generation,
        )
        self._persisted_state = self._current
        return self._current

    @classmethod
    def is_topology_command(cls, command: Command) -> bool:
        """Return whether a command changes authoritative switching topology."""
        if not isinstance(command, Command):
            raise TypeError("command must be a Command")
        command_type = command.command_type
        if command_type in cls._TOPOLOGY_COMMANDS:
            return True
        # Single-terminal equipment changes topology only when the mutation
        # actually supplies/changes a physical Bus attachment. Merely adding
        # an isolated injection is a model mutation, not a topology mutation.
        if command_type.startswith("model.create_") and command_type not in cls._TOPOLOGY_COMMANDS:
            return any(command.payload.get(field) is not None for field in ("endpoint", "endpoint_from", "endpoint_to", "endpoint_a", "endpoint_b"))
        if command_type.startswith("model.delete_") and command_type not in cls._TOPOLOGY_COMMANDS:
            return False
        if command_type in cls._TOPOLOGY_UPDATE_COMMANDS:
            return any(command.payload.get(field) is not None for field in cls._TOPOLOGY_STATE_FIELDS)
        return False

    @classmethod
    def _next_for_command(cls, revision: ProjectRevision, command: Command, *, topology_revision: int | None = None) -> ProjectRevision:
        """Derive the next revision from the canonical Application mutation contract."""
        if not isinstance(revision, ProjectRevision):
            raise TypeError("revision must be a ProjectRevision")
        if not isinstance(command, Command):
            raise TypeError("command must be a Command")

        if not command.command_type.startswith(cls._MUTATING_COMMAND_PREFIXES):
            return revision

        model_revision = revision.model_revision + 1
        if cls.is_topology_command(command):
            if topology_revision is None:
                topology_revision = revision.topology_revision + 1
            if not isinstance(topology_revision, int) or isinstance(topology_revision, bool) or topology_revision < revision.topology_revision:
                raise ValueError("topology_revision must be a non-decreasing Core topology revision.")
        else:
            topology_revision = revision.topology_revision
        return ProjectRevision(
            model_revision=model_revision,
            topology_revision=topology_revision,
            presentation_revision=revision.presentation_revision,
            persisted_revision=revision.persisted_revision,
        )

    def _record_transition(self, after: ProjectRevision) -> ProjectRevision:
        if after == self._current:
            return self._current
        self._undo.append(_RevisionTransition(self._current, after))
        self._current = after
        self._redo.clear()
        return self._current

    def record_command_success(self, command: Command, *, topology_revision: int | None = None) -> ProjectRevision:
        """Record a successful mutation using the committed Core topology revision when supplied."""
        return self._record_transition(self._next_for_command(self._current, command, topology_revision=topology_revision))

    def record_presentation_change(self) -> ProjectRevision:
        """Record one successfully committed persistent SLD presentation command.

        SLD association validation does not advance this revision; only an
        Application command that actually mutates persistent presentation
        state does so.
        """
        next_revision = ProjectRevision(
            model_revision=self._current.model_revision,
            topology_revision=self._current.topology_revision,
            presentation_revision=self._current.presentation_revision + 1,
            persisted_revision=self._current.persisted_revision,
        )
        return self._record_transition(next_revision)

    def record_undo(self, *, topology_revision: int | None = None) -> ProjectRevision:
        """Restore model/presentation revision while adopting the actual Core topology revision."""
        if not self._undo:
            raise RuntimeError("No revision transition is available to undo.")
        transition = self._undo.pop()
        if transition.after != self._current:
            raise RuntimeError("Revision undo state is inconsistent with current revision.")
        before = transition.before
        if topology_revision is not None:
            before = ProjectRevision(model_revision=before.model_revision, topology_revision=int(topology_revision), presentation_revision=before.presentation_revision, persisted_revision=before.persisted_revision)
        self._current = before
        self._redo.append(_RevisionTransition(before, transition.after))
        return self._current

    def record_redo(self, *, topology_revision: int | None = None) -> ProjectRevision:
        """Restore the exact revision state represented by the latest redo transition."""
        if not self._redo:
            raise RuntimeError("No revision transition is available to redo.")
        transition = self._redo.pop()
        if transition.before != self._current:
            raise RuntimeError("Revision redo state is inconsistent with current revision.")
        after = transition.after
        if topology_revision is not None:
            if not isinstance(topology_revision, int) or isinstance(topology_revision, bool) or topology_revision < 0:
                raise ValueError("topology_revision must be a non-negative integer.")
            after = ProjectRevision(
                model_revision=after.model_revision,
                topology_revision=topology_revision,
                presentation_revision=after.presentation_revision,
                persisted_revision=after.persisted_revision,
            )
        self._current = after
        self._undo.append(_RevisionTransition(transition.before, after))
        return self._current

    def initialize_from_network(self, *, topology_revision: int) -> ProjectRevision:
        """Initialize the active project's revision from pre-existing Core state."""
        if not isinstance(topology_revision, int) or isinstance(topology_revision, bool) or topology_revision < 0:
            raise ValueError("topology_revision must be a non-negative integer.")
        self._current = ProjectRevision(topology_revision=topology_revision)
        self._persisted_state = self._current
        self._undo.clear()
        self._redo.clear()
        self._persisted_generation = 0
        return self._current

    def reset_for_project(self) -> ProjectRevision:
        """Reset revision/history state only after successful project activation."""
        self._current = ProjectRevision()
        self._persisted_state = self._current
        self._undo.clear()
        self._redo.clear()
        self._persisted_generation = 0
        return self._current


__all__ = ["RevisionService"]
