"""Canonical Application-owned draft service for the optional motor extension.

Author: Subhendu Mishra

This module has no Qt dependency. Motor placement and Bus connectivity are
recorded in DraftNetwork and pass through the existing Application transaction.
"""
from __future__ import annotations

from typing import Any, Mapping
from uuid import uuid4

from core.application.draft.network import DraftConnection, DraftEndpointReference, DraftEquipment
from core.application.results import ApplicationResult

ADD_DRAFT_MOTOR_PLACEMENT = "motor.add_draft_placement"
CONNECT_MOTOR_TO_BUS = "motor.connect_to_bus"


class MotorDraftService:
    def __init__(self, application: Any) -> None:
        if application is None:
            raise ValueError("Application is required.")
        self._application = application

    def _draft(self):
        draft = self._application.draft_network
        if draft is None:
            raise RuntimeError("Motor placement requires an active Application DraftNetwork.")
        return draft

    @staticmethod
    def _record_undo(draft: Any, transaction: Any) -> None:
        snapshot = draft.to_dict()
        transaction.record_undo(
            lambda snapshot=snapshot, draft=draft: draft.restore_snapshot(snapshot)
        )

    def add_draft_motor(self, *, command: Any, context: Any, transaction: Any) -> ApplicationResult[Any]:
        draft = self._draft()
        payload = command.payload
        motor_id = payload.get("motor_id")
        if not isinstance(motor_id, str) or not motor_id.strip():
            raise ValueError("Motor draft identity must be a non-empty string.")
        motor_id = motor_id.strip()
        contract = self._application.creation_contract_registry.resolve("motor")
        parameters = payload.get("parameters", {})
        if not isinstance(parameters, Mapping):
            raise TypeError("Motor parameters must be a mapping.")
        allowed_parameters = {
            str(item.get("parameter_id"))
            for item in contract.get("parameter_contract", ())
            if isinstance(item, Mapping)
        }
        unknown = set(parameters) - allowed_parameters
        if unknown:
            raise ValueError("Unsupported motor engineering parameters: " + ", ".join(sorted(unknown)))
        equipment = DraftEquipment(
            draft_id=motor_id,
            equipment_type="motor",
            display_name="Motor",
            terminal_contract=tuple(contract.get("terminal_contract", ())),
            engineering_data=dict(parameters),
            placement=(float(payload["x"]), float(payload["y"])),
            presentation={"symbol_type": "motor"},
            command_type=str(contract["command_type"]),
            id_field=str(contract["id_field"]),
            parameter_mapping=dict(contract.get("parameter_mapping", {})),
            endpoint_mapping=dict(contract.get("endpoint_mapping", {})),
            required_connection_terminals=tuple(contract.get("required_connection_terminals", ())),
            parameter_contract=tuple(contract.get("parameter_contract", ())),
            conditional_requirements=tuple(contract.get("conditional_requirements", ())),
        )
        self._record_undo(draft, transaction)
        draft.add_equipment(equipment)
        return ApplicationResult.success_result(value={"draft_id": motor_id, "equipment_type": "motor"})

    def connect_motor_to_bus(self, *, command: Any, context: Any, transaction: Any) -> ApplicationResult[Any]:
        draft = self._draft()
        payload = command.payload
        motor_id = str(payload.get("motor_id", "")).strip()
        bus_id = str(payload.get("bus_id", "")).strip()
        attachment_id = str(payload.get("attachment_id", "")).strip()
        motor = draft.require_equipment(motor_id)
        if motor.equipment_type != "motor":
            raise ValueError(f"Draft equipment {motor_id!r} is not a motor.")
        draft_bus = next((item for item in draft.equipment if item.draft_id == bus_id), None)
        if draft_bus is not None:
            if draft_bus.equipment_type != "bus":
                raise ValueError(f"Draft endpoint {bus_id!r} is not a Bus.")
            bus_endpoint = DraftEndpointReference.bus(
                bus_id=bus_id, attachment_id=attachment_id, scope="draft"
            )
        else:
            bus_endpoint = DraftEndpointReference.bus(
                bus_id=bus_id, attachment_id=attachment_id, scope="core"
            )
        connection = DraftConnection(
            connection_id="motor-wire-" + uuid4().hex,
            source=DraftEndpointReference.terminal(
                draft_id=motor_id, equipment_type="motor", terminal_role="terminal"
            ),
            target=bus_endpoint,
            connection_kind="simple_wire",
        )
        draft.validate_connection_candidate(connection)
        self._record_undo(draft, transaction)
        draft.add_connection(connection)
        return ApplicationResult.success_result(
            value={"connection_id": connection.connection_id, "motor_id": motor_id, "bus_id": bus_id}
        )


class MotorDynamicsComposition:
    """Application-owned adapter for optional plugin command registration."""

    def __init__(self, application: Any) -> None:
        self.application = application
        self.motor_service = MotorDraftService(application)

    def register_motor_extension(self, *, plugin: Any, command_handlers: Mapping[str, Any]):
        plugin_id = getattr(plugin, "plugin_id", None)
        if not isinstance(plugin_id, str) or not plugin_id.strip():
            raise ValueError("Motor extension plugin must expose a stable plugin_id.")
        expected = {ADD_DRAFT_MOTOR_PLACEMENT, CONNECT_MOTOR_TO_BUS}
        if set(command_handlers) != expected:
            raise ValueError("Motor extension must register exactly its two motor command handlers.")
        if any(not callable(handler) for handler in command_handlers.values()):
            raise TypeError("Motor extension handlers must be callable.")
        self.application.register_extension_handler_factory(
            plugin_id,
            lambda _command_manager, handlers=dict(command_handlers): dict(handlers),
        )
        def teardown() -> None:
            self.application.unregister_extension_handler_factory(plugin_id)
        return teardown


__all__ = ["ADD_DRAFT_MOTOR_PLACEMENT", "CONNECT_MOTOR_TO_BUS", "MotorDraftService", "MotorDynamicsComposition"]
