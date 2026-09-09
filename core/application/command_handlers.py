from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable

from .command import Command
from .endpoint_resolver import EndpointResolver
from .results import ApplicationResult
from .transaction import Transaction
from .commands.model_commands import (
    CREATE_BUS, UPDATE_BUS, DELETE_BUS, CREATE_GRID, UPDATE_GRID, DELETE_GRID,
    CREATE_GENERATOR, UPDATE_GENERATOR, DELETE_GENERATOR, CREATE_LOAD, UPDATE_LOAD, DELETE_LOAD,
    CREATE_SHUNT, UPDATE_SHUNT, DELETE_SHUNT, CREATE_LINE, DELETE_LINE,
    CREATE_TRANSFORMER, DELETE_TRANSFORMER, CREATE_CABLE, UPDATE_CABLE, DELETE_CABLE,
    CREATE_SWITCH, UPDATE_SWITCH, DELETE_SWITCH, OPEN_SWITCH, CLOSE_SWITCH,
    PUT_SWITCH_IN_SERVICE, TAKE_SWITCH_OUT_OF_SERVICE, CREATE_DISCONNECTOR, UPDATE_DISCONNECTOR,
    DELETE_DISCONNECTOR, OPEN_DISCONNECTOR, CLOSE_DISCONNECTOR, PUT_DISCONNECTOR_IN_SERVICE,
    TAKE_DISCONNECTOR_OUT_OF_SERVICE, CREATE_FUSE, UPDATE_FUSE, DELETE_FUSE, BLOW_FUSE, RESET_FUSE,
    PUT_FUSE_IN_SERVICE, TAKE_FUSE_OUT_OF_SERVICE,
)
from .commands.breaker_commands import (
    CREATE_BREAKER, UPDATE_BREAKER, DELETE_BREAKER, OPEN_BREAKER, CLOSE_BREAKER, TRIP_BREAKER,
    PUT_BREAKER_IN_SERVICE, TAKE_BREAKER_OUT_OF_SERVICE,
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
    """Application handlers for supported model commands."""

    def __init__(self, model_service: Any) -> None:
        if model_service is None:
            raise ValueError("model_service is required.")
        self._model_service = model_service

    def handlers(self) -> Mapping[str, Handler]:
        return {
            CREATE_BUS: self.create_bus, UPDATE_BUS: self.update_bus, DELETE_BUS: self.delete_bus,
            CREATE_GRID: self.create_grid, UPDATE_GRID: self.update_grid, DELETE_GRID: self.delete_grid,
            CREATE_GENERATOR: self.create_generator, UPDATE_GENERATOR: self.update_generator, DELETE_GENERATOR: self.delete_generator,
            CREATE_LOAD: self.create_load, UPDATE_LOAD: self.update_load, DELETE_LOAD: self.delete_load,
            CREATE_SHUNT: self.create_shunt, UPDATE_SHUNT: self.update_shunt, DELETE_SHUNT: self.delete_shunt,
            CREATE_LINE: self.create_line, DELETE_LINE: self.delete_line,
            CREATE_TRANSFORMER: self.create_transformer, DELETE_TRANSFORMER: self.delete_transformer,
            CREATE_CABLE: self.create_cable, UPDATE_CABLE: self.update_cable, DELETE_CABLE: self.delete_cable,
            CREATE_SWITCH: self.create_switch, UPDATE_SWITCH: self.update_switch, DELETE_SWITCH: self.delete_switch,
            OPEN_SWITCH: self.open_switch, CLOSE_SWITCH: self.close_switch,
            PUT_SWITCH_IN_SERVICE: self.put_switch_in_service, TAKE_SWITCH_OUT_OF_SERVICE: self.take_switch_out_of_service,
            CREATE_BREAKER: self.create_breaker, UPDATE_BREAKER: self.update_breaker, DELETE_BREAKER: self.delete_breaker,
            OPEN_BREAKER: self.open_breaker, CLOSE_BREAKER: self.close_breaker, TRIP_BREAKER: self.trip_breaker,
            PUT_BREAKER_IN_SERVICE: self.put_breaker_in_service, TAKE_BREAKER_OUT_OF_SERVICE: self.take_breaker_out_of_service,
            CREATE_DISCONNECTOR: self.create_disconnector, UPDATE_DISCONNECTOR: self.update_disconnector,
            DELETE_DISCONNECTOR: self.delete_disconnector, OPEN_DISCONNECTOR: self.open_disconnector,
            CLOSE_DISCONNECTOR: self.close_disconnector, PUT_DISCONNECTOR_IN_SERVICE: self.put_disconnector_in_service,
            TAKE_DISCONNECTOR_OUT_OF_SERVICE: self.take_disconnector_out_of_service,
            CREATE_FUSE: self.create_fuse, UPDATE_FUSE: self.update_fuse, DELETE_FUSE: self.delete_fuse,
            BLOW_FUSE: self.blow_fuse, RESET_FUSE: self.reset_fuse,
            PUT_FUSE_IN_SERVICE: self.put_fuse_in_service, TAKE_FUSE_OUT_OF_SERVICE: self.take_fuse_out_of_service,
            CREATE_CAPACITOR: self.create_capacitor, UPDATE_CAPACITOR: self.update_capacitor,
            DELETE_CAPACITOR: self.delete_capacitor, PUT_CAPACITOR_IN_SERVICE: self.put_capacitor_in_service,
            TAKE_CAPACITOR_OUT_OF_SERVICE: self.take_capacitor_out_of_service,
            CREATE_CURRENT_TRANSFORMER: self.create_current_transformer, UPDATE_CURRENT_TRANSFORMER: self.update_current_transformer,
            DELETE_CURRENT_TRANSFORMER: self.delete_current_transformer, PUT_CURRENT_TRANSFORMER_IN_SERVICE: self.put_current_transformer_in_service,
            TAKE_CURRENT_TRANSFORMER_OUT_OF_SERVICE: self.take_current_transformer_out_of_service,
            CREATE_CAPACITIVE_VOLTAGE_TRANSFORMER: self.create_capacitive_voltage_transformer,
            UPDATE_CAPACITIVE_VOLTAGE_TRANSFORMER: self.update_capacitive_voltage_transformer,
            DELETE_CAPACITIVE_VOLTAGE_TRANSFORMER: self.delete_capacitive_voltage_transformer,
            PUT_CAPACITIVE_VOLTAGE_TRANSFORMER_IN_SERVICE: self.put_capacitive_voltage_transformer_in_service,
            TAKE_CAPACITIVE_VOLTAGE_TRANSFORMER_OUT_OF_SERVICE: self.take_capacitive_voltage_transformer_out_of_service,
            CREATE_BATTERY: self.create_battery, UPDATE_BATTERY: self.update_battery, DELETE_BATTERY: self.delete_battery,
            PUT_BATTERY_IN_SERVICE: self.put_battery_in_service, TAKE_BATTERY_OUT_OF_SERVICE: self.take_battery_out_of_service,
        }

    @staticmethod
    def _resolve(payload: dict[str, Any], context: Any, *keys: str) -> dict[str, Any]:
        resolved = dict(payload)
        for key in keys:
            if resolved.get(key) is not None:
                resolved[key] = EndpointResolver.resolve(context, resolved[key])
        return resolved

    @staticmethod
    def _without(payload: dict[str, Any], *keys: str) -> dict[str, Any]:
        result = dict(payload)
        for key in keys:
            result.pop(key, None)
        return result

    def create_bus(self, command, context, transaction): return self._model_service.create_bus(transaction=transaction, **command.payload)
    def update_bus(self, command, context, transaction): return self._model_service.update_bus(transaction=transaction, **command.payload)
    def delete_bus(self, command, context, transaction): return self._model_service.delete_bus(transaction=transaction, **command.payload)
    def create_grid(self, command, context, transaction): return self._model_service.create_grid(transaction=transaction, **command.payload)
    def update_grid(self, command, context, transaction): return self._model_service.update_grid(transaction=transaction, **command.payload)
    def delete_grid(self, command, context, transaction): return self._model_service.delete_grid(transaction=transaction, **command.payload)
    def create_generator(self, command, context, transaction): return self._model_service.create_generator(transaction=transaction, **self._resolve(dict(command.payload), context, "endpoint"))
    def update_generator(self, command, context, transaction): return self._model_service.update_generator(transaction=transaction, **command.payload)
    def delete_generator(self, command, context, transaction): return self._model_service.delete_generator(transaction=transaction, **command.payload)
    def create_load(self, command, context, transaction): return self._model_service.create_load(transaction=transaction, **command.payload)
    def update_load(self, command, context, transaction): return self._model_service.update_load(transaction=transaction, **command.payload)
    def delete_load(self, command, context, transaction): return self._model_service.delete_load(transaction=transaction, **command.payload)
    def create_shunt(self, command, context, transaction): return self._model_service.create_shunt(transaction=transaction, **self._resolve(dict(command.payload), context, "endpoint"))
    def update_shunt(self, command, context, transaction): return self._model_service.update_shunt(transaction=transaction, **command.payload)
    def delete_shunt(self, command, context, transaction): return self._model_service.delete_shunt(transaction=transaction, **command.payload)
    def create_line(self, command, context, transaction): return self._model_service.create_line(transaction=transaction, **self._resolve(dict(command.payload), context, "endpoint_from", "endpoint_to"))
    def delete_line(self, command, context, transaction): return self._model_service.delete_line(transaction=transaction, **command.payload)
    def create_transformer(self, command, context, transaction): return self._model_service.create_transformer(transaction=transaction, **self._resolve(dict(command.payload), context, "endpoint_from", "endpoint_to"))
    def delete_transformer(self, command, context, transaction): return self._model_service.delete_transformer(transaction=transaction, **command.payload)
    def create_cable(self, command, context, transaction): return self._model_service.create_cable(transaction=transaction, **self._resolve(dict(command.payload), context, "endpoint_from", "endpoint_to"))
    def update_cable(self, command, context, transaction): return self._model_service.update_cable(transaction=transaction, **command.payload)
    def delete_cable(self, command, context, transaction): return self._model_service.delete_cable(transaction=transaction, **command.payload)

    def create_switch(self, command, context, transaction): return self._model_service.switching_service.create_switch(transaction=transaction, **self._resolve(dict(command.payload), context, "endpoint_a", "endpoint_b"))
    def update_switch(self, command, context, transaction): return self._model_service.switching_service.update_switch(transaction=transaction, **command.payload)
    def delete_switch(self, command, context, transaction): return self._model_service.switching_service.delete_switch(transaction=transaction, **command.payload)
    def open_switch(self, command, context, transaction): return self._model_service.switching_service.open_switch(transaction=transaction, **command.payload)
    def close_switch(self, command, context, transaction): return self._model_service.switching_service.close_switch(transaction=transaction, **command.payload)
    def put_switch_in_service(self, command, context, transaction): return self._model_service.switching_service.put_switch_in_service(transaction=transaction, **command.payload)
    def take_switch_out_of_service(self, command, context, transaction): return self._model_service.switching_service.take_switch_out_of_service(transaction=transaction, **command.payload)

    def create_breaker(self, command, context, transaction): return self._model_service.switching_service.create_breaker(transaction=transaction, **self._resolve(dict(command.payload), context, "endpoint_from", "endpoint_to"))
    def update_breaker(self, command, context, transaction): return self._model_service.switching_service.update_breaker(transaction=transaction, **command.payload)
    def delete_breaker(self, command, context, transaction): return self._model_service.switching_service.delete_breaker(transaction=transaction, **command.payload)
    def open_breaker(self, command, context, transaction): return self._model_service.switching_service.open_breaker(transaction=transaction, **command.payload)
    def close_breaker(self, command, context, transaction): return self._model_service.switching_service.close_breaker(transaction=transaction, **command.payload)
    def trip_breaker(self, command, context, transaction): return self._model_service.switching_service.trip_breaker(transaction=transaction, **command.payload)
    def put_breaker_in_service(self, command, context, transaction): return self._model_service.switching_service.put_breaker_in_service(transaction=transaction, **command.payload)
    def take_breaker_out_of_service(self, command, context, transaction): return self._model_service.switching_service.take_breaker_out_of_service(transaction=transaction, **command.payload)

    def create_disconnector(self, command, context, transaction): return self._model_service.switching_service.create_disconnector(transaction=transaction, **self._resolve(dict(command.payload), context, "endpoint_from", "endpoint_to"))
    def update_disconnector(self, command, context, transaction): return self._model_service.switching_service.update_disconnector(transaction=transaction, **command.payload)
    def delete_disconnector(self, command, context, transaction): return self._model_service.switching_service.delete_disconnector(transaction=transaction, **command.payload)
    def open_disconnector(self, command, context, transaction): return self._model_service.switching_service.open_disconnector(transaction=transaction, **command.payload)
    def close_disconnector(self, command, context, transaction): return self._model_service.switching_service.close_disconnector(transaction=transaction, **command.payload)
    def put_disconnector_in_service(self, command, context, transaction): return self._model_service.switching_service.put_disconnector_in_service(transaction=transaction, **command.payload)
    def take_disconnector_out_of_service(self, command, context, transaction): return self._model_service.switching_service.take_disconnector_out_of_service(transaction=transaction, **command.payload)
    def create_fuse(self, command, context, transaction): return self._model_service.switching_service.create_fuse(transaction=transaction, **command.payload)
    def update_fuse(self, command, context, transaction): return self._model_service.switching_service.update_fuse(transaction=transaction, **command.payload)
    def delete_fuse(self, command, context, transaction): return self._model_service.switching_service.delete_fuse(transaction=transaction, **command.payload)
    def blow_fuse(self, command, context, transaction): return self._model_service.switching_service.blow_fuse(transaction=transaction, **command.payload)
    def reset_fuse(self, command, context, transaction): return self._model_service.switching_service.reset_fuse(transaction=transaction, **command.payload)
    def put_fuse_in_service(self, command, context, transaction): return self._model_service.switching_service.put_fuse_in_service(transaction=transaction, **command.payload)
    def take_fuse_out_of_service(self, command, context, transaction): return self._model_service.switching_service.take_fuse_out_of_service(transaction=transaction, **command.payload)

    def create_capacitor(self, command, context, transaction): return self._model_service.shunt_service.create_capacitor(transaction=transaction, **self._resolve(dict(command.payload), context, "endpoint"))
    def update_capacitor(self, command, context, transaction): return self._model_service.shunt_service.update_capacitor(transaction=transaction, **self._resolve(dict(command.payload), context, "endpoint"))
    def delete_capacitor(self, command, context, transaction): return self._model_service.shunt_service.delete_capacitor(transaction=transaction, **command.payload)
    def put_capacitor_in_service(self, command, context, transaction): return self._model_service.shunt_service.put_capacitor_in_service(transaction=transaction, **command.payload)
    def take_capacitor_out_of_service(self, command, context, transaction): return self._model_service.shunt_service.take_capacitor_out_of_service(transaction=transaction, **command.payload)

    def create_current_transformer(self, command, context, transaction):
        p = dict(command.payload)
        for key in ("p1_endpoint", "p2_endpoint", "s1_endpoint", "s2_endpoint"):
            if p[key] is not None: p[key] = EndpointResolver.resolve(context, p[key])
        p["ct_id"] = p.pop("transformer_id")
        return self._model_service.measurement_service.create_current_transformer(transaction=transaction, **p)
    def update_current_transformer(self, command, context, transaction):
        p = dict(command.payload); p["ct_id"] = p.pop("transformer_id")
        return self._model_service.measurement_service.update_current_transformer(transaction=transaction, **p)
    def delete_current_transformer(self, command, context, transaction): return self._model_service.measurement_service.delete_current_transformer(ct_id=command.payload["transformer_id"], transaction=transaction)
    def put_current_transformer_in_service(self, command, context, transaction): return self._model_service.measurement_service.put_current_transformer_in_service(ct_id=command.payload["transformer_id"], transaction=transaction)
    def take_current_transformer_out_of_service(self, command, context, transaction): return self._model_service.measurement_service.take_current_transformer_out_of_service(ct_id=command.payload["transformer_id"], transaction=transaction)
    def create_capacitive_voltage_transformer(self, command, context, transaction):
        p = dict(command.payload)
        for key in ("h1_endpoint", "h2_endpoint", "x1_endpoint", "x2_endpoint"):
            if p[key] is not None: p[key] = EndpointResolver.resolve(context, p[key])
        p["cvt_id"] = p.pop("transformer_id")
        return self._model_service.measurement_service.create_capacitive_voltage_transformer(transaction=transaction, **p)
    def update_capacitive_voltage_transformer(self, command, context, transaction):
        p = dict(command.payload); p["cvt_id"] = p.pop("transformer_id")
        return self._model_service.measurement_service.update_capacitive_voltage_transformer(transaction=transaction, **p)
    def delete_capacitive_voltage_transformer(self, command, context, transaction): return self._model_service.measurement_service.delete_capacitive_voltage_transformer(cvt_id=command.payload["transformer_id"], transaction=transaction)
    def put_capacitive_voltage_transformer_in_service(self, command, context, transaction): return self._model_service.measurement_service.put_capacitive_voltage_transformer_in_service(cvt_id=command.payload["transformer_id"], transaction=transaction)
    def take_capacitive_voltage_transformer_out_of_service(self, command, context, transaction): return self._model_service.measurement_service.take_capacitive_voltage_transformer_out_of_service(cvt_id=command.payload["transformer_id"], transaction=transaction)

    def create_battery(self, command, context, transaction): return self._model_service.battery_service.create_battery(transaction=transaction, **self._resolve(dict(command.payload), context, "endpoint"))
    def update_battery(self, command, context, transaction): return self._model_service.battery_service.update_battery(transaction=transaction, **command.payload)
    def delete_battery(self, command, context, transaction): return self._model_service.battery_service.delete_battery(transaction=transaction, **command.payload)
    def put_battery_in_service(self, command, context, transaction): return self._model_service.battery_service.put_battery_in_service(transaction=transaction, **command.payload)
    def take_battery_out_of_service(self, command, context, transaction): return self._model_service.battery_service.take_battery_out_of_service(transaction=transaction, **command.payload)


def build_model_command_handlers(model_service: Any) -> Mapping[str, Handler]:
    return ModelCommandHandlers(model_service).handlers()


__all__ = ["ModelCommandHandlers", "build_model_command_handlers"]
