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

        self._active_document_id: Optional[
            str
        ] = None

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

        self._documents[
            document.document_id
        ] = document

        if self._active_document_id is None:
            self.activate(
                document.document_id
            )

    def unregister(
        self,
        document_id: str,
    ) -> Document:
        document = self._documents.pop(
            document_id,
            None,
        )

        if document is None:
            raise KeyError(document_id)

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
        self._documents.clear()
        self._active_document_id = None

    def __len__(self) -> int:
        return len(self._documents)
