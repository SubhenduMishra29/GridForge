"""Immutable Application commands for Breaker lifecycle operations."""

from __future__ import annotations

from uuid import UUID, uuid4

from ..command import Command
from ..endpoint_reference import EndpointReference

CREATE_BREAKER = "model.create_breaker"
UPDATE_BREAKER = "model.update_breaker"
DELETE_BREAKER = "model.delete_breaker"
OPEN_BREAKER = "model.open_breaker"
CLOSE_BREAKER = "model.close_breaker"
TRIP_BREAKER = "model.trip_breaker"
PUT_BREAKER_IN_SERVICE = "model.put_breaker_in_service"
TAKE_BREAKER_OUT_OF_SERVICE = "model.take_breaker_out_of_service"


class CreateBreakerCommand(Command):
    def __init__(self, *, breaker_id: str, endpoint_from: EndpointReference | None = None, endpoint_to: EndpointReference | None = None, name: str = "", in_service: bool = True, closed: bool = True, failed: bool = False, voltage_kv: float | None = None, current_a: float | None = None, interrupting_ka: float | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if endpoint_from is not None and not isinstance(endpoint_from, EndpointReference): raise TypeError("endpoint_from must be an EndpointReference or None.")
        if endpoint_to is not None and not isinstance(endpoint_to, EndpointReference): raise TypeError("endpoint_to must be an EndpointReference or None.")
        super().__init__(command_type=CREATE_BREAKER, payload={"breaker_id": breaker_id, "endpoint_from": endpoint_from, "endpoint_to": endpoint_to, "name": name, "in_service": in_service, "closed": closed, "failed": failed, "voltage_kv": voltage_kv, "current_a": current_a, "interrupting_ka": interrupting_ka}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class UpdateBreakerCommand(Command):
    def __init__(self, *, breaker_id: str, name: str | None = None, in_service: bool | None = None, closed: bool | None = None, failed: bool | None = None, voltage_kv: float | None = None, current_a: float | None = None, interrupting_ka: float | None = None, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        if all(value is None for value in (name, in_service, closed, failed, voltage_kv, current_a, interrupting_ka)):
            raise ValueError("UpdateBreakerCommand requires at least one mutable Breaker field.")
        super().__init__(command_type=UPDATE_BREAKER, payload={"breaker_id": breaker_id, "name": name, "in_service": in_service, "closed": closed, "failed": failed, "voltage_kv": voltage_kv, "current_a": current_a, "interrupting_ka": interrupting_ka}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class DeleteBreakerCommand(Command):
    def __init__(self, *, breaker_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(command_type=DELETE_BREAKER, payload={"breaker_id": breaker_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class OpenBreakerCommand(Command):
    def __init__(self, *, breaker_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(command_type=OPEN_BREAKER, payload={"breaker_id": breaker_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class CloseBreakerCommand(Command):
    def __init__(self, *, breaker_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(command_type=CLOSE_BREAKER, payload={"breaker_id": breaker_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class TripBreakerCommand(Command):
    """Protection-originated breaker-trip intent; construction never mutates Core."""

    def __init__(
        self,
        *,
        breaker_id: str,
        protection_element_id: str | None = None,
        relay_id: str | None = None,
        decision_id: str | None = None,
        reason: str = "",
        timestamp: float | None = None,
        command_id: UUID | None = None,
        correlation_id: UUID | None = None,
        causation_id: UUID | None = None,
    ) -> None:
        if not isinstance(breaker_id, str) or not breaker_id.strip():
            raise ValueError("breaker_id must be a non-empty string.")
        for name, value in (("protection_element_id", protection_element_id), ("relay_id", relay_id), ("decision_id", decision_id)):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} must be None or a non-empty string.")
        if not isinstance(reason, str):
            raise TypeError("reason must be a string.")
        if timestamp is not None:
            timestamp = float(timestamp)
        payload = {
            "breaker_id": breaker_id.strip(),
            "protection_element_id": protection_element_id.strip() if protection_element_id else None,
            "relay_id": relay_id.strip() if relay_id else None,
            "decision_id": decision_id.strip() if decision_id else None,
            "reason": reason.strip(),
            "timestamp": timestamp,
        }
        super().__init__(command_type=TRIP_BREAKER, payload=payload, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class PutBreakerInServiceCommand(Command):
    def __init__(self, *, breaker_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(command_type=PUT_BREAKER_IN_SERVICE, payload={"breaker_id": breaker_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


class TakeBreakerOutOfServiceCommand(Command):
    def __init__(self, *, breaker_id: str, command_id: UUID | None = None, correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(command_type=TAKE_BREAKER_OUT_OF_SERVICE, payload={"breaker_id": breaker_id}, command_id=command_id or uuid4(), correlation_id=correlation_id, causation_id=causation_id)


__all__ = [
    "CREATE_BREAKER", "UPDATE_BREAKER", "DELETE_BREAKER", "OPEN_BREAKER", "CLOSE_BREAKER", "TRIP_BREAKER",
    "PUT_BREAKER_IN_SERVICE", "TAKE_BREAKER_OUT_OF_SERVICE", "CreateBreakerCommand", "UpdateBreakerCommand",
    "DeleteBreakerCommand", "OpenBreakerCommand", "CloseBreakerCommand", "TripBreakerCommand",
    "PutBreakerInServiceCommand", "TakeBreakerOutOfServiceCommand",
]
