"""Project-scoped Application authority for physical instrumentation wiring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.model.instrument_wiring import InstrumentationWiringInventory


@dataclass(frozen=True, slots=True)
class InstrumentationWiringServiceState:
    project_id: str | None
    activation_generation: int
    inventory: InstrumentationWiringInventory


class InstrumentationWiringService:
    """Activate and expose the canonical inventory for exactly one project generation.

    This first Application slice intentionally provides lifecycle ownership and
    immutable snapshots only. Mutations will be added through commands in the
    next implementation slice; callers cannot edit the inventory in place.
    """

    def __init__(self) -> None:
        self._project_id: str | None = None
        self._activation_generation = 0
        self._inventory = InstrumentationWiringInventory()

    @property
    def project_id(self) -> str | None:
        return self._project_id

    @property
    def activation_generation(self) -> int:
        return self._activation_generation

    @property
    def inventory(self) -> InstrumentationWiringInventory:
        return self._inventory

    def snapshot_state(self) -> InstrumentationWiringServiceState:
        return InstrumentationWiringServiceState(
            self._project_id, self._activation_generation, self._inventory
        )

    def restore_state(self, state: InstrumentationWiringServiceState) -> None:
        if not isinstance(state, InstrumentationWiringServiceState):
            raise TypeError("state must be an InstrumentationWiringServiceState.")
        self._project_id = state.project_id
        self._activation_generation = state.activation_generation
        self._inventory = state.inventory

    def activate(
        self,
        context: Any | None,
        inventory: InstrumentationWiringInventory | None = None,
        *,
        generation: int = 0,
    ) -> InstrumentationWiringServiceState:
        """Install a candidate project inventory and return the prior state."""
        candidate = inventory if inventory is not None else InstrumentationWiringInventory()
        if not isinstance(candidate, InstrumentationWiringInventory):
            raise TypeError("inventory must be an InstrumentationWiringInventory.")
        if context is None:
            if candidate != InstrumentationWiringInventory():
                raise ValueError("A project-less activation cannot contain instrumentation wiring.")
            next_project_id = None
            next_generation = 0
        else:
            project_id = getattr(context, "project_id", None)
            if not isinstance(project_id, str) or not project_id.strip():
                raise ValueError("Project context must expose a non-empty project_id.")
            if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
                raise ValueError("generation must be a positive integer for an active project.")
            next_project_id = project_id.strip()
            next_generation = generation
        previous = self.snapshot_state()
        self._project_id = next_project_id
        self._activation_generation = next_generation
        self._inventory = candidate
        return previous


__all__ = ["InstrumentationWiringService", "InstrumentationWiringServiceState"]
