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

from collections.abc import Callable
from typing import Any, Dict, Mapping, Optional

from ui.workspace.document import Document
from core.persistence.project_package import SLD_SCHEMA_VERSION
from core.persistence.migration import validate_canonical_sld

from .sld_model import SLDAnnotationBlock, SLDModel
from ui.equipment.symbol.symbol_base import SymbolBase


class SLDDocument(Document):
    """Logical SLD document belonging to a Workspace Project.

    SLD_SCHEMA versions the persisted SLD representation independently from
    the enclosing GridForge project schema.
    """

    DOCUMENT_TYPE = "sld"
    SLD_SCHEMA = SLD_SCHEMA_VERSION

    def __init__(
        self,
        document_id: str,
        name: str = "Untitled SLD",
        model: Optional[SLDModel] = None,
        *,
        project_id: str | None = None,
        metadata: Optional[Dict[str, Any]] = None,
        default_symbol_presentation_factory: Callable[[str], Mapping[str, Any]] | None = None,
        annotation_blocks: list[SLDAnnotationBlock | Mapping[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            document_id=document_id,
            document_type=self.DOCUMENT_TYPE,
            name=name,
            project_id=project_id,
            metadata=metadata,
        )
        self._model = model if model is not None else SLDModel()
        self._default_symbol_presentation_factory = default_symbol_presentation_factory
        self._annotation_blocks: list[SLDAnnotationBlock] = []
        for block in annotation_blocks or ():
            self.add_annotation_block(block, mark_modified=False)

    @property
    def model(self) -> SLDModel:
        """Return the presentation-owned SLD structural model."""
        return self._model

    @property
    def default_symbol_presentation_factory(self) -> Callable[[str], Mapping[str, Any]] | None:
        """Return the presentation-layer default symbol factory."""
        return self._default_symbol_presentation_factory


    @property
    def annotation_blocks(self) -> tuple[SLDAnnotationBlock, ...]:
        """Return a stable snapshot of configured presentation data blocks."""
        return tuple(self._annotation_blocks)

    def add_annotation_block(
        self,
        block: SLDAnnotationBlock | Mapping[str, Any],
        *,
        mark_modified: bool = True,
    ) -> SLDAnnotationBlock:
        """Add a data block without copying or becoming authoritative for electrical values."""
        normalized = block if isinstance(block, SLDAnnotationBlock) else SLDAnnotationBlock.from_dict(block)
        if any(existing.block_id == normalized.block_id for existing in self._annotation_blocks):
            raise ValueError("Duplicate SLD annotation block ID: " + normalized.block_id)
        if self._model.get_node_optional(normalized.node_id) is None:
            raise ValueError("Annotation block references unknown SLD node: " + normalized.node_id)
        self._annotation_blocks.append(normalized)
        if mark_modified:
            self.mark_modified()
        return normalized

    def remove_annotation_block(self, block_id: str) -> SLDAnnotationBlock:
        """Remove a configured presentation data block."""
        for index, block in enumerate(self._annotation_blocks):
            if block.block_id == block_id:
                removed = self._annotation_blocks.pop(index)
                self.mark_modified()
                return removed
        raise KeyError("Unknown SLD annotation block: " + str(block_id))

    def materialize_missing_symbol_presentations(self) -> None:
        """Materialize defaults only for nodes that have no authored presentation state."""
        factory = self._default_symbol_presentation_factory
        if factory is None:
            return
        for node in self._model.nodes:
            if node.presentation is not None:
                continue
            element_type = node.properties.get("element_type")
            identifier = (
                element_type
                if isinstance(element_type, str) and element_type.strip()
                else node.equipment_id
            )
            if not isinstance(identifier, str) or not identifier.strip():
                continue
            node.presentation = SymbolBase.from_dict(factory(identifier))

    def set_node_position(self, node_id: str, x: float, y: float) -> None:
        """Persist graphical position in the SLD document model."""
        self._model.get_node(node_id).set_position(x, y)
        self.mark_modified()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the SLD document and its structural model."""
        return {
            "schema": self.SLD_SCHEMA,
            "document_id": self.document_id,
            "project_id": self.project_id,
            "document_type": self.document_type,
            "name": self.name,
            "metadata": dict(self.metadata),
            "model": self.model.to_dict(),
            "annotation_blocks": [block.to_dict() for block in self._annotation_blocks],
        }

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
        *,
        default_symbol_presentation_factory: Callable[[str], Mapping[str, Any]] | None = None,
    ) -> "SLDDocument":
        """Restore an SLD document and materialize missing symbol presentation defaults."""
        if not isinstance(data, Mapping):
            raise TypeError("SLD document payload must be a mapping.")
        validate_canonical_sld(data)
        document = cls(
            document_id=data["document_id"],
            name=data["name"],
            project_id=data["project_id"],
            metadata=dict(data["metadata"]),
            model=SLDModel.from_dict(data["model"]),
            default_symbol_presentation_factory=default_symbol_presentation_factory,
            annotation_blocks=data["annotation_blocks"],
        )
        # Persisted presentation is authored state. Defaults may only be
        # materialized where presentation is explicitly absent.
        document.materialize_missing_symbol_presentations()
        return document

    def clear(self) -> None:
        """Clear presentation structure without touching Core."""
        self._model.clear()
        self._annotation_blocks.clear()
        self.mark_modified()

    def __repr__(self) -> str:
        return (
            f"SLDDocument(document_id={self.document_id!r}, "
            f"name={self.name!r}, nodes={self.model.node_count}, "
            f"connections={self.model.connection_count}, annotation_blocks={len(self._annotation_blocks)}, "
            f"modified={self.modified!r})"
        )


__all__ = ["SLDDocument"]
