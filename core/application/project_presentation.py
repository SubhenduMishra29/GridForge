# ============================================================
# GridForge V2 — Project Presentation Collection
# ============================================================
"""Application-boundary candidate for the complete persisted presentation collection.

This is an activation/persistence DTO, not a second runtime document authority.
The canonical open-document registry remains ui.workspace.DocumentManager.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class ProjectPresentationCollection:
    """Ordered project presentation documents plus the persisted active identity."""

    documents: tuple[Any, ...]
    active_document_id: str | None

    def __post_init__(self) -> None:
        documents = tuple(self.documents)
        ids: list[str] = []
        for document in documents:
            document_id = getattr(document, "document_id", None)
            if not isinstance(document_id, str) or not document_id.strip():
                raise ValueError("Every presentation document must have a stable document_id.")
            if document_id in ids:
                raise ValueError(f"Duplicate presentation document_id: {document_id}")
            ids.append(document_id)
        active = self.active_document_id
        if active is not None and active not in ids:
            active = ids[0] if ids else None
        object.__setattr__(self, "documents", documents)
        object.__setattr__(self, "active_document_id", active)

    @property
    def active_document(self) -> Any | None:
        if self.active_document_id is None:
            return None
        return next(
            (document for document in self.documents if document.document_id == self.active_document_id),
            None,
        )

    @classmethod
    def single(cls, document: Any) -> "ProjectPresentationCollection":
        return cls((document,), getattr(document, "document_id", None))

    @classmethod
    def ordered(cls, documents: Iterable[Any], active_document_id: str | None) -> "ProjectPresentationCollection":
        return cls(tuple(documents), active_document_id)


__all__ = ["ProjectPresentationCollection"]
