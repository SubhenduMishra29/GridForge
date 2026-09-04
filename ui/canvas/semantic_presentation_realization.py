# ============================================================
# File: ui/canvas/semantic_presentation_realization.py
# GridForge V2 — Semantic Presentation Realization
# Author: Subhendu Mishra
# ============================================================

"""Select renderer-neutral presentation representations for SLD nodes.

This boundary interprets semantic information already carried by an
``SLDCanvasNode``.  It deliberately stops before concrete graphics
construction: the render system orchestrates the flow and the graphics-item
factory constructs the resulting presentation item.
"""

from __future__ import annotations

from dataclasses import dataclass

from .sld_canvas_projection import SLDCanvasNode


@dataclass(frozen=True)
class PresentationSelection:
    """Immutable identity of a presentation representation.

    The value is deliberately renderer-neutral.  It carries neither semantic
    element identity nor geometry and does not reference Qt graphics objects.
    """

    representation_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.representation_id, str):
            raise TypeError("representation_id must be a string.")
        if not self.representation_id.strip():
            raise ValueError("representation_id must not be empty.")


class SemanticPresentationRealization:
    """Resolve an SLD node's semantic type to a presentation selection."""

    _PRESENTATION_BY_ELEMENT_TYPE = {
        "buses": "bus",
    }

    def realize(self, node: SLDCanvasNode) -> PresentationSelection:
        """Select the presentation representation appropriate for ``node``."""
        if not isinstance(node, SLDCanvasNode):
            raise TypeError("node must be an SLDCanvasNode.")

        element_type = node.properties.get("element_type")
        if not isinstance(element_type, str) or not element_type.strip():
            raise ValueError("SLDCanvasNode must provide a non-empty element_type.")

        representation_id = self._PRESENTATION_BY_ELEMENT_TYPE.get(element_type)
        if representation_id is None:
            raise ValueError(
                f"Unsupported SLD presentation element_type: {element_type}"
            )

        return PresentationSelection(representation_id=representation_id)


__all__ = ["PresentationSelection", "SemanticPresentationRealization"]
