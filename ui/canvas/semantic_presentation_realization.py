# ============================================================
# File: ui/canvas/semantic_presentation_realization.py
# GridForge V2 — Semantic Presentation Realization
# Author: Subhendu Mishra
# ============================================================

"""Select renderer-neutral presentation representations for SLD nodes."""

from __future__ import annotations

from dataclasses import dataclass

from ui.sld.sld_vocabulary import semantic_type

from .sld_canvas_projection import SLDCanvasNode


@dataclass(frozen=True)
class PresentationSelection:
    """Immutable identity of a presentation representation."""

    representation_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.representation_id, str):
            raise TypeError("representation_id must be a string.")
        if not self.representation_id.strip():
            raise ValueError("representation_id must not be empty.")


class SemanticPresentationRealization:
    """Resolve supported SLD semantic types to renderer-neutral selections."""

    def realize(self, node: SLDCanvasNode) -> PresentationSelection:
        if not isinstance(node, SLDCanvasNode):
            raise TypeError("node must be an SLDCanvasNode.")
        element_type = node.properties.get("element_type")
        if not isinstance(element_type, str) or not element_type.strip():
            raise ValueError("SLDCanvasNode must provide a non-empty element_type.")
        semantic_type(element_type)
        if element_type.strip().upper() in {"BUS", "BUSES"}:
            return PresentationSelection(representation_id="bus")
        return PresentationSelection(representation_id="equipment")


__all__ = ["PresentationSelection", "SemanticPresentationRealization"]
