"""Bindings from Control outputs to stable equipment-action intent."""

from __future__ import annotations

from dataclasses import dataclass

from .decision import ControlActionType, ControlDecision


@dataclass(frozen=True, slots=True)
class ControlActionBinding:
    """Configuration connecting a logic output to an equipment action."""

    control_id: str
    source_component: str
    source_output: str
    target_equipment_id: str
    action_type: ControlActionType
    reason: str

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
        if not isinstance(self.action_type, ControlActionType):
            object.__setattr__(self, "action_type", ControlActionType(self.action_type))

    def decision(self, *, simulation_time: float) -> ControlDecision:
        """Produce intent from an asserted logic output."""
        return ControlDecision(
            control_id=self.control_id,
            action_type=self.action_type,
            target_equipment_id=self.target_equipment_id,
            reason=self.reason,
            simulation_time=simulation_time,
            triggered_by=f"{self.source_component}.{self.source_output}",
        )


__all__ = ["ControlActionBinding"]
