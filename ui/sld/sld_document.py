# ============================================================
# GridForge V2
# ============================================================
# File: ui/sld/sld_document.py
# Purpose: SLD document lifecycle and structural model ownership.
# Author: Subhendu Mishra
# ============================================================
"""Presentation-owned SLD document.

SLDDocument owns editable SLD document structure, including persistent
presentation geometry. It never owns authoritative electrical truth.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from ui.workspace.document import Document

from .sld_model import SLDModel


class SLDDocument(Document):
    """Logical SLD document belonging to a Workspace Project."""

    DOCUMENT_TYPE = "sld"

    def __init__(
        self,
        document_id: str,
        name: str = "Untitled SLD",
        model: Optional[SLDModel] = None,
        *,
        project_id: str | None = None,
    ) -> None:
        super().__init__(
            document_id=document_id,
            document_type=self.DOCUMENT_TYPE,
            name=name,
            project_id=project_id,
        )
        self._model = model if model is not None else SLDModel()

    @property
    def model(self) -> SLDModel:
        """Return the presentation-owned SLD structural model."""
        return self._model

    def set_node_position(self, node_id: str, x: float, y: float) -> None:
        """Persist graphical position in the SLD document model."""
        self._model.get_node(node_id).set_position(x, y)
        self.mark_modified()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the SLD document and its structural model."""
        return {
            "document_id": self.document_id,
            "project_id": self.project_id,
            "document_type": self.document_type,
            "name": self.name,
            "modified": self.modified,
            "model": self.model.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "SLDDocument":
        """Restore an SLD document from presentation data."""
        document = cls(
            document_id=str(data["document_id"]),
            name=str(data.get("name", "Untitled SLD")),
            project_id=data.get("project_id"),
            model=SLDModel.from_dict(data.get("model", {})),
        )
        if bool(data.get("modified", False)):
            document.mark_modified()
        return document

    def clear(self) -> None:
        """Clear presentation structure without touching Core."""
        self._model.clear()
        self.mark_modified()

    def __repr__(self) -> str:
        return (
            f"SLDDocument(document_id={self.document_id!r}, "
            f"name={self.name!r}, nodes={self.model.node_count}, "
            f"connections={self.model.connection_count}, "
            f"modified={self.modified!r})"
        )


__all__ = ["SLDDocument"]
