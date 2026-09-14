"""Application handler for compound bus placement intent."""

from __future__ import annotations

from typing import Any

from .command import Command
from .commands.placement_commands import PLACE_BUS
from .commands.sld_commands import AddSLDNodeCommand
from .results import ApplicationResult
from .services.model_service import ModelService
from .services.sld_service import SLDService
from .transaction import Transaction


class BusPlacementCommandHandler:
    """Create Core Bus state and its SLD node in one Application transaction."""

    def __init__(self, model_service: ModelService, sld_service: SLDService) -> None:
        if not isinstance(model_service, ModelService):
            raise TypeError("model_service must be a ModelService")
        if not isinstance(sld_service, SLDService):
            raise TypeError("sld_service must be an SLDService")
        self._model_service = model_service
        self._sld_service = sld_service

    def __call__(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        if command.command_type != PLACE_BUS:
            raise ValueError(f"Unsupported placement command: {command.command_type}")

        p = command.payload
        model_result = self._model_service.create_bus(
            bus_id=p["bus_id"],
            name=p["name"],
            nominal_voltage_kv=p["nominal_voltage_kv"],
            voltage_pu=p["voltage_pu"],
            angle_deg=p["angle_deg"],
            frequency_hz=p["frequency_hz"],
            in_service=p["in_service"],
            transaction=transaction,
        )

        presentation_result = self._sld_service.execute(
            AddSLDNodeCommand(
                node_id=p["bus_id"],
                equipment_id=p["bus_id"],
                x=p["x"],
                y=p["y"],
                correlation_id=command.correlation_id,
                causation_id=command.command_id,
            ),
            transaction,
        )

        metadata = dict(model_result.metadata)
        metadata.update(presentation_result.metadata)
        metadata["presentation_operation"] = "place_bus"
        metadata["x"] = p["x"]
        metadata["y"] = p["y"]
        return ApplicationResult.success_result(
            value=model_result.value,
            message="Bus placed.",
            metadata=metadata,
        )


__all__ = ["BusPlacementCommandHandler"]
