"""Project-scoped Application authority for physical instrumentation wiring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.application.command import Command
from core.application.commands.instrumentation_wiring_commands import (
    SET_INSTRUMENTATION_WIRING_INVENTORY,
    SetInstrumentationWiringInventoryCommand,
)
from core.application.results import ApplicationResult
from core.application.transaction import Transaction
from core.model.instrument_wiring import InstrumentationWiringInventory


@dataclass(frozen=True, slots=True)
class InstrumentationWiringServiceState:
    project_id: str | None
    activation_generation: int
    network: Any | None
    inventory: InstrumentationWiringInventory


class InstrumentationWiringService:
    """Project lifecycle, canonical terminal validation and controlled mutation."""

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

    def create_replace_command(
        self, replacement: InstrumentationWiringInventory
    ) -> SetInstrumentationWiringInventoryCommand:
        """Capture the current snapshot as a stale-state precondition."""
        return SetInstrumentationWiringInventoryCommand(
            expected_inventory=self._inventory,
            replacement_inventory=replacement,
        )

    def supports(self, command: Command) -> bool:
        return command.command_type == SET_INSTRUMENTATION_WIRING_INVENTORY

    def execute(
        self, command: Command, context: Any, transaction: Transaction
    ) -> ApplicationResult:
        """Apply one atomic inventory replacement with a stale-safe undo journal."""
        if not isinstance(command, SetInstrumentationWiringInventoryCommand):
            raise TypeError("command must be a SetInstrumentationWiringInventoryCommand.")
        if not isinstance(transaction, Transaction) or not transaction.active:
            raise ValueError("Instrumentation wiring mutations require an active transaction.")
        network = getattr(context, "network", None)
        if self._project_id is None or self._network is None or network is not self._network:
            raise ValueError("Instrumentation wiring command does not target the active project Network.")
        expected = command.payload["expected_inventory"]
        replacement = command.payload["replacement_inventory"]
        if self._inventory is not expected:
            raise ValueError("Instrumentation wiring inventory changed since the command was prepared.")
        self._validate_inventory_terminals(network, replacement)
        previous = self._inventory
        project_id = self._project_id
        generation = self._activation_generation
        self._inventory = replacement

        def undo() -> None:
            if (
                self._project_id != project_id
                or self._activation_generation != generation
                or self._network is not network
                or self._inventory is not replacement
            ):
                raise RuntimeError(
                    "Stale instrumentation wiring undo rejected; active project or inventory changed."
                )
            self._inventory = previous

        try:
            transaction.record_undo(undo)
        except Exception:
            self._inventory = previous
            raise
        return ApplicationResult.success_result(
            value=replacement,
            message="Instrumentation wiring inventory updated.",
            metadata={
                "project_id": project_id,
                "activation_generation": generation,
                "cables": len(replacement.cables),
                "cores": len(replacement.cores),
                "panel_wires": len(replacement.panel_wires),
                "signals": len(replacement.signals),
            },
        )

    def handlers(self) -> dict[str, Any]:
        return {SET_INSTRUMENTATION_WIRING_INVENTORY: self.execute}

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


class InstrumentationWiringCommandHandlers:
    """Bind wiring inventory commands to the project-scoped Application service."""

    def __init__(self, service: InstrumentationWiringService) -> None:
        if not isinstance(service, InstrumentationWiringService):
            raise TypeError("service must be an InstrumentationWiringService.")
        self._service = service

    def handlers(self) -> dict[str, Any]:
        return self._service.handlers()


__all__ = [
    "InstrumentationWiringService",
    "InstrumentationWiringServiceState",
    "InstrumentationWiringCommandHandlers",
]
