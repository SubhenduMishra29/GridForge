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
import math
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
    def canvas_viewport_transform(self) -> tuple[float, float, float, float, float, float] | None:
        """Return the persisted pan/zoom transform for this SLD document."""
        value = self.metadata.get("canvas_viewport_transform")
        if value is None:
            return None
        if not isinstance(value, (tuple, list)) or len(value) != 6:
            raise ValueError("SLD canvas_viewport_transform must contain six numeric matrix values.")
        if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value):
            raise TypeError("SLD canvas viewport transform values must be numeric.")
        normalized = tuple(float(item) for item in value)
        if any(not math.isfinite(item) for item in normalized):
            raise ValueError("SLD canvas viewport transform values must be finite.")
        m11, m12, m21, m22, _dx, _dy = normalized
        if (
            m11 <= 0.0
            or m22 <= 0.0
            or not math.isclose(m11, m22, rel_tol=1e-7, abs_tol=1e-7)
            or not math.isclose(m12, 0.0, abs_tol=1e-7)
            or not math.isclose(m21, 0.0, abs_tol=1e-7)
        ):
            raise ValueError("SLD canvas viewport transform violates the positive uniform-scale navigation contract.")
        return normalized

    def set_canvas_viewport_transform(
        self,
        transform: tuple[float, float, float, float, float, float] | list[float],
    ) -> None:
        """Persist the UI-only pan/zoom matrix in this SLD document's metadata."""
        if not isinstance(transform, (tuple, list)) or len(transform) != 6:
            raise ValueError("Canvas viewport transform must contain six matrix values.")
        if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in transform):
            raise TypeError("Canvas viewport transform values must be numeric.")
        normalized = tuple(float(item) for item in transform)
        if any(not math.isfinite(item) for item in normalized):
            raise ValueError("Canvas viewport transform values must be finite.")
        m11, m12, m21, m22, _dx, _dy = normalized
        if (
            m11 <= 0.0
            or m22 <= 0.0
            or not math.isclose(m11, m22, rel_tol=1e-7, abs_tol=1e-7)
            or not math.isclose(m12, 0.0, abs_tol=1e-7)
            or not math.isclose(m21, 0.0, abs_tol=1e-7)
        ):
            raise ValueError("Canvas viewport transform violates the positive uniform-scale navigation contract.")
        previous = self.canvas_viewport_transform
        if previous is not None and all(
            math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-9)
            for left, right in zip(previous, normalized)
        ):
            return
        self.metadata["canvas_viewport_transform"] = list(normalized)
        self.mark_modified()

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

    def replace_annotation_blocks(
        self,
        blocks: list[SLDAnnotationBlock | Mapping[str, Any]],
        *,
        mark_modified: bool = True,
    ) -> tuple[SLDAnnotationBlock, ...]:
        """Atomically replace the full annotation configuration after validation."""
        if not isinstance(blocks, list):
            raise TypeError("annotation blocks must be supplied as a list")
        normalized = [
            block if isinstance(block, SLDAnnotationBlock) else SLDAnnotationBlock.from_dict(block)
            for block in blocks
        ]
        identifiers = [block.block_id for block in normalized]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("SLD annotation block IDs must be unique")
        for block in normalized:
            if self._model.get_node_optional(block.node_id) is None:
                raise ValueError("Annotation block references unknown SLD node: " + block.node_id)
        self._annotation_blocks = normalized
        if mark_modified:
            self.mark_modified()
        return tuple(self._annotation_blocks)

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
