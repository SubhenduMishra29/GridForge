# ============================================================
# File: core/application/draft_study.py
# GridForge V2 — Isolated Draft Study Preparation
# ============================================================

"""Build detached study candidates from Application-owned DraftNetwork state."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from types import SimpleNamespace
from typing import Any, Mapping

from core.application.command_handlers import build_model_command_handlers
from core.application.context import ApplicationContext
from core.application.draft.handlers import CommitNetworkHandler
from core.application.draft.network import DraftNetwork
from core.application.services.model_service import ModelService
from core.application.services.simple_wire_service import SimpleWireConnectionCommandHandlers
from core.application.transaction import Transaction
from core.network.network import Network
from core.network.topology_snapshot import TopologySnapshot
from core.persistence.network_serializer import deserialize_network, serialize_network


@dataclass(frozen=True, slots=True)
class DraftStudyCandidate:
    """Detached Core candidate and its canonical topology for one draft revision."""

    network: Network
    topology_snapshot: TopologySnapshot
    draft_revision: str
    topology_revision: int


class DraftStudyPreparationService:
    """Materialize draft authoring through the same validated commit path on a clone.

    The service never receives the live project Network. Its only mutation target
    is a detached Network reconstructed from the captured ProjectSnapshot.
    """

    def __init__(self, creation_contract_provider: Any) -> None:
        if not callable(creation_contract_provider):
            raise TypeError("creation_contract_provider must be callable.")
        self._creation_contract_provider = creation_contract_provider

    @staticmethod
    def revision(value: DraftNetwork | Mapping[str, Any]) -> str:
        """Return a deterministic content revision for a canonical draft snapshot."""
        payload = value.to_dict() if isinstance(value, DraftNetwork) else value
        if not isinstance(payload, Mapping):
            raise TypeError("Draft revision input must be DraftNetwork or a mapping.")
        try:
            canonical = json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "DraftNetwork contains values that cannot form a canonical study revision."
            ) from exc
        return sha256(canonical.encode("utf-8")).hexdigest()

    def prepare(
        self,
        project_snapshot: Any,
        draft_network: DraftNetwork,
        *,
        document_id: str,
    ) -> DraftStudyCandidate:
        """Apply one immutable draft snapshot to an isolated candidate Network."""
        if project_snapshot is None:
            raise ValueError("A captured ProjectSnapshot is required.")
        if not isinstance(draft_network, DraftNetwork):
            raise TypeError("draft_network must be DraftNetwork.")
        if not isinstance(document_id, str) or not document_id.strip():
            raise ValueError("Draft study preparation requires a document_id.")

        project_id = str(getattr(project_snapshot, "project_id", "")).strip()
        activation_generation = getattr(project_snapshot, "activation_generation", None)
        base_network = getattr(project_snapshot, "network", None)
        if not project_id or not isinstance(activation_generation, int) or activation_generation < 1:
            raise ValueError("ProjectSnapshot has invalid project/generation provenance.")
        if not isinstance(base_network, Network):
            raise TypeError("ProjectSnapshot must contain a Core Network snapshot.")
        if (
            draft_network.project_id != project_id
            or draft_network.activation_generation != activation_generation
        ):
            raise ValueError("DraftNetwork project/generation does not match ProjectSnapshot.")
        if not draft_network.equipment and not draft_network.connections:
            raise ValueError("Draft study requires a non-empty DraftNetwork.")

        # Serialize/deserialize is the canonical Core detachment boundary. The
        # reconstructed revision counter is reset to the captured source value
        # before the draft commit path applies its own candidate mutations.
        candidate_network = deserialize_network(serialize_network(base_network))
        candidate_network.project_id = project_id
        candidate_network.activation_generation = activation_generation
        candidate_network.state.topology_revision = int(base_network.state.topology_revision)
        candidate_network.rebuild_topology()

        candidate_draft = DraftNetwork.from_dict(
            draft_network.to_dict(),
            project_id=project_id,
            activation_generation=activation_generation,
        )
        model_service = ModelService(candidate_network)
        handlers = dict(build_model_command_handlers(model_service))
        handlers.update(SimpleWireConnectionCommandHandlers().handlers())
        context = ApplicationContext(network=candidate_network)
        transaction = Transaction()

        def execute_candidate_command(command: Any, active_transaction: Transaction) -> Any:
            handler = handlers.get(getattr(command, "command_type", ""))
            if handler is None:
                raise ValueError(
                    f"Draft study candidate does not support command "
                    f"{getattr(command, 'command_type', None)!r}."
                )
            result = handler(command, context, active_transaction)
            if not getattr(result, "success", False):
                raise ValueError(
                    getattr(result, "message", "")
                    or f"Candidate command {command.command_type!r} was rejected."
                )
            return result

        payload = {
            "document_id": document_id.strip(),
            "project_id": project_id,
            "activation_generation": activation_generation,
            "draft_network": candidate_draft.to_dict(),
        }
        commit_handler = CommitNetworkHandler(
            lambda requested_document_id: (
                candidate_draft if requested_document_id == document_id.strip() else None
            ),
            execute_candidate_command,
            self._creation_contract_provider,
        )

        # This is the canonical Application Draft→Core translation and
        # validation path, but its command executor is bound exclusively to
        # the detached candidate Network. The candidate draft is disposable.
        commit_handler(SimpleNamespace(payload=payload), context, transaction)
        transaction.commit()

        candidate_network.rebuild_topology()
        candidate_network.validate()
        topology_snapshot = candidate_network.topology_snapshot
        if not isinstance(topology_snapshot, TopologySnapshot):
            raise ValueError("Draft study candidate did not produce a canonical TopologySnapshot.")
        if (
            topology_snapshot.project_id != project_id
            or topology_snapshot.activation_generation != activation_generation
            or topology_snapshot.topology_revision != candidate_network.state.topology_revision
        ):
            raise ValueError("Draft study candidate topology provenance is inconsistent.")

        return DraftStudyCandidate(
            network=candidate_network,
            topology_snapshot=topology_snapshot,
            draft_revision=self.revision(draft_network),
            topology_revision=topology_snapshot.topology_revision,
        )


__all__ = ["DraftStudyCandidate", "DraftStudyPreparationService"]
