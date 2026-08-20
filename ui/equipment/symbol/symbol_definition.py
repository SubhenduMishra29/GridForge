# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/equipment/symbol/symbol_definition.py
#
# Purpose:
#     Defines the static structure of an SLD symbol.
#
# Architectural Role:
#     SymbolDefinition describes the presentation contract that
#     a renderer consumes.
#
# It intentionally does not contain Qt painting code.
#
# Responsibilities:
#     - identify symbol type;
#     - define nominal dimensions;
#     - define terminal anchor positions;
#     - define visual primitives;
#     - provide renderer metadata.
#
# Does NOT:
#     - draw the symbol;
#     - create QPainter/QGraphicsItem;
#     - perform hit testing;
#     - own canvas coordinates.
#
# ============================================================

"""
GridForge V2 — Symbol Definition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class SymbolDefinition:
    """
    Static symbol description.

    ``primitives`` is renderer-neutral metadata. A later renderer can
    interpret these primitives using Qt, SVG, OpenGL or another backend
    without changing the symbol definition.
    """

    definition_id: str

    display_name: str

    width: float = 40.0

    height: float = 40.0

    terminal_anchors: Dict[
        str,
        Tuple[float, float],
    ] = field(default_factory=dict)

    primitives: Tuple[
        Dict[str, Any],
        ...,
    ] = ()

    renderer_id: str = "default"

    def __post_init__(self) -> None:
        if not self.definition_id:
            raise ValueError(
                "definition_id must not be empty"
            )

        if not self.display_name:
            raise ValueError(
                "display_name must not be empty"
            )

        if self.width <= 0.0:
            raise ValueError(
                "width must be greater than zero"
            )

        if self.height <= 0.0:
            raise ValueError(
                "height must be greater than zero"
            )

        object.__setattr__(
            self,
            "terminal_anchors",
            dict(self.terminal_anchors),
        )

        object.__setattr__(
            self,
            "primitives",
            tuple(
                dict(primitive)
                for primitive in self.primitives
            ),
        )

    def anchor(
        self,
        terminal_name: str,
    ) -> Tuple[float, float]:
        """
        Return the symbol-local anchor position of a terminal.
        """
        try:
            return self.terminal_anchors[
                terminal_name
            ]
        except KeyError as exc:
            raise KeyError(
                f"Unknown terminal anchor: "
                f"{terminal_name}"
            ) from exc

    def to_dict(self) -> Dict[str, Any]:
        return {
            "definition_id": self.definition_id,
            "display_name": self.display_name,
            "width": self.width,
            "height": self.height,
            "terminal_anchors": {
                name: list(position)
                for name, position
                in self.terminal_anchors.items()
            },
            "primitives": [
                dict(primitive)
                for primitive in self.primitives
            ],
            "renderer_id": self.renderer_id,
        }
