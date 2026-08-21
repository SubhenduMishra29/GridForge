# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/equipment/symbol/symbol_base.py
#
# Purpose:
#     Base logical representation of an SLD symbol instance.
#
# Architectural Role:
#     Separates a symbol's logical identity and transformation
#     state from the renderer that eventually displays it.
#
# Does NOT:
#     - perform QPainter operations;
#     - create QGraphicsItem objects;
#     - draw lines or shapes;
#     - manage the scene;
#     - perform electrical calculations.
# ============================================================

"""
GridForge V2 — Symbol Base.

Runtime logical representation of an SLD symbol instance.
"""

from __future__ import annotations

from typing import Any, Mapping


class SymbolBase:
    """
    Runtime logical SLD symbol instance.

    This object contains presentation metadata only. It is
    deliberately independent of Qt, QGraphicsScene,
    QGraphicsItem, and renderer implementations.
    """

    def __init__(
        self,
        symbol_id: str,
        definition_id: str,
        *,
        scale: float = 1.0,
        rotation: float = 0.0,
        visible: bool = True,
        properties: Mapping[str, Any] | None = None,
    ) -> None:
        # ----------------------------------------------------
        # Identity validation
        # ----------------------------------------------------

        if (
            not isinstance(symbol_id, str)
            or not symbol_id.strip()
        ):
            raise ValueError(
                "symbol_id must be a non-empty string."
            )

        if (
            not isinstance(definition_id, str)
            or not definition_id.strip()
        ):
            raise ValueError(
                "definition_id must be a non-empty string."
            )

        # ----------------------------------------------------
        # Transformation validation
        # ----------------------------------------------------

        try:
            normalized_scale = float(scale)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "scale must be a real numeric value."
            ) from exc

        if normalized_scale <= 0.0:
            raise ValueError(
                "scale must be greater than zero."
            )

        try:
            normalized_rotation = float(rotation)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "rotation must be a real numeric value."
            ) from exc

        # ----------------------------------------------------
        # Properties validation
        # ----------------------------------------------------

        if properties is not None and not isinstance(
            properties,
            Mapping,
        ):
            raise TypeError(
                "properties must be a mapping or None."
            )

        normalized_properties: dict[str, Any] = {}

        if properties is not None:
            for key, value in properties.items():

                if (
                    not isinstance(key, str)
                    or not key.strip()
                ):
                    raise ValueError(
                        "property keys must be "
                        "non-empty strings."
                    )

                normalized_properties[key] = value

        # ----------------------------------------------------
        # State
        # ----------------------------------------------------

        self._symbol_id = symbol_id
        self._definition_id = definition_id
        self._scale = normalized_scale
        self._rotation = normalized_rotation
        self._visible = bool(visible)
        self._properties = normalized_properties

    # ========================================================
    # IDENTITY
    # ========================================================

    @property
    def symbol_id(self) -> str:
        """Return the runtime symbol identity."""
        return self._symbol_id

    # --------------------------------------------------------

    @property
    def definition_id(self) -> str:
        """Return the referenced SymbolDefinition identity."""
        return self._definition_id

    # ========================================================
    # TRANSFORMATION
    # ========================================================

    @property
    def scale(self) -> float:
        """Return the symbol scale."""
        return self._scale

    @scale.setter
    def scale(
        self,
        value: float,
    ) -> None:
        try:
            normalized = float(value)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "scale must be a real numeric value."
            ) from exc

        if normalized <= 0.0:
            raise ValueError(
                "scale must be greater than zero."
            )

        self._scale = normalized

    # --------------------------------------------------------

    @property
    def rotation(self) -> float:
        """Return symbol rotation in degrees."""
        return self._rotation

    @rotation.setter
    def rotation(
        self,
        value: float,
    ) -> None:
        try:
            self._rotation = float(value)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "rotation must be a real numeric value."
            ) from exc

    # ========================================================
    # VISIBILITY
    # ========================================================

    @property
    def visible(self) -> bool:
        """Return whether the symbol is visible."""
        return self._visible

    @visible.setter
    def visible(
        self,
        value: bool,
    ) -> None:
        self._visible = bool(value)

    # ========================================================
    # PROPERTIES
    # ========================================================

    @property
    def properties(self) -> dict[str, Any]:
        """
        Return the symbol property collection.

        The dictionary is intentionally mutable because symbol
        properties are runtime instance state.
        """
        return self._properties

    # --------------------------------------------------------

    def get_property(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Return a symbol property."""

        if (
            not isinstance(key, str)
            or not key.strip()
        ):
            raise ValueError(
                "property key must be a "
                "non-empty string."
            )

        return self._properties.get(
            key,
            default,
        )

    # --------------------------------------------------------

    def set_property(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Set a symbol property."""

        if (
            not isinstance(key, str)
            or not key.strip()
        ):
            raise ValueError(
                "property key must be a "
                "non-empty string."
            )

        self._properties[key] = value

    # --------------------------------------------------------

    def remove_property(
        self,
        key: str,
    ) -> Any:
        """Remove and return a symbol property."""

        if (
            not isinstance(key, str)
            or not key.strip()
        ):
            raise ValueError(
                "property key must be a "
                "non-empty string."
            )

        return self._properties.pop(key)

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the logical symbol instance.

        The returned structure contains ordinary Python
        containers and no Qt/rendering objects.
        """

        return {
            "symbol_id": self.symbol_id,
            "definition_id": self.definition_id,
            "scale": self.scale,
            "rotation": self.rotation,
            "visible": self.visible,
            "properties": dict(
                self.properties
            ),
        }

    # --------------------------------------------------------

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> "SymbolBase":
        """
        Reconstruct a SymbolBase from serialized data.
        """

        if not isinstance(data, Mapping):
            raise TypeError(
                "data must be a mapping."
            )

        return cls(
            symbol_id=data["symbol_id"],
            definition_id=data["definition_id"],
            scale=data.get(
                "scale",
                1.0,
            ),
            rotation=data.get(
                "rotation",
                0.0,
            ),
            visible=data.get(
                "visible",
                True,
            ),
            properties=data.get(
                "properties",
                {},
            ),
        )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        return (
            "SymbolBase("
            f"symbol_id={self.symbol_id!r}, "
            f"definition_id={self.definition_id!r}, "
            f"scale={self.scale!r}, "
            f"rotation={self.rotation!r}, "
            f"visible={self.visible!r}"
            ")"
        )


__all__ = [
    "SymbolBase",
]
