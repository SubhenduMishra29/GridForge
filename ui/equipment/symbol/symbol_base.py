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
#     Separates a symbol's logical identity and geometry metadata
#     from the renderer that eventually displays it.
#
# Responsibilities:
#     - identify a symbol;
#     - reference its symbol definition;
#     - store scale/rotation;
#     - store visibility;
#     - store symbol-specific properties.
#
# Does NOT:
#     - perform QPainter operations;
#     - create QGraphicsItem objects;
#     - draw lines or shapes;
#     - manage the scene.
#
# Relationship:
#
#     Equipment
#         |
#         v
#     SymbolBase
#         |
#         v
#     Renderer
#         |
#         v
#     Canvas
#
# ============================================================

"""
GridForge V2 — Symbol Base.
"""

from __future__ import annotations

from typing import Any, Dict


class SymbolBase:
    """
    Runtime logical symbol instance.

    This is presentation metadata, not a Qt graphics object.
    """

    def __init__(
        self,
        symbol_id: str,
        definition_id: str,
        *,
        scale: float = 1.0,
        rotation: float = 0.0,
        visible: bool = True,
        properties: Dict[str, Any] | None = None,
    ) -> None:
        if not symbol_id:
            raise ValueError(
                "symbol_id must not be empty"
            )

        if not definition_id:
            raise ValueError(
                "definition_id must not be empty"
            )

        if scale <= 0.0:
            raise ValueError(
                "scale must be greater than zero"
            )

        self._symbol_id = str(symbol_id)
        self._definition_id = str(definition_id)
        self._scale = float(scale)
        self._rotation = float(rotation)
        self._visible = bool(visible)
        self._properties = dict(
            properties or {}
        )

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    @property
    def symbol_id(self) -> str:
        return self._symbol_id

    @property
    def definition_id(self) -> str:
        return self._definition_id

    # --------------------------------------------------------
    # Transformation
    # --------------------------------------------------------

    @property
    def scale(self) -> float:
        return self._scale

    @scale.setter
    def scale(self, value: float) -> None:
        if value <= 0.0:
            raise ValueError(
                "scale must be greater than zero"
            )

        self._scale = float(value)

    @property
    def rotation(self) -> float:
        return self._rotation

    @rotation.setter
    def rotation(self, value: float) -> None:
        self._rotation = float(value)

    # --------------------------------------------------------
    # Visibility
    # --------------------------------------------------------

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = bool(value)

    # --------------------------------------------------------
    # Properties
    # --------------------------------------------------------

    @property
    def properties(self) -> Dict[str, Any]:
        return self._properties

    def get_property(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        return self._properties.get(
            key,
            default,
        )

    def set_property(
        self,
        key: str,
        value: Any,
    ) -> None:
        if not key:
            raise ValueError(
                "property key must not be empty"
            )

        self._properties[key] = value

    # --------------------------------------------------------
    # Serialization
    # --------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
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
