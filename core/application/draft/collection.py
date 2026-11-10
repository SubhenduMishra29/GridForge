"""Document-scoped collection for transient SLD authoring networks.

Draft data remains separate from the committed Core Network.  The collection
provides deterministic project serialization and a migration path for the
legacy single-network representation.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from .network import DraftNetwork


class DraftNetworkCollection:
    """Own one DraftNetwork per persistent SLD document identity."""

    SCHEMA = 1

    def __init__(self, project_id: str, activation_generation: int) -> None:
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("DraftNetworkCollection requires a project_id.")
        if isinstance(activation_generation, bool) or not isinstance(activation_generation, int) or activation_generation < 1:
            raise ValueError("DraftNetworkCollection requires a positive activation_generation.")
        self.project_id = project_id.strip()
        self.activation_generation = activation_generation
        self._networks: dict[str, DraftNetwork] = {}

    @property
    def document_ids(self) -> tuple[str, ...]:
        return tuple(self._networks)

    def get(self, document_id: str, *, create: bool = False) -> DraftNetwork | None:
        key = self._document_id(document_id)
        network = self._networks.get(key)
        if network is None and create:
            network = DraftNetwork.empty(self.project_id, self.activation_generation)
            self._networks[key] = network
        return network

    def require(self, document_id: str) -> DraftNetwork:
        network = self.get(document_id)
        if network is None:
            raise KeyError(f"No DraftNetwork is registered for SLD document {document_id!r}.")
        return network

    def set(self, document_id: str, network: DraftNetwork | None) -> None:
        key = self._document_id(document_id)
        if network is None:
            self._networks.pop(key, None)
            return
        if not isinstance(network, DraftNetwork):
            raise TypeError("network must be a DraftNetwork or None.")
        if network.project_id != self.project_id:
            raise ValueError("DraftNetwork project_id does not match its collection.")
        if network.activation_generation != self.activation_generation:
            raise ValueError("DraftNetwork activation_generation does not match its collection.")
        self._networks[key] = DraftNetwork.from_dict(
            network.to_dict(),
            project_id=self.project_id,
            activation_generation=self.activation_generation,
        )

    def ensure_documents(self, document_ids) -> None:
        expected = tuple(self._document_id(value) for value in document_ids)
        if len(set(expected)) != len(expected):
            raise ValueError("SLD document identities must be unique.")
        unknown = set(self._networks) - set(expected)
        if unknown:
            raise ValueError(
                "DraftNetworkCollection contains drafts for unknown SLD documents: "
                + ", ".join(sorted(unknown))
            )
        for document_id in expected:
            self.get(document_id, create=True)

    def remove_document(self, document_id: str) -> None:
        """Remove a document draft only as part of an explicit document lifecycle operation."""
        self._networks.pop(self._document_id(document_id), None)

    def snapshot(self) -> dict[str, DraftNetwork]:
        return {
            document_id: DraftNetwork.from_dict(
                network.to_dict(),
                project_id=self.project_id,
                activation_generation=self.activation_generation,
            )
            for document_id, network in self._networks.items()
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.SCHEMA,
            "project_id": self.project_id,
            "activation_generation": self.activation_generation,
            "documents": [
                {"document_id": document_id, "draft_network": self._networks[document_id].to_dict()}
                for document_id in sorted(self._networks)
            ],
        }

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any] | None,
        *,
        project_id: str,
        activation_generation: int,
        document_ids=None,
        legacy_document_id: str | None = None,
    ) -> "DraftNetworkCollection":
        collection = cls(project_id, activation_generation)
        if data is None:
            if document_ids is not None:
                collection.ensure_documents(document_ids)
            return collection
        if not isinstance(data, Mapping):
            raise TypeError("DraftNetworkCollection payload must be a mapping.")
        if "documents" not in data:
            # Legacy project.json stored one project-scoped DraftNetwork. It is
            # assigned only when there is exactly one SLD document; ambiguous
            # multi-document migration is rejected instead of leaking draft
            # objects into an arbitrary canvas.
            target = legacy_document_id
            if target is None:
                ids = tuple(document_ids or ())
                if len(ids) == 1:
                    target = ids[0]
            if target is None and (data.get("equipment") or data.get("connections")):
                raise ValueError(
                    "Legacy project DraftNetwork cannot be assigned safely: "
                    "provide the owning legacy_document_id when document ownership is ambiguous."
                )
            if target is not None:
                collection.set(
                    target,
                    DraftNetwork.from_dict(
                        data,
                        project_id=project_id,
                        activation_generation=activation_generation,
                    ),
                )
            if document_ids is not None:
                if document_ids is not None:
                collection.ensure_documents(document_ids)
            return collection
        if data.get("schema") != cls.SCHEMA:
            raise ValueError(f"Unsupported DraftNetworkCollection schema: {data.get('schema')!r}.")
        if data.get("project_id") != project_id:
            raise ValueError("DraftNetworkCollection project_id does not match project metadata.")
        entries = data.get("documents")
        if not isinstance(entries, list):
            raise ValueError("DraftNetworkCollection documents must be an array.")
        seen: set[str] = set()
        for entry in entries:
            if not isinstance(entry, Mapping):
                raise ValueError("DraftNetworkCollection entries must be objects.")
            document_id = cls._document_id(entry.get("document_id"))
            if document_id in seen:
                raise ValueError(f"Duplicate DraftNetwork document_id: {document_id!r}.")
            seen.add(document_id)
            network_data = entry.get("draft_network")
            if not isinstance(network_data, Mapping):
                raise ValueError(f"DraftNetwork payload missing for document {document_id!r}.")
            collection.set(
                document_id,
                DraftNetwork.from_dict(
                    deepcopy(network_data),
                    project_id=project_id,
                    activation_generation=activation_generation,
                ),
            )
        if document_ids is not None:
            collection.ensure_documents(document_ids)
        return collection

    @staticmethod
    def _document_id(value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("A persistent non-empty SLD document_id is required.")
        return value.strip()


__all__ = ["DraftNetworkCollection"]
