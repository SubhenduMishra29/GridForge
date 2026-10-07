# ============================================================
# GridForge V2 — Electrical Equipment Insertion Service
# ============================================================

"""Application transaction service for series equipment insertion."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from core.model import EndpointReference
from core.model.endpoint_reference import EquipmentType
from core.network import EndpointCompatibility, EndpointCompatibilityError

from ..command import Command
from ..commands.breaker_commands import CreateBreakerCommand
from ..commands.measurement_commands import CreateCurrentTransformerCommand
from ..commands.model_commands import CreateDisconnectorCommand, CreateTransformerCommand
from ..commands.simple_wire_commands import CreateSimpleWireConnectionCommand, RemoveSimpleWireConnectionCommand
from ..errors import ValidationError
from ..results import ApplicationResult
from ..transaction import Transaction
from .insertion_contract import INSERTION_CONTRACTS, InsertionContract

CommandExecutor = Callable[[Command, Transaction], ApplicationResult[Any]]


class ElectricalInsertionService:
    """Own the complete Application-side insertion workflow.

    Core topology remains owned by Network/ConnectivityStore. SLD mutation is
    coordinated by Application's pre-commit hook from the returned immutable
    insertion metadata.
    """

    def __init__(self, *, command_executor: CommandExecutor) -> None:
        if not callable(command_executor):
            raise TypeError("command_executor must be callable.")
        self._command_executor = command_executor

    def execute(
        self,
        command: Command,
        context: Any,
        transaction: Transaction,
    ) -> ApplicationResult[Any]:
        if not isinstance(transaction, Transaction):
            raise TypeError("transaction must be a Transaction.")
        network = getattr(context, "network", None)
        if network is None:
            raise RuntimeError("Electrical insertion requires the canonical Network.")

        payload = command.payload
        equipment_type = str(payload["equipment_type"]).strip().lower()
        contract = INSERTION_CONTRACTS.get(equipment_type)
        if contract is None:
            raise ValidationError(
                code="EQUIPMENT_NOT_INSERTION_CAPABLE",
                message=f"Equipment type {equipment_type!r} is not insertion-capable.",
                details={"equipment_type": equipment_type},
            )

        connection_id = str(payload["connection_id"])
        connection = network.get_simple_wire_connection(connection_id)
        endpoint_a = connection.endpoint_a
        endpoint_b = connection.endpoint_b
        if endpoint_a == endpoint_b:
            raise ValidationError(
                code="INVALID_INSERTION_CONNECTION",
                message="The target Simple Wire must have two distinct endpoints.",
                details={"connection_id": connection_id},
            )

        requested_equipment_id = payload.get("equipment_id")
        equipment_id = (
            str(requested_equipment_id).strip()
            if requested_equipment_id is not None
            else f"insert-{command.command_id.hex}"
        )
        try:
            network.get_by_identity(equipment_id)
        except KeyError:
            pass
        else:
            raise ValidationError(
                code="EQUIPMENT_ID_ALREADY_EXISTS",
                message=f"Equipment identity {equipment_id!r} already exists.",
                details={"equipment_id": equipment_id},
            )

        mapping = payload.get("terminal_mapping")
        terminal_mapping = (
            tuple(mapping)
            if mapping is not None
            else contract.terminal_mapping
        )
        if tuple(terminal_mapping) != contract.terminal_mapping:
            raise ValidationError(
                code="UNSUPPORTED_TERMINAL_MAPPING",
                message=(
                    f"{equipment_type!r} insertion requires terminal mapping "
                    f"{contract.terminal_mapping!r}."
                ),
                details={
                    "equipment_type": equipment_type,
                    "requested_mapping": tuple(terminal_mapping),
                    "required_mapping": contract.terminal_mapping,
                },
            )

        parameters = dict(payload.get("creation_parameters") or {})
        forbidden = {
            "endpoint", "endpoint_from", "endpoint_to", "endpoint_a", "endpoint_b",
            "p1_endpoint", "p2_endpoint", "s1_endpoint", "s2_endpoint",
        }
        if forbidden.intersection(parameters):
            raise ValidationError(
                code="INSERTION_ENDPOINT_OVERRIDE",
                message="Insertion creation parameters cannot override terminal endpoints.",
                details={"fields": sorted(forbidden.intersection(parameters))},
            )
        missing = tuple(
            field for field in contract.required_parameters
            if parameters.get(field) is None
        )
        if missing:
            raise ValidationError(
                code="MISSING_ENGINEERING_PARAMETERS",
                message=(
                    f"{equipment_type!r} insertion is missing required "
                    f"engineering parameters: {', '.join(missing)}."
                ),
                details={"equipment_type": equipment_type, "missing": missing},
            )

        insertion_position = tuple(payload["insertion_position"])
        if len(insertion_position) != 2:
            raise ValidationError(
                code="INVALID_INSERTION_POSITION",
                message="Insertion position must contain exactly two coordinates.",
                details={},
            )

        # The first mapped terminal is connected to the first side of the
        # existing relationship; the second mapped terminal is connected to
        # the second side. The explicit mapping is the engineering contract,
        # not a UI terminal-name guess.
        input_role, output_role = terminal_mapping
        equipment_type_enum = EquipmentType(equipment_type)
        input_ref = EndpointReference.terminal(
            equipment_type=equipment_type_enum,
            equipment_id=equipment_id,
            terminal_role=input_role,
        )
        output_ref = EndpointReference.terminal(
            equipment_type=equipment_type_enum,
            equipment_id=equipment_id,
            terminal_role=output_role,
        )

        # Create the equipment disconnected first. Its own canonical model
        # command remains the authoritative equipment-creation pathway.
        create_command = self._creation_command(
            equipment_type=equipment_type,
            equipment_id=equipment_id,
            parameters=parameters,
            command=command,
        )
        create_result = self._command_executor(create_command, transaction)
        if not create_result.success:
            raise ValidationError(
                code="EQUIPMENT_CREATION_FAILED",
                message=create_result.message or "Equipment creation failed.",
                details=dict(create_result.metadata),
            )

        # Remove the original relationship before creating either replacement.
        remove_result = self._command_executor(
            RemoveSimpleWireConnectionCommand(
                connection_id=connection_id,
                endpoint_a=endpoint_a,
                endpoint_b=endpoint_b,
                correlation_id=command.correlation_id,
                causation_id=command.command_id,
            ),
            transaction,
        )
        if not remove_result.success:
            raise ValidationError(
                code="INSERTION_ORIGINAL_CONNECTION_REMOVE_FAILED",
                message=remove_result.message or "Original connection removal failed.",
                details=dict(remove_result.metadata),
            )

        first_connection_id = f"{connection_id}-A"
        second_connection_id = f"{connection_id}-B"
        if first_connection_id == second_connection_id:
            raise ValidationError(code="INSERTION_CONNECTION_ID_COLLISION", message="Replacement connection IDs collide.", details={})

        first_result = self._command_executor(
            CreateSimpleWireConnectionCommand(
                connection_id=first_connection_id,
                endpoint_a=endpoint_a,
                endpoint_b=input_ref,
                correlation_id=command.correlation_id,
                causation_id=command.command_id,
            ),
            transaction,
        )
        if not first_result.success:
            raise ValidationError(
                code="INSERTION_FIRST_CONNECTION_FAILED",
                message=first_result.message or "First replacement connection failed.",
                details=dict(first_result.metadata),
            )

        second_result = self._command_executor(
            CreateSimpleWireConnectionCommand(
                connection_id=second_connection_id,
                endpoint_a=output_ref,
                endpoint_b=endpoint_b,
                correlation_id=command.correlation_id,
                causation_id=command.command_id,
            ),
            transaction,
        )
        if not second_result.success:
            raise ValidationError(
                code="INSERTION_SECOND_CONNECTION_FAILED",
                message=second_result.message or "Second replacement connection failed.",
                details=dict(second_result.metadata),
            )

        # Validate the authoritative aggregate before the outer transaction can
        # commit. The original direct relationship must be gone.
        if network.connectivity.contains(connection_id):
            raise ValidationError(
                code="INSERTION_DIRECT_CONNECTION_REMAINS",
                message="The original Simple Wire remains after insertion.",
                details={"connection_id": connection_id},
            )
        if not network.connectivity.contains(first_connection_id) or not network.connectivity.contains(second_connection_id):
            raise ValidationError(
                code="INSERTION_REPLACEMENT_CONNECTION_MISSING",
                message="Insertion did not produce both replacement Simple Wires.",
                details={
                    "first_connection_id": first_connection_id,
                    "second_connection_id": second_connection_id,
                },
            )

        try:
            network.connectivity.validate(network)
            network.validate()
        except Exception as exc:
            raise ValidationError(
                code="INSERTION_TOPOLOGY_INVALID",
                message=f"Inserted topology failed Core validation: {exc}",
                details={"connection_id": connection_id, "equipment_id": equipment_id},
            ) from exc

        return ApplicationResult.success_result(
            value=create_result.value,
            message=f"{equipment_type.title()} {equipment_id} inserted into {connection_id}.",
            metadata={
                "insertion": True,
                "connection_id": connection_id,
                "equipment_type": equipment_type,
                "equipment_id": equipment_id,
                "insertion_position": insertion_position,
                "orientation": float(payload["orientation"]),
                "segment_index": int(payload["segment_index"]),
                "terminal_mapping": tuple(terminal_mapping),
                "endpoint_a": dict(endpoint_a.to_mapping()),
                "endpoint_b": dict(endpoint_b.to_mapping()),
                "input_endpoint": dict(input_ref.to_mapping()),
                "output_endpoint": dict(output_ref.to_mapping()),
                "replacement_connection_ids": (first_connection_id, second_connection_id),
                "sld_node_id": f"sld-core-{equipment_id}",
                "sld_connection_ids": (
                    f"sld-wire-{first_connection_id}",
                    f"sld-wire-{second_connection_id}",
                ),
            },
        )

    @staticmethod
    def _creation_command(
        *,
        equipment_type: str,
        equipment_id: str,
        parameters: Mapping[str, Any],
        command: Command,
    ) -> Command:
        common = dict(
            parameters,
            command_id=None,
            correlation_id=command.correlation_id,
            causation_id=command.command_id,
        )
        if equipment_type == "breaker":
            return CreateBreakerCommand(
                breaker_id=equipment_id,
                **common,
            )
        if equipment_type == "disconnector":
            return CreateDisconnectorCommand(
                disconnector_id=equipment_id,
                **common,
            )
        if equipment_type == "transformer":
            return CreateTransformerCommand(
                transformer_id=equipment_id,
                **common,
            )
        if equipment_type == "current_transformer":
            return CreateCurrentTransformerCommand(
                transformer_id=equipment_id,
                **common,
            )
        raise ValueError(f"Unsupported insertion-capable equipment type: {equipment_type!r}")


class ElectricalInsertionCommandHandlers:
    """Register the insertion command in the single Application registry."""

    def __init__(self, service: ElectricalInsertionService) -> None:
        if not isinstance(service, ElectricalInsertionService):
            raise TypeError("service must be an ElectricalInsertionService.")
        self._service = service

    def handlers(self) -> dict[str, Any]:
        from ..commands.insertion_commands import INSERT_EQUIPMENT_INTO_CONNECTION
        return {INSERT_EQUIPMENT_INTO_CONNECTION: self.execute}

    def execute(self, command: Command, context: Any, transaction: Transaction) -> ApplicationResult:
        return self._service.execute(command, context, transaction)


__all__ = [
    "ElectricalInsertionService",
    "ElectricalInsertionCommandHandlers",
]
