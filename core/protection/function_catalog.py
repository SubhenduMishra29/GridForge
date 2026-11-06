# ============================================================
# File: core/protection/function_catalog.py
# GridForge V2 — Protection Function Catalog
# Author: Subhendu Mishra
# ============================================================

"""Canonical catalog of supported ANSI functions and their setting contracts."""

from __future__ import annotations

from dataclasses import MISSING, dataclass, fields, is_dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping, get_type_hints

from core.protection.distance import DistanceRelay
from core.protection.directional import DirectionalRelay
from core.protection.ieee_curves import IEEE_CURVES
from core.protection.overcurrent import (
    EarthIECOvercurrentRelay,
    EarthIECOvercurrentSettings,
    EarthInstantaneousOvercurrentRelay,
    EarthInstantaneousOvercurrentSettings,
    IECOvercurrentRelay,
    IECOvercurrentSettings,
    InstantaneousOvercurrentRelay,
    InstantaneousOvercurrentSettings,
    NegativeSequenceOvercurrentRelay,
)
from core.protection.relay_functions import IEC_CURVES
from core.protection.thermal import ThermalOverloadRelay
from core.protection.voltage import (
    OverVoltageRelay,
    OverVoltageSettings,
    UnderVoltageRelay,
    UnderVoltageSettings,
)
from core.protection.input_contracts import (
    ProtectionFunctionInputContract,
    CONTRACT_50, CONTRACT_51, CONTRACT_50N, CONTRACT_51N,
    CONTRACT_27, CONTRACT_59, CONTRACT_46, CONTRACT_49, CONTRACT_67, CONTRACT_21,
)


class ProtectionFunctionStatus(str, Enum):
    """Implementation status of an ANSI protection function."""

    IMPLEMENTED = "IMPLEMENTED"
    PARTIAL = "PARTIAL"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


@dataclass(frozen=True, slots=True)
class ProtectionSettingDefinition:
    """Immutable presentation metadata for one authoritative setting field."""

    key: str
    label: str
    datatype: str
    unit: str
    required: bool = True
    choices: tuple[str, ...] = ()
    choices_by: str | None = None
    choices_by_value: Mapping[str, tuple[str, ...]] | None = None

    def __post_init__(self) -> None:
        for name in ("key", "label", "datatype", "unit"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Protection setting {name} must be a non-empty string.")
            object.__setattr__(self, name, value.strip())
        if self.datatype not in {"number", "string"}:
            raise ValueError("Protection setting datatype must be number or string.")
        if not isinstance(self.required, bool):
            raise TypeError("Protection setting required must be boolean.")
        if not isinstance(self.choices, tuple) or any(
            not isinstance(choice, str) or not choice.strip() for choice in self.choices
        ):
            raise TypeError("Protection setting choices must be a tuple of non-empty strings.")
        if len(set(self.choices)) != len(self.choices):
            raise ValueError("Protection setting choices must be unique.")
        if self.choices_by is not None:
            if not isinstance(self.choices_by, str) or not self.choices_by.strip():
                raise ValueError("choices_by must be a non-empty setting key.")
            object.__setattr__(self, "choices_by", self.choices_by.strip())
        if self.choices_by_value is not None:
            if self.choices or self.choices_by is None or not isinstance(self.choices_by_value, Mapping):
                raise ValueError("Conditional choices require choices_by and cannot also define flat choices.")
            normalized = {}
            for selector, options in self.choices_by_value.items():
                if not isinstance(selector, str) or not selector.strip():
                    raise ValueError("Conditional choice selectors must be non-empty strings.")
                if not isinstance(options, tuple) or not options or any(
                    not isinstance(option, str) or not option.strip() for option in options
                ):
                    raise ValueError("Each conditional choice set must be a non-empty tuple of strings.")
                if len(set(options)) != len(options):
                    raise ValueError("Conditional choices must be unique.")
                normalized[selector.strip()] = tuple(options)
            object.__setattr__(self, "choices_by_value", MappingProxyType(normalized))
        elif self.choices_by is not None:
            raise ValueError("choices_by requires choices_by_value.")


@dataclass(frozen=True, slots=True)
class ProtectionFunctionSettingsContract:
    """Presentation contract cross-checked against an implementation dataclass.

    This metadata does not validate engineering values. The settings dataclass
    and ProtectionConfigurationService remain the validation authorities.
    """

    settings_type: type[Any]
    fields: tuple[ProtectionSettingDefinition, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.settings_type, type) or not is_dataclass(self.settings_type):
            raise TypeError("Protection settings contract requires a dataclass settings type.")
        if not isinstance(self.fields, tuple) or any(
            not isinstance(item, ProtectionSettingDefinition) for item in self.fields
        ):
            raise TypeError("Protection settings contract fields must be a tuple of setting definitions.")
        keys = tuple(item.key for item in self.fields)
        if len(set(keys)) != len(keys):
            raise ValueError("Protection settings contract keys must be unique.")
        model_fields = {item.name: item for item in fields(self.settings_type)}
        if set(keys) != set(model_fields):
            raise ValueError(
                f"Setting metadata keys for {self.settings_type.__name__} must exactly match "
                f"the settings dataclass fields; metadata={sorted(keys)}, model={sorted(model_fields)}."
            )
        try:
            annotations = get_type_hints(self.settings_type)
        except (NameError, TypeError):
            annotations = getattr(self.settings_type, "__annotations__", {})
        for definition in self.fields:
            model_field = model_fields[definition.key]
            expected_required = model_field.default is MISSING and model_field.default_factory is MISSING
            if definition.required is not expected_required:
                raise ValueError(
                    f"Required metadata for {definition.key} does not match "
                    f"{self.settings_type.__name__} dataclass defaults."
                )
            annotation = annotations.get(definition.key, model_field.type)
            expected_type = float if definition.datatype == "number" else str
            if annotation is not expected_type:
                raise TypeError(
                    f"Setting metadata datatype for {definition.key} does not match "
                    f"{self.settings_type.__name__} annotation {annotation!r}."
                )
            if definition.choices_by is not None and definition.choices_by not in keys:
                raise ValueError(f"Conditional setting {definition.key} references an unknown selector.")
        for definition in self.fields:
            if definition.choices_by_value is not None:
                selector = next(item for item in self.fields if item.key == definition.choices_by)
                if set(definition.choices_by_value) != set(selector.choices):
                    raise ValueError(
                        f"Conditional choices for {definition.key} must cover every "
                        f"choice of selector {definition.choices_by}."
                    )

    @property
    def default_values(self) -> Mapping[str, Any]:
        """Return defaults declared by the settings dataclass, never invented here."""
        values = {}
        for item in fields(self.settings_type):
            if item.default is not MISSING:
                values[item.name] = item.default
        return MappingProxyType(values)


@dataclass(frozen=True, slots=True)
class ProtectionFunctionSpecification:
    """Immutable metadata for one canonical ANSI function code."""

    code: str
    name: str
    status: ProtectionFunctionStatus
    implementation: type[Any] | None = None
    input_contract: ProtectionFunctionInputContract | None = None
    settings_contract: ProtectionFunctionSettingsContract | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.code, str):
            raise TypeError("Protection function code must be a string.")
        if not isinstance(self.name, str):
            raise TypeError("Protection function name must be a string.")
        if not isinstance(self.status, ProtectionFunctionStatus):
            raise TypeError("Protection function status must be a ProtectionFunctionStatus.")
        if self.implementation is not None and not isinstance(self.implementation, type):
            raise TypeError("Protection function implementation must be a class or None.")
        if self.input_contract is not None and not isinstance(
            self.input_contract, ProtectionFunctionInputContract
        ):
            raise TypeError("Protection function input contract must be a ProtectionFunctionInputContract or None.")
        if self.settings_contract is not None and not isinstance(
            self.settings_contract, ProtectionFunctionSettingsContract
        ):
            raise TypeError("Protection function settings contract must be ProtectionFunctionSettingsContract or None.")

        code = self.code.strip().upper()
        name = self.name.strip()
        if not code:
            raise ValueError("Protection function code cannot be empty.")
        if not name:
            raise ValueError("Protection function name cannot be empty.")
        if self.status is ProtectionFunctionStatus.IMPLEMENTED and self.implementation is None:
            raise ValueError("Implemented protection functions require an implementation.")
        if self.status is ProtectionFunctionStatus.NOT_IMPLEMENTED and self.implementation is not None:
            raise ValueError("Unimplemented protection functions cannot advertise an implementation.")
        if self.status is ProtectionFunctionStatus.PARTIAL and self.implementation is None:
            raise ValueError("Partially implemented protection functions require an implementation.")
        if self.status is ProtectionFunctionStatus.IMPLEMENTED and self.input_contract is None:
            raise ValueError("Implemented protection functions require an explicit input contract.")
        if self.status is ProtectionFunctionStatus.IMPLEMENTED and self.settings_contract is None:
            raise ValueError("Implemented protection functions require an explicit settings contract.")
        if self.status is not ProtectionFunctionStatus.IMPLEMENTED and self.settings_contract is not None:
            raise ValueError("Only implemented protection functions may advertise editable settings metadata.")
        if self.status is ProtectionFunctionStatus.NOT_IMPLEMENTED and self.input_contract is not None:
            raise ValueError("Unimplemented protection functions cannot advertise an input contract.")
        if self.input_contract is not None and self.input_contract.function_code != code:
            raise ValueError("Protection function input contract code must match the catalog code.")
        if self.settings_contract is not None:
            try:
                settings_type = get_type_hints(self.implementation.__init__).get("settings")
            except (NameError, TypeError):
                settings_type = getattr(self.implementation.__init__, "__annotations__", {}).get("settings")
            if settings_type is not self.settings_contract.settings_type:
                raise TypeError(
                    f"Settings contract for ANSI {code} does not match its implementation constructor."
                )
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "name", name)


def _settings_contract(settings_type: type[Any], *definitions: ProtectionSettingDefinition):
    return ProtectionFunctionSettingsContract(settings_type, tuple(definitions))


_PICKUP_A = ProtectionSettingDefinition("pickup", "Pickup", "number", "A")
_PICKUP_V = ProtectionSettingDefinition("pickup", "Pickup", "number", "V")
_CURVE_STANDARD = ProtectionSettingDefinition(
    "curve_standard", "Curve standard", "string", "—", required=False,
    choices=("IEC", "IEEE"),
)
_CURVE = ProtectionSettingDefinition(
    "curve", "Inverse-time curve", "string", "—", required=False,
    choices_by="curve_standard",
    choices_by_value={
        "IEC": tuple(IEC_CURVES),
        "IEEE": tuple(IEEE_CURVES),
    },
)


_SPECS = (
    ProtectionFunctionSpecification(
        "50", "Instantaneous overcurrent", ProtectionFunctionStatus.IMPLEMENTED,
        InstantaneousOvercurrentRelay, CONTRACT_50,
        _settings_contract(InstantaneousOvercurrentSettings, _PICKUP_A),
    ),
    ProtectionFunctionSpecification(
        "51", "Inverse-time overcurrent", ProtectionFunctionStatus.IMPLEMENTED,
        IECOvercurrentRelay, CONTRACT_51,
        _settings_contract(
            IECOvercurrentSettings,
            _PICKUP_A,
            _CURVE,
            ProtectionSettingDefinition("TMS", "Time multiplier setting", "number", "—", required=False),
            _CURVE_STANDARD,
        ),
    ),
    ProtectionFunctionSpecification(
        "50N", "Instantaneous earth-fault overcurrent", ProtectionFunctionStatus.IMPLEMENTED,
        EarthInstantaneousOvercurrentRelay, CONTRACT_50N,
        _settings_contract(EarthInstantaneousOvercurrentSettings, _PICKUP_A),
    ),
    ProtectionFunctionSpecification(
        "51N", "Inverse-time earth-fault overcurrent", ProtectionFunctionStatus.IMPLEMENTED,
        EarthIECOvercurrentRelay, CONTRACT_51N,
        _settings_contract(
            EarthIECOvercurrentSettings,
            _PICKUP_A,
            _CURVE,
            ProtectionSettingDefinition("TMS", "Time multiplier setting", "number", "—", required=False),
            _CURVE_STANDARD,
        ),
    ),
    ProtectionFunctionSpecification(
        "27", "Undervoltage", ProtectionFunctionStatus.IMPLEMENTED,
        UnderVoltageRelay, CONTRACT_27,
        _settings_contract(UnderVoltageSettings, _PICKUP_V),
    ),
    ProtectionFunctionSpecification(
        "59", "Overvoltage", ProtectionFunctionStatus.IMPLEMENTED,
        OverVoltageRelay, CONTRACT_59,
        _settings_contract(OverVoltageSettings, _PICKUP_V),
    ),
    ProtectionFunctionSpecification("46", "Negative-sequence / phase-balance overcurrent", ProtectionFunctionStatus.PARTIAL, NegativeSequenceOvercurrentRelay, CONTRACT_46),
    ProtectionFunctionSpecification("49", "Thermal overload", ProtectionFunctionStatus.PARTIAL, ThermalOverloadRelay, CONTRACT_49),
    ProtectionFunctionSpecification("67", "Directional overcurrent", ProtectionFunctionStatus.PARTIAL, DirectionalRelay, CONTRACT_67),
    ProtectionFunctionSpecification("81", "Frequency (underfrequency/overfrequency; RoCoF not implemented)", ProtectionFunctionStatus.NOT_IMPLEMENTED),
    ProtectionFunctionSpecification("87", "Differential protection", ProtectionFunctionStatus.NOT_IMPLEMENTED),
    ProtectionFunctionSpecification("21", "Distance protection", ProtectionFunctionStatus.PARTIAL, DistanceRelay, CONTRACT_21),
)

_CATALOG: Mapping[str, ProtectionFunctionSpecification] = MappingProxyType({spec.code: spec for spec in _SPECS})


def list_protection_functions() -> tuple[str, ...]:
    return tuple(_CATALOG)


def get_protection_function(code: str) -> ProtectionFunctionSpecification:
    if not isinstance(code, str):
        raise TypeError("Protection function code must be a string.")
    normalized = code.strip().upper()
    if not normalized:
        raise ValueError("Protection function code cannot be empty.")
    try:
        return _CATALOG[normalized]
    except KeyError as exc:
        raise KeyError(f"Unknown protection function code: {normalized}") from exc


__all__ = [
    "ProtectionFunctionStatus",
    "ProtectionSettingDefinition",
    "ProtectionFunctionSettingsContract",
    "ProtectionFunctionSpecification",
    "get_protection_function",
    "list_protection_functions",
]
