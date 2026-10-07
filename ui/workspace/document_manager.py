# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/workspace/document_manager.py
#
# Purpose:
#     Manages the lifecycle of open application documents.
#
# Architectural Role:
#     Central document registry for the workspace.
#
# Responsibilities:
#     - register documents;
#     - unregister documents;
#     - retrieve documents;
#     - activate documents;
#     - enumerate open documents.
#
# Does NOT:
#     - create canvas widgets;
#     - perform rendering;
#     - perform electrical analysis.
#
# ============================================================

"""
GridForge V2 — Document Manager.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional

from .document import Document


class DocumentManager:
    """
    Registry and lifecycle manager for workspace documents.
    """

    def __init__(self) -> None:
        self._documents: Dict[
            str,
            Document,
        ] = {}

        self._active_document_id: Optional[str] = None
        # Canonical runtime persistence-dirty authority for open documents.
        self._dirty_document_ids: set[str] = set()

    @property
    def active_document_id(self) -> Optional[str]:
        return self._active_document_id

    @property
    def active_document(self) -> Optional[Document]:
        if self._active_document_id is None:
            return None

        return self._documents.get(
            self._active_document_id
        )

    def register(
        self,
        document: Document,
    ) -> None:
        if document.document_id in self._documents:
            raise ValueError(
                f"Document already registered: "
                f"{document.document_id}"
            )

        self._documents[document.document_id] = document
        setter = getattr(document, "_set_dirty_callback", None)
        if callable(setter):
            setter(self._on_document_dirty_changed)
        if bool(getattr(document, "modified", False)):
            self._dirty_document_ids.add(document.document_id)

        if self._active_document_id is None:
            self.activate(
                document.document_id
            )

    def unregister(
        self,
        document_id: str,
    ) -> Document:
        document = self._documents.pop(document_id, None)

        if document is None:
            raise KeyError(document_id)
        self._dirty_document_ids.discard(document_id)
        setter = getattr(document, "_set_dirty_callback", None)
        if callable(setter):
            setter(None)

        if (
            self._active_document_id
            == document_id
        ):
            self._active_document_id = None

            if self._documents:
                self._active_document_id = next(
                    iter(self._documents)
                )

        return document

    def replace(self, document: Document) -> Document:
        """Replace one registered document without changing registry authority."""
        if not isinstance(document, Document):
            raise TypeError("document must be a Document.")
        if document.document_id not in self._documents:
            raise KeyError(document.document_id)
        was_active = self._active_document_id == document.document_id
        self.unregister(document.document_id)
        self._documents[document.document_id] = document
        setter = getattr(document, "_set_dirty_callback", None)
        if callable(setter):
            setter(self._on_document_dirty_changed)
        if bool(getattr(document, "modified", False)):
            self._dirty_document_ids.add(document.document_id)
        if was_active:
            self._active_document_id = document.document_id
        return document

    def move(self, document_id: str, index: int) -> None:
        """Reorder document presentation without changing document identity."""
        if document_id not in self._documents:
            raise KeyError(document_id)
        ordered = list(self._documents.items())
        item = next((pair for pair in ordered if pair[0] == document_id), None)
        if item is None:
            raise KeyError(document_id)
        ordered.remove(item)
        if not isinstance(index, int) or isinstance(index, bool):
            raise TypeError("index must be an integer.")
        ordered.insert(max(0, min(index, len(ordered))), item)
        self._documents = dict(ordered)

    def mark_dirty(self, document_id: str | None = None) -> None:
        target = document_id or self._active_document_id
        if target is None:
            return
        self.require(target)
        self._dirty_document_ids.add(target)

    def mark_clean(self, document_id: str | None = None) -> None:
        target = document_id or self._active_document_id
        if target is None:
            return
        self.require(target)
        self._dirty_document_ids.discard(target)

    def is_dirty(self, document_id: str | None = None) -> bool:
        target = document_id or self._active_document_id
        return target in self._dirty_document_ids if target is not None else False

    @property
    def dirty_document_ids(self) -> tuple[str, ...]:
        return tuple(document_id for document_id in self._documents if document_id in self._dirty_document_ids)

    def _on_document_dirty_changed(self, document_id: str, dirty: bool) -> None:
        if document_id not in self._documents:
            return
        if dirty:
            self._dirty_document_ids.add(document_id)
        else:
            self._dirty_document_ids.discard(document_id)

    def get(
        self,
        document_id: str,
    ) -> Optional[Document]:
        return self._documents.get(
            document_id
        )

    def require(
        self,
        document_id: str,
    ) -> Document:
        document = self.get(document_id)

        if document is None:
            raise KeyError(document_id)

        return document

    def activate(
        self,
        document_id: str,
    ) -> Document:
        document = self.require(
            document_id
        )

        self._active_document_id = document_id

        return document

    def documents(
        self,
    ) -> Iterable[Document]:
        return tuple(
            self._documents.values()
        )

    def clear(self) -> None:
        for document in tuple(self._documents.values()):
            setter = getattr(document, "_set_dirty_callback", None)
            if callable(setter):
                setter(None)
        self._documents.clear()
        self._dirty_document_ids.clear()
        self._active_document_id = None

    def __len__(self) -> int:
        return len(self._documents)
