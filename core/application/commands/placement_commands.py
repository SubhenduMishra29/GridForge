"""Compatibility constructor for the canonical Bus creation command."""

from __future__ import annotations

from uuid import UUID, uuid4

from .model_commands import CREATE_BUS
from ..command import Command


PLACE_BUS = CREATE_BUS


class PlaceBusCommand(Command):
    """Compatibility constructor for the canonical Bus creation command."""

    def __init__(self, *, bus_id: str, name: str = "Bus", nominal_voltage_kv: float = 0.0,
                 voltage_pu: float = 1.0, angle_deg: float = 0.0, frequency_hz: float = 50.0,
                 in_service: bool = True, x: float = 0.0, y: float = 0.0,
                 presentation_properties: dict | None = None,
                 command_id: UUID | None = None, correlation_id: UUID | None = None,
                 causation_id: UUID | None = None) -> None:
        super().__init__(
            command_type=CREATE_BUS,
            payload={
                "bus_id": bus_id, "name": name,
                "nominal_voltage_kv": nominal_voltage_kv,
                "voltage_pu": voltage_pu, "angle_deg": angle_deg,
                "frequency_hz": frequency_hz, "in_service": in_service,
                "x": float(x), "y": float(y),
                "presentation_properties": {} if presentation_properties is None else dict(presentation_properties),
            },
            command_id=command_id or uuid4(),
            correlation_id=correlation_id,
            causation_id=causation_id,
        )


__all__ = ["PLACE_BUS", "PlaceBusCommand"]
