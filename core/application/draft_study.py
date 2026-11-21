"""Application-owned isolated Network preparation for draft numerical studies."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Any

from core.network.network import Network
from core.network.topology_snapshot import TopologySnapshot
from core.persistence.network_serializer import deserialize_network, serialize_network
from core.protection.project_configuration import ProtectionProjectConfiguration

from .command_handlers import ModelCommandHandlers
from .command_manager import CommandManager
from .commands.draft_commands import CommitNetworkCommand
from .draft.handlers import CommitNetworkHandler
from .draft.network import DraftNetwork
from .relay_command_handlers import RelayCommandHandlers
from .services.model_service import ModelService
from .services.relay_model_service import RelayModelService
from .services.simple_wire_service import SimpleWireConnectionCommandHandlers
from .transaction import Transaction


class DraftStudyPreparationError(ValueError):
    """Raised when a DraftNetwork cannot form a supported isolated study input."""


@dataclass(frozen=True, slots=True)
class _CandidateCommandContext:
    """Minimal Application command context bound only to the detached candidate."""

    network: Network


@dataclass(frozen=True, slots=True)
class DraftStudyCandidate:
    """Detached Core Network and canonical topology produced from one draft snapshot."""

    network: Network
    topology_snapshot: TopologySnapshot
    draft_to_core_ids: Mapping[str, str]
    solver_element_ids: tuple[str, ...]
    topology_only_element_ids: tuple[str, ...]
    excluded_element_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.network, Network):
            raise TypeError("network must be a Core Network.")
        if not isinstance(self.topology_snapshot, TopologySnapshot):
            raise TypeError("topology_snapshot must be a TopologySnapshot.")
        if not isinstance(self.draft_to_core_ids, Mapping):
            raise TypeError("draft_to_core_ids must be a mapping.")
        identity_map: dict[str, str] = {}
        for draft_id, core_id in self.draft_to_core_ids.items():
            draft_key = str(draft_id).strip()
            core_value = str(core_id).strip()
            if not draft_key or not core_value or draft_key in identity_map:
                raise ValueError("draft_to_core_ids must contain unique non-empty draft/Core identities.")
            identity_map[draft_key] = core_value
        if len(set(identity_map.values())) != len(identity_map):
            raise ValueError("draft_to_core_ids must map each draft identity to a unique Core identity.")
        object.__setattr__(self, "draft_to_core_ids", MappingProxyType(identity_map))
        for name in ("solver_element_ids", "topology_only_element_ids", "excluded_element_ids"):
            values = tuple(str(value).strip() for value in getattr(self, name))
            if any(not value for value in values) or len(values) != len(set(values)):
                raise ValueError(f"{name} must contain unique non-empty Core identities.")
            object.__setattr__(self, name, values)
        core_ids = set(identity_map.values())
        if any(not set(getattr(self, name)).issubset(core_ids) for name in ("solver_element_ids", "topology_only_element_ids", "excluded_element_ids")):
            raise ValueError("DraftStudyCandidate classifications must reference mapped Core identities.")
        if (
            getattr(self.network, "project_id", None) != self.topology_snapshot.project_id
            or getattr(self.network, "activation_generation", None) != self.topology_snapshot.activation_generation
            or getattr(getattr(self.network, "state", None), "topology_revision", None)
            != self.topology_snapshot.topology_revision
            or getattr(self.network, "topology_snapshot", None) != self.topology_snapshot
        ):
            raise ValueError("DraftStudyCandidate Network and TopologySnapshot provenance differ.")
        groups = (
            set(self.solver_element_ids),
            set(self.topology_only_element_ids),
            set(self.excluded_element_ids),
        )
        if any(groups[left].intersection(groups[right]) for left in range(len(groups)) for right in range(left + 1, len(groups))):
            raise ValueError("DraftStudyCandidate element classifications must be disjoint.")


    def remap_configuration(self, configuration: Any) -> Any:
        """Translate draft-scoped IDs to the exact Core identities in this candidate."""
        from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
        from core.analysis.short_circuit_configuration import ShortCircuitStudyConfiguration

        def map_identity(value: str) -> str:
            return self.draft_to_core_ids.get(value, value)

        def map_node_identity(value: str) -> str:
            direct = map_identity(value)
            if direct != value:
                return direct
            try:
                parts = json.loads(value)
            except (TypeError, ValueError):
                return value
            if not isinstance(parts, list) or not all(isinstance(part, str) for part in parts):
                return value
            mapped = [map_identity(part) for part in parts]
            return json.dumps(mapped, ensure_ascii=True, separators=(",", ":")) if mapped != parts else value

        if isinstance(configuration, PowerFlowStudyConfiguration):
            bus_types: dict[str, Any] = {}
            for bus_id, bus_type in configuration.bus_types.items():
                core_id = map_identity(bus_id)
                if core_id in bus_types:
                    raise DraftStudyPreparationError(
                        f"Power Flow bus identities collide after draft/Core resolution: {core_id!r}."
                    )
                bus_types[core_id] = bus_type
            voltage_bases: dict[str, float] = {}
            for bus_id, voltage in configuration.voltage_bases_kv.items():
                core_id = map_identity(bus_id)
                if core_id in voltage_bases:
                    raise DraftStudyPreparationError(
                        f"Power Flow voltage-base identities collide after draft/Core resolution: {core_id!r}."
                    )
                voltage_bases[core_id] = voltage
            return replace(
                configuration,
                bus_types=bus_types,
                voltage_bases_kv=voltage_bases,
            )

        if isinstance(configuration, ShortCircuitStudyConfiguration):
            if configuration.phase_domain_case is not None:
                raise DraftStudyPreparationError(
                    "A prebuilt phase-domain case is bound to its original topology snapshot. "
                    "For draft studies, supply explicit phase_domain_sources and phase_domain_faults "
                    "so the phase-domain graph can be rebuilt from the isolated candidate Network."
                )
            from core.solver.short_circuit.phase_domain_solver import (
                PhaseDomainFaultConnection,
                PhaseDomainMultiConductorSource,
                PhaseDomainSourceEquivalent,
            )
            if configuration.phase_domain_sources or configuration.phase_domain_faults:
                unsupported_sources = tuple(
                    str(getattr(item, "id", ""))
                    for item in getattr(self.network, "synchronous_machines", ())
                    if getattr(item, "in_service", True) is True
                )
                if unsupported_sources:
                    raise DraftStudyPreparationError(
                        "Phase-domain short-circuit preparation does not yet admit synchronous-machine "
                        "source equivalents; fail-closed source IDs: " + ", ".join(sorted(unsupported_sources))
                    )
            sources = []
            for source in configuration.phase_domain_sources:
                if isinstance(source, PhaseDomainSourceEquivalent):
                    sources.append(replace(
                        source,
                        source_id=map_identity(source.source_id),
                        node_id=map_node_identity(source.node_id),
                    ))
                elif isinstance(source, PhaseDomainMultiConductorSource):
                    sources.append(replace(
                        source,
                        source_id=map_identity(source.source_id),
                        node_ids=tuple(map_node_identity(item) for item in source.node_ids),
                    ))
                else:
                    raise DraftStudyPreparationError(
                        f"Unsupported phase-domain source type for draft study: {type(source).__name__}."
                    )
            faults = []
            for fault in configuration.phase_domain_faults:
                if not isinstance(fault, PhaseDomainFaultConnection):
                    raise DraftStudyPreparationError(
                        f"Unsupported phase-domain fault type for draft study: {type(fault).__name__}."
                    )
                faults.append(replace(
                    fault,
                    from_node_id=map_node_identity(fault.from_node_id),
                    to_node_id=map_node_identity(fault.to_node_id),
                ))
            element_ids = tuple(map_identity(item) for item in configuration.element_ids)
            if len(set(element_ids)) != len(element_ids):
                raise DraftStudyPreparationError(
                    "Short Circuit element identities collide after draft/Core resolution."
                )
            return replace(
                configuration,
                fault_bus_id=map_identity(configuration.fault_bus_id),
                element_ids=element_ids,
                phase_domain_sources=tuple(sources),
                phase_domain_faults=tuple(faults),
            )

        raise DraftStudyPreparationError(
            "Draft studies require a typed PowerFlowStudyConfiguration or ShortCircuitStudyConfiguration."
        )


class DraftStudyCandidateBuilder:
    """Materialize a detached candidate using the exact canonical commit validators."""

    _SOLVER_MODELS = {
        "power_flow": frozenset({
            "bus", "grid", "generator", "synchronous_machine", "load", "motor",
            "solar", "battery", "line", "cable", "transformer", "shunt",
            "capacitor", "reactor",
        }),
        "short_circuit": frozenset({
            "bus", "grid", "generator", "synchronous_machine", "motor",
            "line", "cable", "transformer",
        }),
    }
    _TOPOLOGY_ONLY_MODELS = frozenset({"breaker", "switch", "disconnector", "fuse"})
    _NON_SOLVER_MODELS = frozenset({
        "current_transformer", "potential_transformer",
        "capacitive_voltage_transformer", "relay",
    })

    def __init__(self, creation_contract_registry: Any) -> None:
        if creation_contract_registry is None or not callable(getattr(creation_contract_registry, "resolve", None)):
            raise TypeError("creation_contract_registry must expose resolve().")
        self._creation_contract_registry = creation_contract_registry

    def build(
        self,
        base_network: Network,
        draft_network: DraftNetwork,
        *,
        document_id: str,
        study_type: str,
    ) -> DraftStudyCandidate:
        if not isinstance(base_network, Network):
            raise TypeError("base_network must be a detached Core Network.")
        if not isinstance(draft_network, DraftNetwork):
            raise TypeError("draft_network must be a detached DraftNetwork.")
        if not isinstance(document_id, str) or not document_id.strip():
            raise ValueError("document_id must be a non-empty string.")
        study_type = str(study_type).strip().lower()
        if study_type not in self._SOLVER_MODELS:
            raise DraftStudyPreparationError(
                f"Draft studies support power_flow and short_circuit, not {study_type!r}."
            )
        if not draft_network.equipment and not draft_network.connections:
            raise DraftStudyPreparationError("The active DraftNetwork is empty.")

        solver_items: list[Any] = []
        topology_items: list[Any] = []
        excluded_items: list[Any] = []
        unsupported: list[str] = []
        solver_types = self._SOLVER_MODELS[study_type]
        for item in draft_network.equipment:
            equipment_type = str(item.equipment_type).strip().lower()
            if equipment_type in solver_types:
                solver_items.append(item)
            elif equipment_type in self._TOPOLOGY_ONLY_MODELS:
                topology_items.append(item)
            elif equipment_type in self._NON_SOLVER_MODELS:
                excluded_items.append(item)
            else:
                unsupported.append(f"{item.draft_id} ({equipment_type})")
        if unsupported:
            raise DraftStudyPreparationError(
                f"{study_type} has no declared solver model for draft element(s): "
                + ", ".join(sorted(unsupported))
                + ". No numerical defaults or substitute models were fabricated."
            )

        project_id = draft_network.project_id
        activation_generation = draft_network.activation_generation
        if getattr(base_network, "project_id", None) != project_id:
            raise DraftStudyPreparationError("DraftNetwork and detached base Network project identities differ.")
        if getattr(base_network, "activation_generation", None) != activation_generation:
            raise DraftStudyPreparationError("DraftNetwork and detached base Network activation generations differ.")

        candidate_network = deserialize_network(serialize_network(base_network))
        candidate_network.project_id = project_id
        candidate_network.activation_generation = activation_generation
        candidate_network.state.topology_revision = base_network.state.topology_revision
        candidate_network.rebuild_topology()

        candidate_draft = DraftNetwork.from_dict(
            draft_network.to_dict(),
            project_id=project_id,
            activation_generation=activation_generation,
            revision=draft_network.revision,
            snapshot_id=draft_network.snapshot_id,
        )
        context = _CandidateCommandContext(network=candidate_network)
        model_service = ModelService(candidate_network)
        relay_configuration = ProtectionProjectConfiguration(project_id)
        handler_groups = (
            ModelCommandHandlers(model_service).handlers(),
            SimpleWireConnectionCommandHandlers().handlers(),
            RelayCommandHandlers(
                RelayModelService(
                    candidate_network,
                    protection_configuration_provider=lambda: relay_configuration,
                )
            ).handlers(),
        )
        handlers: dict[str, Any] = {}
        for group in handler_groups:
            overlap = set(handlers).intersection(group)
            if overlap:
                raise DraftStudyPreparationError(
                    "Candidate command composition contains duplicate handlers: "
                    + ", ".join(sorted(overlap))
                )
            handlers.update(group)
        command_manager = CommandManager(context=context, handlers=handlers)
        transaction = Transaction()
        commit_handler = CommitNetworkHandler(
            draft_provider=lambda target: candidate_draft if target == document_id.strip() else None,
            command_executor=command_manager.execute_in_transaction,
            creation_contract_provider=lambda: self._creation_contract_registry,
        )
        command = CommitNetworkCommand(
            project_id=project_id,
            activation_generation=activation_generation,
            draft_network=candidate_draft.to_dict(),
            document_id=document_id.strip(),
        )
        try:
            result = commit_handler(command, context, transaction)
            if not result.success:
                raise DraftStudyPreparationError(
                    result.message or "Canonical DraftNetwork commit preparation failed."
                )
            transaction.commit()
        except BaseException as exc:
            rollback_error = None
            if transaction.active:
                try:
                    transaction.rollback()
                except BaseException as rollback_exc:
                    rollback_error = rollback_exc
            if not isinstance(exc, Exception):
                if rollback_error is not None:
                    raise exc from rollback_error
                raise
            if rollback_error is not None:
                raise DraftStudyPreparationError(
                    f"Isolated candidate rollback failed after {type(exc).__name__}: {exc}; "
                    f"rollback error: {type(rollback_error).__name__}: {rollback_error}"
                ) from rollback_error
            if isinstance(exc, DraftStudyPreparationError):
                raise
            raise DraftStudyPreparationError(
                f"Canonical isolated DraftNetwork commit failed: {type(exc).__name__}: {exc}"
            ) from exc

        try:
            candidate_network.rebuild_topology()
            candidate_network.validate()
        except Exception as exc:
            raise DraftStudyPreparationError(
                f"Candidate Core Network validation failed: {type(exc).__name__}: {exc}"
            ) from exc
        if candidate_network.state.topology_dirty or not candidate_network.state.topology_valid:
            raise DraftStudyPreparationError("Candidate Network did not produce a valid canonical topology.")
        topology_snapshot = candidate_network.topology_snapshot
        if topology_snapshot is None:
            raise DraftStudyPreparationError("Candidate Network did not produce a TopologySnapshot.")
        if (
            topology_snapshot.project_id != project_id
            or topology_snapshot.activation_generation != activation_generation
            or topology_snapshot.topology_revision != candidate_network.state.topology_revision
        ):
            raise DraftStudyPreparationError("Candidate TopologySnapshot provenance is inconsistent.")

        created = result.metadata.get("created_elements", ())
        core_ids_by_draft = {
            str(item.get("draft_id")): str(item.get("core_id"))
            for item in created
            if isinstance(item, Mapping) and item.get("draft_id") and item.get("core_id")
        }
        expected_draft_ids = {item.draft_id for item in draft_network.equipment}
        if (
            set(core_ids_by_draft) != expected_draft_ids
            or len(set(core_ids_by_draft.values())) != len(core_ids_by_draft)
        ):
            raise DraftStudyPreparationError(
                "Canonical commit result did not provide one unique Core identity for every draft equipment item."
            )

        def identities(items: list[Any]) -> tuple[str, ...]:
            return tuple(sorted(core_ids_by_draft[item.draft_id] for item in items))

        return DraftStudyCandidate(
            network=candidate_network,
            topology_snapshot=topology_snapshot,
            solver_element_ids=identities(solver_items),
            topology_only_element_ids=identities(topology_items),
            excluded_element_ids=identities(excluded_items),
            draft_to_core_ids=core_ids_by_draft,
        )


__all__ = [
    "DraftStudyPreparationError",
    "DraftStudyCandidate",
    "DraftStudyCandidateBuilder",
]
