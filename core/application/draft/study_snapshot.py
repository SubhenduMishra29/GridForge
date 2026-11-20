# ============================================================
# File: core/application/draft/study_snapshot.py
# GridForge V2 — Isolated Draft Study Candidate Network
# ============================================================

"""Build detached study networks from immutable Application DraftNetwork snapshots."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from core.application.command_handlers import build_model_command_handlers
from core.application.command_manager import CommandManager
from core.application.commands.draft_commands import COMMIT_NETWORK, CommitNetworkCommand
from core.application.context import ApplicationContext
from core.application.draft.handlers import CommitNetworkHandler
from core.application.draft.network import DraftNetwork
from core.application.services.model_service import ModelService
from core.application.services.simple_wire_service import SimpleWireConnectionCommandHandlers
from core.network.topology_snapshot import TopologySnapshot


class DraftStudyPreparationError(ValueError):
    """A draft cannot be converted into a solver-ready detached candidate."""

    def __init__(self, code: str, message: str, *, details: Mapping[str, Any] | None = None) -> None:
        self.code = str(code).strip()
        self.details = dict(details or {})
        super().__init__(str(message))


class DraftStudyNetworkBuilder:
    """Apply the canonical DraftNetwork commit path to a detached Network only."""

    _SUPPORTED_EQUIPMENT = {
        "power_flow": frozenset({
            "bus", "grid", "generator", "synchronous_machine", "load", "motor",
            "shunt", "capacitor", "reactor", "solar", "battery", "line", "cable",
            "transformer", "switch", "breaker", "disconnector", "fuse",
        }),
        "short_circuit": frozenset({
            "bus", "grid", "generator", "synchronous_machine", "motor",
            "line", "cable", "transformer", "switch", "breaker", "disconnector", "fuse",
        }),
    }

    def __init__(self, creation_contract_registry: Any) -> None:
        if creation_contract_registry is None or not callable(
            getattr(creation_contract_registry, "resolve", None)
        ):
            raise TypeError("A trusted Application CreationContractRegistry is required.")
        self._creation_contract_registry = creation_contract_registry

    @classmethod
    def _unsupported_equipment(
        cls,
        draft_snapshot: Mapping[str, Any],
        study_type: str,
    ) -> tuple[str, ...]:
        supported = cls._SUPPORTED_EQUIPMENT[study_type]
        unsupported = []
        for item in draft_snapshot.get("equipment", ()):
            if not isinstance(item, Mapping):
                unsupported.append("<malformed-draft-equipment>")
                continue
            equipment_type = str(item.get("equipment_type", "")).strip().lower()
            draft_id = str(item.get("draft_id", "")).strip() or "<missing-id>"
            if equipment_type not in supported:
                unsupported.append(f"{equipment_type or '<missing-type>'}:{draft_id}")
        return tuple(sorted(unsupported))

    def build(
        self,
        *,
        committed_network: Any,
        draft_snapshot: Mapping[str, Any],
        project_id: str,
        activation_generation: int,
        document_id: str,
        study_type: str,
    ) -> Any:
        """Return a detached candidate Network; never mutate the active project Network."""
        normalized_type = str(study_type).strip().lower()
        if normalized_type not in self._SUPPORTED_EQUIPMENT:
            raise DraftStudyPreparationError(
                "UNSUPPORTED_DRAFT_STUDY_TYPE",
                "Draft studies support Power Flow and Short-Circuit only.",
                details={"study_type": normalized_type},
            )
        if committed_network is None:
            raise DraftStudyPreparationError(
                "COMMITTED_SNAPSHOT_MISSING",
                "A detached committed ProjectSnapshot Network is required.",
            )
        if not isinstance(draft_snapshot, Mapping):
            raise DraftStudyPreparationError(
                "DRAFT_SNAPSHOT_INVALID",
                "The captured DraftNetwork snapshot is not a mapping.",
            )
        if str(draft_snapshot.get("project_id", project_id)) != project_id:
            raise DraftStudyPreparationError(
                "DRAFT_PROJECT_MISMATCH",
                "DraftNetwork project identity does not match the active project.",
            )
        if int(draft_snapshot.get("activation_generation", activation_generation)) > activation_generation:
            raise DraftStudyPreparationError(
                "DRAFT_GENERATION_MISMATCH",
                "DraftNetwork belongs to a newer project activation.",
            )

        unsupported = self._unsupported_equipment(draft_snapshot, normalized_type)
        if unsupported:
            raise DraftStudyPreparationError(
                "UNSUPPORTED_DRAFT_STUDY_MODEL",
                (
                    f"{normalized_type} cannot be prepared because these draft elements "
                    "have no supported solver model: " + ", ".join(unsupported)
                ),
                details={"study_type": normalized_type, "unsupported_elements": unsupported},
            )

        try:
            draft = DraftNetwork.from_dict(
                draft_snapshot,
                project_id=project_id,
                activation_generation=activation_generation,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise DraftStudyPreparationError(
                "DRAFT_SNAPSHOT_INVALID",
                f"DraftNetwork snapshot could not be reconstructed: {exc}",
            ) from exc
        if not draft.equipment and not draft.connections:
            raise DraftStudyPreparationError(
                "DRAFT_NETWORK_EMPTY",
                "The active DraftNetwork has no equipment or connections to study.",
            )

        # The supplied Network is already detached by Application.capture_project_snapshot().
        # All canonical creation and endpoint resolution below therefore stays off the live Core.
        candidate_network = committed_network
        candidate_network.project_id = project_id
        candidate_network.activation_generation = activation_generation
        if candidate_network.state.topology_dirty or not candidate_network.state.topology_valid:
            candidate_network.rebuild_topology()

        context = ApplicationContext(network=candidate_network)
        model_service = ModelService(candidate_network)
        handlers = dict(build_model_command_handlers(model_service))
        handlers.update(SimpleWireConnectionCommandHandlers().handlers())
        command_manager = CommandManager(context=context, handlers=handlers)

        def draft_provider(requested_document_id: str | None = None):
            if requested_document_id is not None and requested_document_id != document_id:
                return None
            return draft

        command_manager.register_handler(
            COMMIT_NETWORK,
            CommitNetworkHandler(
                draft_provider=draft_provider,
                command_executor=command_manager.execute_in_transaction,
                creation_contract_provider=lambda: self._creation_contract_registry,
            ),
        )
        command = CommitNetworkCommand(
            project_id=project_id,
            activation_generation=activation_generation,
            draft_network=draft.to_dict(),
            document_id=document_id,
        )
        try:
            result = command_manager.execute(command)
        except Exception as exc:
            raise DraftStudyPreparationError(
                "DRAFT_CANDIDATE_COMMIT_FAILED",
                f"Detached DraftNetwork commit failed: {type(exc).__name__}: {exc}",
            ) from exc
        if not result.success:
            raise DraftStudyPreparationError(
                "DRAFT_CANDIDATE_COMMIT_FAILED",
                result.message or "Detached DraftNetwork commit was rejected.",
                details=dict(getattr(result, "metadata", {}) or {}),
            )
        if command_manager.integrity_state != "CLEAN":
            raise DraftStudyPreparationError(
                "DRAFT_CANDIDATE_INTEGRITY_FAILED",
                "Detached candidate command execution did not finish in a clean transaction state.",
                details={"integrity_state": command_manager.integrity_state},
            )

        if candidate_network.state.topology_dirty or not candidate_network.state.topology_valid:
            candidate_network.rebuild_topology()
        if candidate_network.state.topology_dirty or not candidate_network.state.topology_valid:
            raise DraftStudyPreparationError(
                "DRAFT_CANDIDATE_TOPOLOGY_INVALID",
                "Detached DraftNetwork candidate did not produce a valid canonical Core topology.",
            )
        topology = candidate_network.topology_snapshot
        if not isinstance(topology, TopologySnapshot):
            raise DraftStudyPreparationError(
                "DRAFT_CANDIDATE_TOPOLOGY_MISSING",
                "Detached DraftNetwork candidate has no canonical TopologySnapshot.",
            )
        if (
            topology.project_id != project_id
            or topology.activation_generation != activation_generation
            or topology.topology_revision != candidate_network.state.topology_revision
        ):
            raise DraftStudyPreparationError(
                "DRAFT_CANDIDATE_PROVENANCE_MISMATCH",
                "Detached candidate Network and TopologySnapshot provenance do not match.",
            )
        return candidate_network


__all__ = ["DraftStudyPreparationError", "DraftStudyNetworkBuilder"]
