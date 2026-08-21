# ============================================================
# File: ui/equipment/symbol/symbol_definition.py
# GridForge V2 — Symbol Definition
# ============================================================
"""
Immutable logical definition of an SLD equipment symbol.

This module contains renderer-neutral symbol metadata only.

Architecture
------------
    SymbolDefinition
          │
          ▼
    SymbolRegistry
          │
          ▼
    SymbolFactory
          │
          ▼
      SymbolBase
          │
          ▼
       Renderer

The definition contains no Qt objects, graphics items, scene
state, or rendering behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class SymbolDefinition:
    """
    Immutable renderer-neutral definition of an SLD symbol.

    Parameters
    ----------
    symbol_id:
        Stable symbol-definition identity.

    display_name:
        Human-readable symbol name.

    width:
        Logical symbol width.

    height:
        Logical symbol height.

    terminal_anchors:
        Mapping from terminal name to local symbol coordinates.

    primitives:
        Renderer-neutral primitive descriptions.

    renderer_id:
        Identifier of the renderer responsible for drawing the
        symbol.
    """

    symbol_id: str
    display_name: str
    width: float
    height: float
    terminal_anchors: Mapping[str, tuple[float, float]]
    primitives: tuple[Mapping[str, Any], ...]
    renderer_id: str = "default"

    def __post_init__(self) -> None:
        """Validate and defensively freeze nested state."""

        if (
            not isinstance(self.symbol_id, str)
            or not self.symbol_id.strip()
        ):
            raise ValueError(
                "symbol_id must be a non-empty string."
            )

        if (
            not isinstance(self.display_name, str)
            or not self.display_name.strip()
        ):
            raise ValueError(
                "display_name must be a non-empty string."
            )

        if self.width <= 0:
            raise ValueError(
                "width must be greater than zero."
            )

        if self.height <= 0:
            raise ValueError(
                "height must be greater than zero."
            )

        if (
            not isinstance(self.renderer_id, str)
            or not self.renderer_id.strip()
        ):
            raise ValueError(
                "renderer_id must be a non-empty string."
            )

        # ----------------------------------------------------
        # Terminal anchors
        # ----------------------------------------------------

        anchors: dict[str, tuple[float, float]] = {}

        for name, position in dict(
            self.terminal_anchors
        ).items():

            if (
                not isinstance(name, str)
                or not name.strip()
            ):
                raise ValueError(
                    "terminal anchor names must be "
                    "non-empty strings."
                )

            if not isinstance(position, (tuple, list)):
                raise TypeError(
                    "terminal anchor positions must be "
                    "two-element sequences."
                )

            if len(position) != 2:
                raise ValueError(
                    "terminal anchor positions must contain "
                    "exactly two values."
                )

            anchors[name] = (
                float(position[0]),
                float(position[1]),
            )

        # ----------------------------------------------------
        # Renderer-neutral primitives
        # ----------------------------------------------------

        frozen_primitives: list[Mapping[str, Any]] = []

        for primitive in self.primitives:

            if not isinstance(primitive, Mapping):
                raise TypeError(
                    "each primitive must be a mapping."
                )

            frozen_primitives.append(
                MappingProxyType(
                    dict(primitive)
                )
            )

        object.__setattr__(
            self,
            "terminal_anchors",
            MappingProxyType(anchors),
        )

        object.__setattr__(
            self,
            "primitives",
            tuple(frozen_primitives),
        )

    # ========================================================
    # TERMINALS
    # ========================================================

    def has_terminal_anchor(
        self,
        terminal_name: str,
    ) -> bool:
        """Return whether an anchor exists for a terminal."""

        return terminal_name in self.terminal_anchors

    # --------------------------------------------------------

    def get_terminal_anchor(
        self,
        terminal_name: str,
    ) -> tuple[float, float]:
        """Return the local position of a terminal anchor."""

        try:
            return self.terminal_anchors[
                terminal_name
            ]
        except KeyError as exc:
            raise KeyError(
                f"Unknown terminal anchor: "
                f"{terminal_name!r}"
            ) from exc

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to ordinary mutable Python structures.

        MappingProxyType is deliberately removed from the
        serialized representation.
        """

        return {
            "symbol_id": self.symbol_id,
            "display_name": self.display_name,
            "width": self.width,
            "height": self.height,
            "terminal_anchors": {
                name: tuple(position)
                for name, position
                in self.terminal_anchors.items()
            },
            "primitives": [
                dict(primitive)
                for primitive in self.primitives
            ],
            "renderer_id": self.renderer_id,
        }

    # --------------------------------------------------------

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> "SymbolDefinition":
        """
        Construct a SymbolDefinition from serialized data.
        """

        if not isinstance(data, Mapping):
            raise TypeError(
                "data must be a mapping."
            )

        return cls(
            symbol_id=data["symbol_id"],
            display_name=data["display_name"],
            width=float(data["width"]),
            height=float(data["height"]),
            terminal_anchors=data.get(
                "terminal_anchors",
                {},
            ),
            primitives=tuple(
                data.get(
                    "primitives",
                    (),
                )
            ),
            renderer_id=data.get(
                "renderer_id",
                "default",
            ),
        )


__all__ = [
    "SymbolDefinition",
]
