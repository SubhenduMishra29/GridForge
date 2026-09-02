# ============================================================
# GridForge V2
# ============================================================
# File: ui/workspace/document.py
# Purpose: UI workspace document descriptor.
# Author: Subhendu Mishra
# ============================================================
"""Generic Presentation/workspace document boundary.

A Document belongs to a Project but is not the Core engineering model.
It contains document identity, type, metadata and editable state only.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class Document:
    """Generic Presentation/workspace document descriptor."""

    def __init__(
        self,
        document_id: str,
        document_type: str,
        name: str = "Untitled",
        *,
        project_id: str | None = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not document_id:
            raise ValueError("document_id must not be empty")
        if not document_type:
            raise ValueError("document_type must not be empty")
        if not name:
            raise ValueError("name must not be empty")
        if project_id is not None and not str(project_id).strip():
            raise ValueError("project_id must not be empty")

        self._document_id = str(document_id)
        self._document_type = str(document_type)
        self._name = str(name)
        self._project_id = str(project_id) if project_id is not None else None
        self._metadata = dict(metadata or {})
        self._modified = False

    @property
    def document_id(self) -> str:
        return self._document_id

    @property
    def project_id(self) -> str | None:
        return self._project_id

    @property
    def document_type(self) -> str:
        return self._document_type

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
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    @property
    def modified(self) -> bool:
        return self._modified

    def mark_modified(self) -> None:
        self._modified = True

    def mark_clean(self) -> None:
        self._modified = False

    def get_metadata(self, key: str, default: Any = None) -> Any:
        return self._metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        if not key:
            raise ValueError("metadata key must not be empty")
        self._metadata[key] = value
        self.mark_modified()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "project_id": self.project_id,
            "document_type": self.document_type,
            "name": self.name,
            "metadata": dict(self.metadata),
            "modified": self.modified,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        document = cls(
            document_id=str(data["document_id"]),
            project_id=data.get("project_id"),
            document_type=str(data["document_type"]),
            name=str(data.get("name", "Untitled")),
            metadata=dict(data.get("metadata", {})),
        )
        if data.get("modified", False):
            document.mark_modified()
        return document


__all__ = ["Document"]
