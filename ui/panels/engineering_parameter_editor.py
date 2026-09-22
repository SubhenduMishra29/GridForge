# ============================================================
# File: ui/panels/engineering_parameter_editor.py
# GridForge V2 — Generic Engineering Parameter Editor
# Author: Subhendu Mishra
# ============================================================

"""Generic presentation-to-Application adapter for typed engineering edits."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Mapping

from core.application.commands.model_commands import UpdateTransformerCommand
from core.model.transformer import ImpedanceBasis

from ui.projection.projection_state import ProjectionState


@dataclass(frozen=True, slots=True)
class EngineeringConfigurationIntent:
    """Immutable UI intent containing typed engineering values only."""

    element_type: str
    element_id: str
    values: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.element_type, str) or not self.element_type.strip():
            raise ValueError("element_type must be non-empty.")
        if not isinstance(self.element_id, str) or not self.element_id.strip():
            raise ValueError("element_id must be non-empty.")
        object.__setattr__(self, "element_type", self.element_type.strip().lower())
        object.__setattr__(self, "element_id", self.element_id.strip())
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))


class EngineeringParameterEditor:
    """Build and submit immutable commands from generic projected parameters.

    The editor owns no engineering state. Values are read from ProjectionState,
    edited as typed values, converted into one immutable Application command,
    and then discarded. Core/Application ReadModel state remains authoritative.
    """

    def __init__(self, application: Any) -> None:
        if application is None or not callable(getattr(application, "execute", None)):
            raise TypeError("application must provide execute(command).")
        self._application = application
        self._builders: dict[str, Callable[[EngineeringConfigurationIntent], Any]] = {
            "transformer": self._build_transformer_command,
            "transformers": self._build_transformer_command,
        }

    def intent_from_projection(
        self,
        projection: ProjectionState,
        changes: Mapping[str, Any],
    ) -> EngineeringConfigurationIntent:
        if not isinstance(projection, ProjectionState):
            raise TypeError("projection must be a ProjectionState.")
        if not changes:
            raise ValueError("At least one engineering parameter change is required.")

        editable = {
            item.parameter_id: item
            for item in projection.engineering_parameters
            if item.editable and not item.derived
        }
        unknown = [key for key in changes if key not in editable]
        if unknown:
            raise ValueError(
                "Engineering parameter(s) are not editable or not projected: "
                + ", ".join(sorted(unknown))
            )

        typed_values: dict[str, Any] = {}
        for parameter_id, value in changes.items():
            parameter = editable[parameter_id]
            typed_values[parameter_id] = self._coerce_typed_value(
                parameter.datatype, value, parameter_id
            )

        return EngineeringConfigurationIntent(
            element_type=projection.display_type,
            element_id=projection.object_id,
            values=typed_values,
        )

    def submit(self, intent: EngineeringConfigurationIntent) -> Any:
        if not isinstance(intent, EngineeringConfigurationIntent):
            raise TypeError("intent must be an EngineeringConfigurationIntent.")
        builder = self._builders.get(intent.element_type)
        if builder is None:
            raise KeyError(
                f"No canonical engineering command builder is registered for "
                f"{intent.element_type!r}."
            )
        return self._application.execute(builder(intent))

    @staticmethod
    def _coerce_typed_value(datatype: str, value: Any, parameter_id: str) -> Any:
        normalized = str(datatype or "unknown").strip().lower()
        if normalized in {"float", "number"}:
            if isinstance(value, bool):
                raise TypeError(f"{parameter_id} requires a numeric value.")
            return float(value)
        if normalized in {"bool", "boolean"}:
            if not isinstance(value, bool):
                raise TypeError(f"{parameter_id} requires a boolean value.")
            return value
        if normalized == "enum":
            return str(value).strip().lower()
        return value

    @staticmethod
    def _build_transformer_command(
        intent: EngineeringConfigurationIntent,
    ) -> UpdateTransformerCommand:
        values = dict(intent.values)
        if "impedance_basis" in values:
            values["impedance_basis"] = ImpedanceBasis(str(values["impedance_basis"]).strip().lower())
        return UpdateTransformerCommand(
            transformer_id=intent.element_id,
            **values,
        )


__all__ = ["EngineeringConfigurationIntent", "EngineeringParameterEditor"]
