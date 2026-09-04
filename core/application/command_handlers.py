# ============================================================
# File: core/application/command_handlers.py
# GridForge V2 — Application Command Handlers
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from .command import Command
from .endpoint_resolver import EndpointResolver
from .results import ApplicationResult
from .transaction import Transaction
from .services.bus_model_service import ModelService

from .commands.model_commands import (
    CREATE_BUS,
    DELETE_BUS,
    CREATE_LINE,
    DELETE_LINE,
    CREATE_TRANSFORMER,
    DELETE_TRANSFORMER,
    CREATE_LOAD,
    UPDATE_LOAD,
    DELETE_LOAD,
    CREATE_GRID,
    UPDATE_GRID,
    DELETE_GRID,
)

Handler = Callable[[Command, Any, Transaction], ApplicationResult[Any]]


class ModelCommandHandlers:
    """Application handlers for model commands."""

    def __init__(self, model_service: Any) -> None:
        if model_service is None:
            raise ValueError("model_service is required.")
        self._model_service = model_service

    def handlers(self) -> Mapping[str, Handler]:
        return {
            CREATE_BUS: self.create_bus,
            DELETE_BUS: self.delete_bus,
            CREATE_LINE: self.create_line,
            DELETE_LINE: self.delete_line,
            CREATE_TRANSFORMER: self.create_transformer,
            DELETE_TRANSFORMER: self.delete_transformer,
            CREATE_LOAD: self.create_load,
            UPDATE_LOAD: self.update_load,
            DELETE_LOAD: self.delete_load,
            CREATE_GRID: self.create_grid,
            UPDATE_GRID: self.update_grid,
            DELETE_GRID: self.delete_grid,
        }

    def create_bus(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        """Create a Core Bus using the authoritative Bus contract."""
        payload = command.payload
        return self._model_service.create_bus(
            bus_id=payload["bus_id"],
            name=payload["name"],
            nominal_voltage_kv=payload["nominal_voltage_kv"],
            voltage_pu=payload["voltage_pu"],
            angle_deg=payload["angle_deg"],
            frequency_hz=payload["frequency_hz"],
            in_service=payload["in_service"],
            transaction=transaction,
        )

    def delete_bus(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._model_service.delete_bus(
            bus_id=command.payload["bus_id"], transaction=transaction
        )

    def create_line(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        payload = command.payload
        endpoint_from = EndpointResolver.resolve(context, payload["endpoint_from"])
        endpoint_to = EndpointResolver.resolve(context, payload["endpoint_to"])
        return self._model_service.create_line(
            line_id=payload["line_id"], endpoint_from=endpoint_from,
            endpoint_to=endpoint_to, r=payload["r"], x=payload["x"],
            b=payload["b"], name=payload["name"],
            rate_mva=payload["rate_mva"], transaction=transaction,
        )

    def delete_line(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._model_service.delete_line(
            line_id=command.payload["line_id"], transaction=transaction
        )

    def create_transformer(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        payload = command.payload
        endpoint_from = EndpointResolver.resolve(context, payload["endpoint_from"])
        endpoint_to = EndpointResolver.resolve(context, payload["endpoint_to"])
        return self._model_service.create_transformer(
            transformer_id=payload["transformer_id"],
            endpoint_from=endpoint_from, endpoint_to=endpoint_to,
            r=payload["r"], x=payload["x"], tap=payload["tap"],
            shift=payload["shift"], name=payload["name"],
            rate_mva=payload["rate_mva"], transaction=transaction,
        )

    def delete_transformer(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._model_service.delete_transformer(
            transformer_id=command.payload["transformer_id"],
            transaction=transaction,
        )

    def create_load(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        payload = command.payload
        return self._model_service.create_load(
            load_id=payload["load_id"], p=payload["p"], q=payload["q"],
            name=payload["name"], in_service=payload["in_service"],
            transaction=transaction,
        )

    def update_load(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        payload = command.payload
        return self._model_service.update_load(
            load_id=payload["load_id"], name=payload["name"],
            p=payload["p"], q=payload["q"],
            in_service=payload["in_service"], transaction=transaction,
        )

    def delete_load(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._model_service.delete_load(
            load_id=command.payload["load_id"], transaction=transaction
        )

    def create_grid(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        payload = command.payload
        return self._model_service.create_grid(
            grid_id=payload["grid_id"], name=payload["name"],
            nominal_voltage_kv=payload["nominal_voltage_kv"],
            frequency_hz=payload["frequency_hz"], voltage_pu=payload["voltage_pu"],
            angle_deg=payload["angle_deg"], p_mw=payload["p_mw"],
            q_mvar=payload["q_mvar"], short_circuit_mva=payload["short_circuit_mva"],
            x_over_r=payload["x_over_r"], z1_pu=payload["z1_pu"],
            z2_pu=payload["z2_pu"], z0_pu=payload["z0_pu"],
            in_service=payload["in_service"], grounded=payload["grounded"],
            transaction=transaction,
        )

    def update_grid(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        payload = command.payload
        return self._model_service.update_grid(
            grid_id=payload["grid_id"], name=payload["name"],
            nominal_voltage_kv=payload["nominal_voltage_kv"],
            frequency_hz=payload["frequency_hz"], voltage_pu=payload["voltage_pu"],
            angle_deg=payload["angle_deg"], p_mw=payload["p_mw"],
            q_mvar=payload["q_mvar"], short_circuit_mva=payload["short_circuit_mva"],
            x_over_r=payload["x_over_r"], z1_pu=payload["z1_pu"],
            z2_pu=payload["z2_pu"], z0_pu=payload["z0_pu"],
            in_service=payload["in_service"], grounded=payload["grounded"],
            transaction=transaction,
        )

    def delete_grid(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._model_service.delete_grid(
            grid_id=command.payload["grid_id"], transaction=transaction
        )


def build_model_command_handlers(model_service: Any) -> Mapping[str, Handler]:
    return ModelCommandHandlers(model_service).handlers()


__all__ = ["ModelCommandHandlers", "build_model_command_handlers"]
