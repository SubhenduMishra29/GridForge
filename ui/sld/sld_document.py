"""
GridForge V2 — SLD Document.

An SLDDocument owns one logical Single Line Diagram document and its
associated model.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from .sld_model import SLDModel


class SLDDocument:
    """
    Logical SLD document.

    The document provides identity and lifecycle around an ``SLDModel``.
    """

    def __init__(
        self,
        document_id: str,
        name: str = "Untitled SLD",
        model: Optional[SLDModel] = None,
    ) -> None:
        if not document_id:
            raise ValueError("document_id must not be empty")

        if not name:
            raise ValueError("name must not be empty")

        self._document_id = str(document_id)
        self._name = str(name)
        self._model = model if model is not None else SLDModel()
        self._modified = False

    @property
    def document_id(self) -> str:
        return self._document_id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not value:
            raise ValueError("name must not be empty")

        if value != self._name:
            self._name = str(value)
            self.mark_modified()

    @property
    def model(self) -> SLDModel:
        return self._model

    @property
    def modified(self) -> bool:
        return self._modified

    def mark_modified(self) -> None:
        self._modified = True

    def mark_clean(self) -> None:
        self._modified = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "name": self.name,
            "modified": self.modified,
            "model": self.model.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SLDDocument":
        document = cls(
            document_id=str(data["document_id"]),
            name=str(data.get("name", "Untitled SLD")),
            model=SLDModel.from_dict(data.get("model", {})),
        )

        if bool(data.get("modified", False)):
            document.mark_modified()

        return document

    def clear(self) -> None:
        self._model.clear()
        self.mark_modified()

    def __repr__(self) -> str:
        return (
            f"SLDDocument("
            f"document_id={self.document_id!r}, "
            f"name={self.name!r}, "
            f"nodes={self.model.node_count}, "
            f"connections={self.model.connection_count}, "
            f"modified={self.modified!r})"
        )
