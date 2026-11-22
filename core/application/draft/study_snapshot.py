"""Build an isolated Core Network from one document-scoped DraftNetwork.

This Application service reuses the canonical DraftNetwork commit translation
and Core command handlers, but applies them only to a detached Network copy.
The live project Network and the live DraftNetwork are never mutated.
"""

from __future__ import annotations

from typing import Any

from core.application.command_handlers import build_model_command_handlers
from core.application.command_manager import CommandManager
from core.application.commands.draft_commands import CommitNetworkCommand
from core.application.context import ApplicationContext
from core.application.draft.handlers import CommitNetworkHandler
from core.application.services.model_service import ModelService
from core.application.services.simple_wire_service import SimpleWireConnectionCommandHandlers
from core.application.transaction import Transaction
from core.network.network import Network
from core.network.topology_snapshot import TopologySnapshot
from core.persistence.network_serializer import deserialize_network, serialize_network

from .network import DraftNetwork


class DraftStudySnapshotError(RuntimeError):
    """Raised when a detached candidate Network cannot be built safely."""


class DraftStudyNetworkBuilder:
    """Translate a captured draft into a detached, validated study Network."""

    def __init__(self, creation_contract_provider: Any) -> None:
        if not callable(creation_contract_provider):
            raise TypeError("creation_contract_provider must be callable.")
        self._creation_contract_provider = creation_contract_provider

    def build(
        self,
        base_network: Network,
        draft_snapshot: DraftNetwork,
        *,
        project_id: str,
        activation_generation: int,
    ) -> tuple[Network, TopologySnapshot]:
        if not isinstance(base_network, Network):
            raise TypeError("base_network must be a Core Network.")
        if not isinstance(draft_snapshot, DraftNetwork):
            raise TypeError("draft_snapshot must be a detached DraftNetwork.")
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id must be non-empty.")
        if (
            isinstance(activation_generation, bool)
            or not isinstance(activation_generation, int)
            or activation_generation < 1
        ):
            raise ValueError("activation_generation must be a positive integer.")
        if (
            draft_snapshot.project_id != project_id.strip()
            or draft_snapshot.activation_generation != activation_generation
        ):
            raise ValueError("DraftNetwork scope does not match the requested study project generation.")
        if not draft_snapshot.equipment and not draft_snapshot.connections:
            raise DraftStudySnapshotError("The active SLD document has no pending draft equipment or connections.")

        try:
            # Persistence DTO round-trip is the canonical detached Core copy;
            # no object or registry identity is shared with the live Network.
            candidate = deserialize_network(serialize_network(base_network))
            candidate.project_id = project_id.strip()
            candidate.activation_generation = activation_generation

            context = ApplicationContext(network=candidate)
            model_service = ModelService(candidate)
            handlers = dict(build_model_command_handlers(model_service))
            handlers.update(SimpleWireConnectionCommandHandlers().handlers())
            command_manager = CommandManager(context=context, handlers=handlers)

            # Reuse the exact creation-contract, endpoint-identity, required
            # terminal-connection and Simple Wire validation path used by a
            # real DraftNetwork commit. An incomplete electrical model must not
            # be silently admitted to a numerical study candidate.
            commit_handler = CommitNetworkHandler(
                draft_provider=lambda document_id: draft_snapshot,
                command_executor=command_manager.execute_in_transaction,
                creation_contract_provider=self._creation_contract_provider,
            )
            command = CommitNetworkCommand(
                project_id=project_id.strip(),
                activation_generation=activation_generation,
                draft_network=draft_snapshot.to_dict(),
                document_id=f"draft-study:{draft_snapshot.snapshot_id}",
            )
            transaction = Transaction()
            try:
                result = commit_handler(command, context, transaction)
                if not getattr(result, "success", False):
                    raise DraftStudySnapshotError(
                        getattr(result, "message", "Draft candidate commit was rejected.")
                    )
                transaction.commit()
            except BaseException:
                if transaction.active:
                    transaction.rollback()
                raise

            candidate.rebuild_topology()
            candidate.validate()
            topology = candidate.topology_snapshot
            if not isinstance(topology, TopologySnapshot):
                raise DraftStudySnapshotError("Candidate Network did not produce a canonical TopologySnapshot.")
            if (
                topology.project_id != project_id.strip()
                or topology.activation_generation != activation_generation
                or topology.topology_revision != candidate.state.topology_revision
            ):
                raise DraftStudySnapshotError("Candidate topology provenance does not match its detached Network.")
            return candidate, topology
        except DraftStudySnapshotError:
            raise
        except Exception as exc:
            raise DraftStudySnapshotError(
                f"Unable to prepare the isolated draft study Network: {type(exc).__name__}: {exc}"
            ) from exc


__all__ = ["DraftStudySnapshotError", "DraftStudyNetworkBuilder"]
