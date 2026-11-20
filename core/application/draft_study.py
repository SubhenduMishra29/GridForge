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

    _POWER_FLOW_DRAFT_TYPES = frozenset({
        "bus", "grid", "generator", "synchronous_machine", "load", "motor",
        "solar", "battery", "line", "cable", "transformer", "shunt",
        "capacitor", "reactor", "breaker", "switch", "disconnector", "fuse",
    })
    _SHORT_CIRCUIT_DRAFT_TYPES = frozenset({
        "bus", "grid", "generator", "synchronous_machine", "motor",
        "line", "cable", "transformer", "breaker", "switch",
        "disconnector", "fuse",
    })

    @classmethod
    def validate_solver_eligibility(
        cls,
        draft_network: DraftNetwork,
        study_type: str,
    ) -> None:
        """Reject draft equipment with no explicit model in the selected solver path.

        Breakers, switches, disconnectors and fuses are topology-only inputs:
        their conduction state is consumed by canonical TopologySnapshot
        normalization. They are not fabricated as numerical impedance branches.
        """
        if not isinstance(draft_network, DraftNetwork):
            raise TypeError("draft_network must be DraftNetwork.")
        if study_type == "power_flow":
            supported = cls._POWER_FLOW_DRAFT_TYPES
        elif study_type == "short_circuit":
            supported = cls._SHORT_CIRCUIT_DRAFT_TYPES
        else:
            raise ValueError(
                "Draft solver eligibility is defined only for power_flow and short_circuit."
            )
        unsupported = tuple(sorted(
            (
                str(getattr(item, "draft_id", "")).strip(),
                str(getattr(item, "equipment_type", "")).strip().lower(),
            )
            for item in draft_network.equipment
            if str(getattr(item, "equipment_type", "")).strip().lower() not in supported
        ))
        if unsupported:
            details = ", ".join(
                f"{draft_id or '<missing-id>'}:{equipment_type or '<missing-type>'}"
                for draft_id, equipment_type in unsupported
            )
            raise ValueError(
                f"Draft {study_type.replace('_', ' ')} study cannot model these draft "
                f"equipment items: {details}. Remove them from this candidate or use "
                "a study type with an explicit numerical model; no default impedance "
                "or equivalent source will be synthesized."
            )

    @staticmethod
    def validate_candidate_connectivity(
        candidate: DraftStudyCandidate,
        draft_network: DraftNetwork,
    ) -> None:
        """Require every draft solver element to reach its canonical Bus terminals."""
        if not isinstance(candidate, DraftStudyCandidate):
            raise TypeError("candidate must be DraftStudyCandidate.")
        if not isinstance(draft_network, DraftNetwork):
            raise TypeError("draft_network must be DraftNetwork.")
        attachments: dict[str, list[Any]] = {}
        for record in candidate.topology_snapshot.equipment_bus_attachments:
            attachments.setdefault(str(record.equipment_id), []).append(record)
        required_counts = {
            "grid": 1,
            "generator": 1,
            "synchronous_machine": 1,
            "load": 1,
            "motor": 1,
            "solar": 1,
            "battery": 1,
            "shunt": 1,
            "capacitor": 1,
            "reactor": 1,
            "line": 2,
            "cable": 2,
            "transformer": 2,
            "breaker": 2,
            "switch": 2,
            "disconnector": 2,
            "fuse": 2,
        }
        for item in draft_network.equipment:
            equipment_type = str(item.equipment_type).strip().lower()
            core_id = f"{equipment_type}-{item.draft_id}"
            if equipment_type == "bus":
                if core_id not in candidate.topology_snapshot.bus_ids:
                    raise ValueError(
                        f"Draft Bus {item.draft_id!r} was not materialized in the candidate TopologySnapshot."
                    )
                continue
            expected = required_counts.get(equipment_type)
            if expected is None:
                # Solver-type eligibility is checked separately; keep this
                # guard fail-closed if a future type is added to that list
                # without defining its physical Bus attachment contract.
                raise ValueError(
                    f"Draft equipment {item.draft_id!r} ({equipment_type}) has no "
                    "declared candidate Bus-attachment contract."
                )
            actual_records = attachments.get(core_id, ())
            if len(actual_records) != expected:
                raise ValueError(
                    f"Draft equipment {item.draft_id!r} ({equipment_type}) requires "
                    f"{expected} canonical Bus terminal attachment(s) for this study; "
                    f"found {len(actual_records)}. Complete its DraftConnections "
                    "before running the solver."
                )

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
        if not candidate_network.validate():
            raise ValueError("Draft study candidate Network failed Core structural validation.")
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
