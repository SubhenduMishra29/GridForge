# ============================================================
# Author: Subhendu Mishra
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
from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from ui.creation.creation_definition import CreationDefinition

@dataclass(frozen=True, slots=True)
class EngineeringParameterDefinition:
    """Canonical engineering parameter contract for equipment creation."""
    parameter_id: str
    display_name: str
    datatype: str = "str"
    unit: str | None = None
    required_before_create: bool = False
    default_value: Any = None
    editable: bool = True
    derived: bool = False
    choices: tuple[Any, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    validation: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.parameter_id, str) or not self.parameter_id.strip():
            raise ValueError("parameter_id must be non-empty")
        if not isinstance(self.display_name, str) or not self.display_name.strip():
            raise ValueError("display_name must be non-empty")
        if not isinstance(self.datatype, str) or not self.datatype.strip():
            raise ValueError("datatype must be non-empty")
        if self.derived and self.editable:
            raise ValueError("derived parameters cannot be editable")
        object.__setattr__(self, "parameter_id", self.parameter_id.strip())
        object.__setattr__(self, "display_name", self.display_name.strip())
        object.__setattr__(self, "datatype", self.datatype.strip())
        object.__setattr__(self, "choices", tuple(self.choices))
        object.__setattr__(self, "validation", dict(self.validation))


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

    # Canonical UI tool identity for engineer activation.
    tool_id: str = ""

    terminal_names: tuple[str, ...] = ()

    symbol_id: str = ""

    default_properties: dict[str, Any] = field(
        default_factory=dict
    )

    category: str = "electrical"
    engineering_parameters: tuple[EngineeringParameterDefinition, ...] = ()
    creation_definition: CreationDefinition | None = None

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

        tool_id = self.tool_id or equipment_type
        tool_id = self._validate_text(tool_id, "tool_id")

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

        if self.creation_definition is not None and not callable(getattr(self.creation_definition, 'validate_values', None)):
            raise TypeError('creation_definition must provide validate_values().')
        if self.creation_definition is not None:
            creation_roles = tuple(
                requirement.terminal_name
                for requirement in self.creation_definition.terminal_requirements
            )
            if creation_roles != tuple(normalized_terminal_names) and not (
                self.equipment_type.strip().lower() == "bus" and not creation_roles
            ):
                raise ValueError(
                    "creation_definition terminal roles must match terminal_names exactly."
                )
        if not isinstance(self.engineering_parameters, (tuple, list)):
            raise TypeError("engineering_parameters must be a tuple/list of EngineeringParameterDefinition")
        normalized_parameters: list[EngineeringParameterDefinition] = []
        seen_parameters: set[str] = set()
        for parameter in self.engineering_parameters:
            if not isinstance(parameter, EngineeringParameterDefinition):
                raise TypeError("engineering_parameters must contain EngineeringParameterDefinition values")
            if parameter.parameter_id in seen_parameters:
                raise ValueError("Duplicate engineering parameter: " + parameter.parameter_id)
            seen_parameters.add(parameter.parameter_id)
            normalized_parameters.append(parameter)

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
            "tool_id",
            tool_id,
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

        object.__setattr__(self, "category", category)
        object.__setattr__(self, "engineering_parameters", tuple(normalized_parameters))
        if self.creation_definition is not None:
            contract_parameters = tuple(getattr(self.creation_definition, 'parameter_definitions', ()))
            if tuple(p.parameter_id for p in contract_parameters) != tuple(p.parameter_id for p in normalized_parameters):
                raise ValueError('creation_definition parameters must match engineering_parameters.')

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
    # ENGINEERING CREATION CONTRACT
    # ========================================================

    def parameter(self, parameter_id: str) -> EngineeringParameterDefinition:
        for parameter in self.engineering_parameters:
            if parameter.parameter_id == parameter_id:
                return parameter
        raise KeyError(parameter_id)

    def parameter_ids(self) -> tuple[str, ...]:
        return tuple(item.parameter_id for item in self.engineering_parameters)

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
            "tool_id": self.tool_id,
            "terminal_names": list(
                self.terminal_names
            ),
            "symbol_id": self.symbol_id,
            "default_properties": dict(
                self.default_properties
            ),
            "category": self.category,
            "creation_definition": None if self.creation_definition is None else {"equipment_type": self.creation_definition.equipment_type, "tool_id": self.creation_definition.tool_id, "id_field": self.creation_definition.id_field, "parameter_mapping": dict(self.creation_definition.parameter_mapping), "endpoint_mapping": dict(self.creation_definition.endpoint_mapping)},
            "engineering_parameters": [
                {"parameter_id": item.parameter_id, "display_name": item.display_name,
                 "datatype": item.datatype, "unit": item.unit,
                 "required_before_create": item.required_before_create,
                 "default_value": item.default_value, "editable": item.editable,
                 "derived": item.derived, "choices": list(item.choices),
                 "minimum": item.minimum, "maximum": item.maximum,
                 "validation": dict(item.validation)}
                for item in self.engineering_parameters
            ],
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

        creation_definition = None
        if data.get('creation_definition') is not None:
            from ui.creation.creation_definition import creation_definition_for
            creation_definition = creation_definition_for(data['equipment_type'], tuple(data.get('terminal_names', ())))

        return cls(
            equipment_type=data[
                "equipment_type"
            ],
            display_name=data[
                "display_name"
            ],
            tool_id=data.get(
                "tool_id",
                data["equipment_type"],
            ),
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
            category=data.get("category", "electrical"),
            engineering_parameters=tuple(EngineeringParameterDefinition(parameter_id=item['parameter_id'], display_name=item['display_name'], datatype=item.get('datatype', 'str'), unit=item.get('unit'), required_before_create=item.get('required_before_create', False), default_value=item.get('default_value'), editable=item.get('editable', True), derived=item.get('derived', False), choices=tuple(item.get('choices', ())), minimum=item.get('minimum'), maximum=item.get('maximum'), validation=item.get('validation', {})) for item in data.get('engineering_parameters', ())),
            creation_definition=creation_definition,
        )


__all__ = ["EngineeringParameterDefinition", "EquipmentDefinition"]
