# ============================================================
# GridForge V2
# ============================================================
# File:
#     ui/equipment/equipment_definition.py
#
# Purpose:
#     Immutable-style metadata describing an equipment type.
#
# Architectural Role:
#     Separates equipment TYPE metadata from an individual
#     equipment INSTANCE.
#
# Does NOT:
#     - create graphics;
#     - create equipment instances;
#     - calculate electrical parameters;
#     - validate network topology.
#
# ============================================================

"""
GridForge V2 — Equipment Definition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class EquipmentDefinition:
    """
    Static definition of an SLD equipment type.

    Definitions belong to the equipment registry/factory layer.
    They are not individual equipment instances.

    ``default_properties`` is defensively copied during
    construction and when returned to callers.
    """

    equipment_type: str

    display_name: str

    terminal_names: tuple[str, ...] = ()

    symbol_id: str = ""

    default_properties: dict[str, Any] = field(
        default_factory=dict
    )

    category: str = "electrical"

    # ========================================================
    # VALIDATION
    # ========================================================

    def __post_init__(self) -> None:
        """
        Validate and normalize definition metadata.
        """

        equipment_type = self._validate_text(
            self.equipment_type,
            "equipment_type",
        )

        display_name = self._validate_text(
            self.display_name,
            "display_name",
        )

        category = self._validate_text(
            self.category,
            "category",
        )

        symbol_id = self.symbol_id

        if symbol_id:
            symbol_id = self._validate_text(
                symbol_id,
                "symbol_id",
            )
        else:
            symbol_id = equipment_type

        if isinstance(
            self.terminal_names,
            (str, bytes),
        ):
            raise TypeError(
                "terminal_names must be an iterable of strings"
            )

        normalized_terminal_names: list[str] = []

        try:
            terminal_names = tuple(
                self.terminal_names
            )
        except TypeError as exc:
            raise TypeError(
                "terminal_names must be an iterable"
            ) from exc

        for terminal_name in terminal_names:
            normalized_name = self._validate_text(
                terminal_name,
                "terminal_name",
            )

            if normalized_name in normalized_terminal_names:
                raise ValueError(
                    "Duplicate terminal name: "
                    f"{normalized_name}"
                )

            normalized_terminal_names.append(
                normalized_name
            )

        if not isinstance(
            self.default_properties,
            Mapping,
        ):
            raise TypeError(
                "default_properties must be a mapping"
            )

        object.__setattr__(
            self,
            "equipment_type",
            equipment_type,
        )

        object.__setattr__(
            self,
            "display_name",
            display_name,
        )

        object.__setattr__(
            self,
            "terminal_names",
            tuple(normalized_terminal_names),
        )

        object.__setattr__(
            self,
            "symbol_id",
            symbol_id,
        )

        object.__setattr__(
            self,
            "default_properties",
            dict(self.default_properties),
        )

        object.__setattr__(
            self,
            "category",
            category,
        )

    # --------------------------------------------------------

    @staticmethod
    def _validate_text(
        value: str,
        field_name: str,
    ) -> str:
        """
        Validate a required textual field.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string"
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"{field_name} must not be empty"
            )

        return value

    # ========================================================
    # TERMINALS
    # ========================================================

    @property
    def terminal_count(self) -> int:
        """
        Return the number of logical terminals defined.
        """

        return len(
            self.terminal_names
        )

    # --------------------------------------------------------

    def has_terminal(
        self,
        terminal_name: str,
    ) -> bool:
        """
        Return whether a terminal name is defined.
        """

        if not isinstance(
            terminal_name,
            str,
        ):
            raise TypeError(
                "terminal_name must be a string"
            )

        return terminal_name in self.terminal_names

    # ========================================================
    # DEFAULT PROPERTIES
    # ========================================================

    def create_default_properties(
        self,
    ) -> dict[str, Any]:
        """
        Return a fresh default-property dictionary.

        Each equipment instance receives an independent copy.
        """

        return dict(
            self.default_properties
        )

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the equipment definition.
        """

        return {
            "equipment_type": self.equipment_type,
            "display_name": self.display_name,
            "terminal_names": list(
                self.terminal_names
            ),
            "symbol_id": self.symbol_id,
            "default_properties": dict(
                self.default_properties
            ),
            "category": self.category,
        }

    # --------------------------------------------------------

    @classmethod
    def from_dict(
        cls,
        data: Mapping[str, Any],
    ) -> "EquipmentDefinition":
        """
        Reconstruct a definition from serialized metadata.
        """

        if not isinstance(
            data,
            Mapping,
        ):
            raise TypeError(
                "data must be a mapping"
            )

        if "equipment_type" not in data:
            raise KeyError(
                "equipment_type"
            )

        if "display_name" not in data:
            raise KeyError(
                "display_name"
            )

        default_properties = data.get(
            "default_properties",
            {},
        )

        if not isinstance(
            default_properties,
            Mapping,
        ):
            raise TypeError(
                "default_properties must be a mapping"
            )

        return cls(
            equipment_type=data[
                "equipment_type"
            ],
            display_name=data[
                "display_name"
            ],
            terminal_names=tuple(
                data.get(
                    "terminal_names",
                    (),
                )
            ),
            symbol_id=data.get(
                "symbol_id",
                "",
            ),
            default_properties=dict(
                default_properties
            ),
            category=data.get(
                "category",
                "electrical",
            ),
        )


__all__ = [
    "EquipmentDefinition",
]
