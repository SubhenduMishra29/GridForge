from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from .command import Command
from .endpoint_resolver import EndpointResolver
from .results import ApplicationResult
from .transaction import Transaction
from .commands.model_commands import (
    CREATE_BUS, UPDATE_BUS, DELETE_BUS, CREATE_LINE, DELETE_LINE,
    CREATE_TRANSFORMER, DELETE_TRANSFORMER, CREATE_LOAD, UPDATE_LOAD, DELETE_LOAD,
    CREATE_GRID, UPDATE_GRID, DELETE_GRID,
)
from .commands.capacitor_commands import (
    CREATE_CAPACITOR, UPDATE_CAPACITOR, DELETE_CAPACITOR,
    PUT_CAPACITOR_IN_SERVICE, TAKE_CAPACITOR_OUT_OF_SERVICE,
)
from .commands.measurement_commands import (
    CREATE_CURRENT_TRANSFORMER, UPDATE_CURRENT_TRANSFORMER, DELETE_CURRENT_TRANSFORMER,
    PUT_CURRENT_TRANSFORMER_IN_SERVICE, TAKE_CURRENT_TRANSFORMER_OUT_OF_SERVICE,
    CREATE_CAPACITIVE_VOLTAGE_TRANSFORMER, UPDATE_CAPACITIVE_VOLTAGE_TRANSFORMER,
    DELETE_CAPACITIVE_VOLTAGE_TRANSFORMER, PUT_CAPACITIVE_VOLTAGE_TRANSFORMER_IN_SERVICE,
    TAKE_CAPACITIVE_VOLTAGE_TRANSFORMER_OUT_OF_SERVICE,
)
from .commands.battery_commands import (
    CREATE_BATTERY, UPDATE_BATTERY, DELETE_BATTERY,
    PUT_BATTERY_IN_SERVICE, TAKE_BATTERY_OUT_OF_SERVICE,
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
            CREATE_BUS: self.create_bus, UPDATE_BUS: self.update_bus, DELETE_BUS: self.delete_bus,
            CREATE_LINE: self.create_line, DELETE_LINE: self.delete_line,
            CREATE_TRANSFORMER: self.create_transformer, DELETE_TRANSFORMER: self.delete_transformer,
            CREATE_LOAD: self.create_load, UPDATE_LOAD: self.update_load, DELETE_LOAD: self.delete_load,
            CREATE_GRID: self.create_grid, UPDATE_GRID: self.update_grid, DELETE_GRID: self.delete_grid,
            CREATE_CAPACITOR: self.create_capacitor, UPDATE_CAPACITOR: self.update_capacitor,
            DELETE_CAPACITOR: self.delete_capacitor, PUT_CAPACITOR_IN_SERVICE: self.put_capacitor_in_service,
            TAKE_CAPACITOR_OUT_OF_SERVICE: self.take_capacitor_out_of_service,
            CREATE_CURRENT_TRANSFORMER: self.create_current_transformer,
            UPDATE_CURRENT_TRANSFORMER: self.update_current_transformer,
            DELETE_CURRENT_TRANSFORMER: self.delete_current_transformer,
            PUT_CURRENT_TRANSFORMER_IN_SERVICE: self.put_current_transformer_in_service,
            TAKE_CURRENT_TRANSFORMER_OUT_OF_SERVICE: self.take_current_transformer_out_of_service,
            CREATE_CAPACITIVE_VOLTAGE_TRANSFORMER: self.create_capacitive_voltage_transformer,
            UPDATE_CAPACITIVE_VOLTAGE_TRANSFORMER: self.update_capacitive_voltage_transformer,
            DELETE_CAPACITIVE_VOLTAGE_TRANSFORMER: self.delete_capacitive_voltage_transformer,
            PUT_CAPACITIVE_VOLTAGE_TRANSFORMER_IN_SERVICE: self.put_capacitive_voltage_transformer_in_service,
            TAKE_CAPACITIVE_VOLTAGE_TRANSFORMER_OUT_OF_SERVICE: self.take_capacitive_voltage_transformer_out_of_service,
            CREATE_BATTERY: self.create_battery,
            UPDATE_BATTERY: self.update_battery,
            DELETE_BATTERY: self.delete_battery,
            PUT_BATTERY_IN_SERVICE: self.put_battery_in_service,
            TAKE_BATTERY_OUT_OF_SERVICE: self.take_battery_out_of_service,
        }

    def create_bus(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        p = command.payload
        return self._model_service.create_bus(bus_id=p["bus_id"], name=p["name"], nominal_voltage_kv=p["nominal_voltage_kv"], voltage_pu=p["voltage_pu"], angle_deg=p["angle_deg"], frequency_hz=p["frequency_hz"], in_service=p["in_service"], transaction=transaction)

    def update_bus(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        p = command.payload
        return self._model_service.update_bus(bus_id=p["bus_id"], name=p["name"], nominal_voltage_kv=p["nominal_voltage_kv"], voltage_pu=p["voltage_pu"], angle_deg=p["angle_deg"], frequency_hz=p["frequency_hz"], in_service=p["in_service"], transaction=transaction)

    def delete_bus(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._model_service.delete_bus(bus_id=command.payload["bus_id"], transaction=transaction)

    def create_line(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        p = command.payload
        return self._model_service.create_line(line_id=p["line_id"], endpoint_from=EndpointResolver.resolve(context, p["endpoint_from"]), endpoint_to=EndpointResolver.resolve(context, p["endpoint_to"]), r=p["r"], x=p["x"], b=p["b"], name=p["name"], rate_mva=p["rate_mva"], transaction=transaction)

    def delete_line(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._model_service.delete_line(line_id=command.payload["line_id"], transaction=transaction)

    def create_transformer(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        p = command.payload
        return self._model_service.create_transformer(transformer_id=p["transformer_id"], endpoint_from=EndpointResolver.resolve(context, p["endpoint_from"]), endpoint_to=EndpointResolver.resolve(context, p["endpoint_to"]), r=p["r"], x=p["x"], tap=p["tap"], shift=p["shift"], name=p["name"], rate_mva=p["rate_mva"], transaction=transaction)

    def delete_transformer(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._model_service.delete_transformer(transformer_id=command.payload["transformer_id"], transaction=transaction)

    def create_load(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        p = command.payload
        return self._model_service.create_load(load_id=p["load_id"], p=p["p"], q=p["q"], name=p["name"], in_service=p["in_service"], transaction=transaction)

    def update_load(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        p = command.payload
        return self._model_service.update_load(load_id=p["load_id"], name=p["name"], p=p["p"], q=p["q"], in_service=p["in_service"], transaction=transaction)

    def delete_load(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._model_service.delete_load(load_id=command.payload["load_id"], transaction=transaction)

    def create_grid(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        p = command.payload
        return self._model_service.create_grid(grid_id=p["grid_id"], name=p["name"], nominal_voltage_kv=p["nominal_voltage_kv"], frequency_hz=p["frequency_hz"], voltage_pu=p["voltage_pu"], angle_deg=p["angle_deg"], p_mw=p["p_mw"], q_mvar=p["q_mvar"], short_circuit_mva=p["short_circuit_mva"], x_over_r=p["x_over_r"], z1_pu=p["z1_pu"], z2_pu=p["z2_pu"], z0_pu=p["z0_pu"], in_service=p["in_service"], grounded=p["grounded"], transaction=transaction)

    def update_grid(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        p = command.payload
        return self._model_service.update_grid(grid_id=p["grid_id"], name=p["name"], nominal_voltage_kv=p["nominal_voltage_kv"], frequency_hz=p["frequency_hz"], voltage_pu=p["voltage_pu"], angle_deg=p["angle_deg"], p_mw=p["p_mw"], q_mvar=p["q_mvar"], short_circuit_mva=p["short_circuit_mva"], x_over_r=p["x_over_r"], z1_pu=p["z1_pu"], z2_pu=p["z2_pu"], z0_pu=p["z0_pu"], in_service=p["in_service"], grounded=p["grounded"], transaction=transaction)

    def delete_grid(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._model_service.delete_grid(grid_id=command.payload["grid_id"], transaction=transaction)

    def _shunt_service(self) -> Any:
        return self._model_service.shunt_service

    def create_capacitor(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        p = command.payload
        endpoint = EndpointResolver.resolve(context, p["endpoint"]) if p["endpoint"] is not None else None
        return self._shunt_service().create_capacitor(capacitor_id=p["capacitor_id"], name=p["name"], endpoint=endpoint, reactive_power_injection_mvar=p["reactive_power_injection_mvar"], in_service=p["in_service"], transaction=transaction)

    def update_capacitor(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        p = command.payload
        endpoint = EndpointResolver.resolve(context, p["endpoint"]) if p["endpoint"] is not None else None
        return self._shunt_service().update_capacitor(capacitor_id=p["capacitor_id"], name=p["name"], endpoint=endpoint, reactive_power_injection_mvar=p["reactive_power_injection_mvar"], in_service=p["in_service"], transaction=transaction)

    def delete_capacitor(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._shunt_service().delete_capacitor(capacitor_id=command.payload["capacitor_id"], transaction=transaction)

    def put_capacitor_in_service(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._shunt_service().put_capacitor_in_service(capacitor_id=command.payload["capacitor_id"], transaction=transaction)

    def take_capacitor_out_of_service(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._shunt_service().take_capacitor_out_of_service(capacitor_id=command.payload["capacitor_id"], transaction=transaction)

    def _measurement_service(self) -> Any:
        return self._model_service.measurement_service

    def create_current_transformer(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        p = command.payload
        resolve = lambda key: EndpointResolver.resolve(context, p[key]) if p[key] is not None else None
        return self._measurement_service().create_current_transformer(ct_id=p["transformer_id"], name=p["name"], primary_rated_current_a=p["primary_rated_current_a"], secondary_rated_current_a=p["secondary_rated_current_a"], burden_va=p["burden_va"], accuracy_class=p["accuracy_class"], frequency_hz=p["frequency_hz"], polarity=p["polarity"], in_service=p["in_service"], p1_endpoint=resolve("p1_endpoint"), p2_endpoint=resolve("p2_endpoint"), s1_endpoint=resolve("s1_endpoint"), s2_endpoint=resolve("s2_endpoint"), transaction=transaction)

    def update_current_transformer(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        p = command.payload
        return self._measurement_service().update_current_transformer(ct_id=p["transformer_id"], name=p["name"], primary_rated_current_a=p["primary_rated_current_a"], secondary_rated_current_a=p["secondary_rated_current_a"], burden_va=p["burden_va"], accuracy_class=p["accuracy_class"], frequency_hz=p["frequency_hz"], polarity=p["polarity"], in_service=p["in_service"], transaction=transaction)

    def delete_current_transformer(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._measurement_service().delete_current_transformer(ct_id=command.payload["transformer_id"], transaction=transaction)

    def put_current_transformer_in_service(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._measurement_service().put_current_transformer_in_service(ct_id=command.payload["transformer_id"], transaction=transaction)

    def take_current_transformer_out_of_service(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._measurement_service().take_current_transformer_out_of_service(ct_id=command.payload["transformer_id"], transaction=transaction)

    def create_capacitive_voltage_transformer(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        p = command.payload
        resolve = lambda key: EndpointResolver.resolve(context, p[key]) if p[key] is not None else None
        return self._measurement_service().create_capacitive_voltage_transformer(cvt_id=p["transformer_id"], name=p["name"], rated_primary_voltage_kv=p["rated_primary_voltage_kv"], rated_secondary_voltage_v=p["rated_secondary_voltage_v"], accuracy_class=p["accuracy_class"], rated_burden_va=p["rated_burden_va"], polarity=p["polarity"], frequency_hz=p["frequency_hz"], in_service=p["in_service"], h1_endpoint=resolve("h1_endpoint"), h2_endpoint=resolve("h2_endpoint"), x1_endpoint=resolve("x1_endpoint"), x2_endpoint=resolve("x2_endpoint"), transaction=transaction)

    def update_capacitive_voltage_transformer(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        p = command.payload
        return self._measurement_service().update_capacitive_voltage_transformer(cvt_id=p["transformer_id"], name=p["name"], rated_primary_voltage_kv=p["rated_primary_voltage_kv"], rated_secondary_voltage_v=p["rated_secondary_voltage_v"], accuracy_class=p["accuracy_class"], rated_burden_va=p["rated_burden_va"], polarity=p["polarity"], frequency_hz=p["frequency_hz"], in_service=p["in_service"], transaction=transaction)

    def delete_capacitive_voltage_transformer(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._measurement_service().delete_capacitive_voltage_transformer(cvt_id=command.payload["transformer_id"], transaction=transaction)

    def put_capacitive_voltage_transformer_in_service(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._measurement_service().put_capacitive_voltage_transformer_in_service(cvt_id=command.payload["transformer_id"], transaction=transaction)

    def take_capacitive_voltage_transformer_out_of_service(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._measurement_service().take_capacitive_voltage_transformer_out_of_service(cvt_id=command.payload["transformer_id"], transaction=transaction)

    def _battery_service(self) -> Any:
        return self._model_service.battery_service

    def create_battery(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        p = command.payload
        endpoint = EndpointResolver.resolve(context, p["endpoint"]) if p["endpoint"] is not None else None
        return self._battery_service().create_battery(
            battery_id=p["battery_id"], name=p["name"], endpoint=endpoint,
            p_mw=p["p_mw"], q_mvar=p["q_mvar"], max_charge_mw=p["max_charge_mw"],
            max_discharge_mw=p["max_discharge_mw"], energy_capacity_mwh=p["energy_capacity_mwh"],
            soc=p["soc"], soc_min=p["soc_min"], soc_max=p["soc_max"],
            in_service=p["in_service"], transaction=transaction,
        )

    def update_battery(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        p = command.payload
        return self._battery_service().update_battery(
            battery_id=p["battery_id"], name=p["name"], p_mw=p["p_mw"], q_mvar=p["q_mvar"],
            max_charge_mw=p["max_charge_mw"], max_discharge_mw=p["max_discharge_mw"],
            energy_capacity_mwh=p["energy_capacity_mwh"], soc=p["soc"], soc_min=p["soc_min"],
            soc_max=p["soc_max"], in_service=p["in_service"], transaction=transaction,
        )

    def delete_battery(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._battery_service().delete_battery(battery_id=command.payload["battery_id"], transaction=transaction)

    def put_battery_in_service(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._battery_service().put_battery_in_service(battery_id=command.payload["battery_id"], transaction=transaction)

    def take_battery_out_of_service(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult[Any]:
        return self._battery_service().take_battery_out_of_service(battery_id=command.payload["battery_id"], transaction=transaction)


def build_model_command_handlers(model_service: Any) -> Mapping[str, Handler]:
    return ModelCommandHandlers(model_service).handlers()


__all__ = ["ModelCommandHandlers", "build_model_command_handlers"]