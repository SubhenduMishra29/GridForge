"""Bindings from Control outputs to stable equipment-action intent.

Author: Subhendu Mishra
"""

from __future__ import annotations

from dataclasses import dataclass

from .decision import ControlActionType, ControlDecision, ControlTargetType


@dataclass(frozen=True, slots=True)
class ControlActionBinding:
    """Configuration connecting a logic output to an equipment action intent."""

    control_id: str
    source_component: str
    source_output: str
    target_equipment_id: str
    action_type: ControlActionType
    reason: str
    target_equipment_type: str = ControlTargetType.BREAKER.value
    interlock_id: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "control_id",
            "source_component",
            "source_output",
            "target_equipment_id",
            "reason",
        ):
            value = str(getattr(self, field_name)).strip()
            if not value:
                raise ValueError(f"{field_name} must be a non-empty string.")
            object.__setattr__(self, field_name, value)

        target_type = str(self.target_equipment_type).strip().lower()
        try:
            target_type = ControlTargetType(target_type).value
        except ValueError as exc:
            raise ValueError(
                f"Unsupported Control target equipment type: {target_type!r}."
            ) from exc
        object.__setattr__(self, "target_equipment_type", target_type)

        if self.interlock_id is not None:
            value = str(self.interlock_id).strip()
            object.__setattr__(self, "interlock_id", value or None)
        if not isinstance(self.action_type, ControlActionType):
            object.__setattr__(self, "action_type", ControlActionType(self.action_type))

    @property
    def binding_id(self) -> str: return self.control_id
    @property
    def source_control_id(self) -> str: return self.control_id
    @property
    def target_type(self) -> str: return self.target_equipment_type
    @property
    def target_id(self) -> str: return self.target_equipment_id
    @property
    def action(self) -> ControlActionType: return self.action_type

    def decision(self, *, simulation_time: float):
        """Produce an immutable intent from an asserted logic output."""
        return ControlDecision(
            control_id=self.control_id,
            action_type=self.action_type,
            target_equipment_id=self.target_equipment_id,
            target_equipment_type=self.target_equipment_type,
            reason=self.reason,
            simulation_time=simulation_time,
            triggered_by=f"{self.source_component}.{self.source_output}",
        )


__all__ = ["ControlActionBinding"]
