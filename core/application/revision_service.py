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
    """
    Own the authoritative in-memory revision state for the active project.

    The service deliberately tracks state transitions rather than inferring
    dirty state from command-history depth. This makes undo/redo restore the
    exact revision state that existed before the corresponding mutation.
    """

    _TOPOLOGY_COMMANDS = frozenset({
        "model.create_line", "model.delete_line",
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
    })

    def __init__(self) -> None:
        self._current = ProjectRevision()
        self._persisted_state = self._current
        self._undo: list[_RevisionTransition] = []
        self._redo: list[_RevisionTransition] = []
        self._persisted_generation = 0

    @property
    def revision(self) -> ProjectRevision:
        """Return the immutable current revision snapshot."""
        return self._current

    @property
    def is_dirty(self) -> bool:
        """Return whether the current engineering/presentation state is unsaved."""
        return self._current != self._persisted_state

    def reset_for_project(self) -> ProjectRevision:
        """Reset revision state for a newly active project."""
        self._persisted_generation += 1
        self._current = ProjectRevision(
            persisted_revision=self._persisted_generation,
        )
        self._persisted_state = self._current
        self._undo.clear()
        self._redo.clear()
        return self._current

    def record_command_success(self, command: Command) -> ProjectRevision:
        """Record one successfully committed persistent command."""
        if not isinstance(command, Command):
            raise TypeError("command must be a Command.")

        before = self._current
        after = self._next_for_command(before, command)
        if after == before:
            return before

        self._undo.append(_RevisionTransition(before, after))
        self._redo.clear()
        self._current = after
        return after

    def record_presentation_change(self) -> ProjectRevision:
        """Record one successfully committed persistent SLD presentation edit."""
        before = self._current
        after = ProjectRevision(
            model_revision=before.model_revision,
            topology_revision=before.topology_revision,
            presentation_revision=before.presentation_revision + 1,
            persisted_revision=before.persisted_revision,
        )
        self._undo.append(_RevisionTransition(before, after))
        self._redo.clear()
        self._current = after
        return after

    def record_undo(self) -> ProjectRevision:
        """Restore the exact revision state preceding the latest mutation."""
        if not self._undo:
            return self._current
        transition = self._undo.pop()
        if transition.after != self._current:
            raise RuntimeError("Revision undo state is inconsistent with current revision.")
        self._redo.append(transition)
        self._current = transition.before
        return self._current

    def record_redo(self) -> ProjectRevision:
        """Restore the exact revision state produced by the latest undone mutation."""
        if not self._redo:
            return self._current
        transition = self._redo.pop()
        if transition.before != self._current:
            raise RuntimeError("Revision redo state is inconsistent with current revision.")
        self._undo.append(transition)
        self._current = transition.after
        return self._current

    def mark_persisted(self) -> ProjectRevision:
        """Mark the current state as successfully persisted."""
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
    def _next_for_command(
        cls,
        revision: ProjectRevision,
        command: Command,
    ) -> ProjectRevision:
        command_type = command.command_type
        model_revision = revision.model_revision
        topology_revision = revision.topology_revision

        if command_type in cls._TOPOLOGY_COMMANDS:
            model_revision += 1
            topology_revision += 1
        elif command_type.startswith("model."):
            model_revision += 1
        else:
            return revision

        return ProjectRevision(
            model_revision=model_revision,
            topology_revision=topology_revision,
            presentation_revision=revision.presentation_revision,
            persisted_revision=revision.persisted_revision,
        )


__all__ = ["RevisionService"]
