"""Project-scoped Application authority for physical instrumentation wiring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.model.instrument_wiring import InstrumentationWiringInventory


@dataclass(frozen=True, slots=True)
class InstrumentationWiringServiceState:
    project_id: str | None
    activation_generation: int
    network: Any | None
    inventory: InstrumentationWiringInventory


class InstrumentationWiringService:
    """Activate and expose the canonical inventory for one project generation.

    This service owns project lifecycle and read access. Controlled mutations
    are added through Application commands in a subsequent implementation
    slice; the immutable Core inventory cannot be edited in place.
    """

    def __init__(self) -> None:
        self._project_id: str | None = None
        self._activation_generation = 0
        self._network: Any | None = None
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
            self._project_id, self._activation_generation,
            self._network, self._inventory,
        )

    def restore_state(self, state: InstrumentationWiringServiceState) -> None:
        if not isinstance(state, InstrumentationWiringServiceState):
            raise TypeError("state must be an InstrumentationWiringServiceState.")
        self._project_id = state.project_id
        self._activation_generation = state.activation_generation
        self._network = state.network
        self._inventory = state.inventory

    @staticmethod
    def _validate_terminal_reference(network: Any, reference: Any) -> None:
        """Resolve the existing Core identity: equipment ID plus exact role."""
        try:
            equipment = network.get_by_identity(reference.equipment_id)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Wiring terminal owner '{reference.equipment_id}' is not registered in the active Network."
            ) from exc
        if getattr(equipment, "id", None) != reference.equipment_id:
            raise ValueError(
                f"Wiring terminal owner '{reference.equipment_id}' resolved to a different Core identity."
            )
        terminals = getattr(equipment, "terminals", None)
        if terminals is None:
            raise ValueError(
                f"Wiring terminal owner '{reference.equipment_id}' does not expose Core terminals."
            )
        matches = [
            terminal for terminal in terminals
            if terminal.role == reference.terminal_role and terminal.owner is equipment
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Wiring terminal reference {reference.equipment_id}:{reference.terminal_role} "
                f"resolved to {len(matches)} Core terminals; exactly one is required."
            )

    @classmethod
    def _validate_inventory_terminals(cls, network: Any, inventory: InstrumentationWiringInventory) -> None:
        references = []
        for core in inventory.cores:
            references.extend(core.terminal_path)
        for wire in inventory.panel_wires:
            references.extend(wire.terminal_path)
        seen: set[tuple[str, str]] = set()
        for reference in references:
            if reference.identity in seen:
                continue
            seen.add(reference.identity)
            cls._validate_terminal_reference(network, reference)

    def activate(
        self,
        context: Any | None,
        inventory: InstrumentationWiringInventory | None = None,
        *,
        network: Any | None = None,
        generation: int = 0,
    ) -> InstrumentationWiringServiceState:
        """Install a candidate project inventory after validating terminal owners."""
        candidate = inventory if inventory is not None else InstrumentationWiringInventory()
        if not isinstance(candidate, InstrumentationWiringInventory):
            raise TypeError("inventory must be an InstrumentationWiringInventory.")
        if context is None:
            if candidate != InstrumentationWiringInventory():
                raise ValueError("A project-less activation cannot contain instrumentation wiring.")
            next_project_id = None
            next_generation = 0
            next_network = None
        else:
            project_id = getattr(context, "project_id", None)
            if not isinstance(project_id, str) or not project_id.strip():
                raise ValueError("Project context must expose a non-empty project_id.")
            if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
                raise ValueError("generation must be a positive integer for an active project.")
            if network is None or not callable(getattr(network, "get_by_identity", None)):
                raise ValueError("An active project wiring inventory requires the canonical Core Network.")
            self._validate_inventory_terminals(network, candidate)
            next_project_id = project_id.strip()
            next_generation = generation
            next_network = network
        previous = self.snapshot_state()
        self._project_id = next_project_id
        self._activation_generation = next_generation
        self._network = next_network
        self._inventory = candidate
        return previous


__all__ = ["InstrumentationWiringService", "InstrumentationWiringServiceState"]
