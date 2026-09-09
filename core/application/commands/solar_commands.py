"""Immutable Application commands for Solar mutations."""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from ..command import Command
from ..endpoint_reference import EndpointReference

CREATE_SOLAR = "model.create_solar"
UPDATE_SOLAR = "model.update_solar"
DELETE_SOLAR = "model.delete_solar"


def _command(command_type: str, payload: dict[str, Any], *, command_id: UUID | None = None,
             correlation_id: UUID | None = None, causation_id: UUID | None = None) -> dict[str, Any]:
    return {"command_type": command_type, "payload": payload, "command_id": command_id or uuid4(),
            "correlation_id": correlation_id, "causation_id": causation_id}


def _endpoint(value: EndpointReference | None, name: str) -> None:
    if value is not None and not isinstance(value, EndpointReference):
        raise TypeError(f"{name} must be an EndpointReference or None.")


class CreateSolarCommand(Command):
    def __init__(self, *, solar_id: str, endpoint: EndpointReference | None = None,
                 name: str = "", p_mw: float = 0.0, q_mvar: float = 0.0,
                 p_max_mw: float | None = None, p_min_mw: float = 0.0,
                 q_max_mvar: float | None = None, q_min_mvar: float | None = None,
                 in_service: bool = True, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        _endpoint(endpoint, "endpoint")
        super().__init__(**_command(
            CREATE_SOLAR,
            {"solar_id": solar_id, "endpoint": endpoint, "name": name, "p_mw": p_mw,
             "q_mvar": q_mvar, "p_max_mw": p_max_mw, "p_min_mw": p_min_mw,
             "q_max_mvar": q_max_mvar, "q_min_mvar": q_min_mvar, "in_service": in_service},
            command_id=command_id, correlation_id=correlation_id, causation_id=causation_id,
        ))


class UpdateSolarCommand(Command):
    def __init__(self, *, solar_id: str, name: str | None = None,
                 p_mw: float | None = None, q_mvar: float | None = None,
                 p_max_mw: float | None = None, p_min_mw: float | None = None,
                 q_max_mvar: float | None = None, q_min_mvar: float | None = None,
                 in_service: bool | None = None, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        values = (name, p_mw, q_mvar, p_max_mw, p_min_mw, q_max_mvar, q_min_mvar, in_service)
        if all(value is None for value in values):
            raise ValueError("UpdateSolarCommand requires at least one mutable field.")
        super().__init__(**_command(
            UPDATE_SOLAR,
            {"solar_id": solar_id, "name": name, "p_mw": p_mw, "q_mvar": q_mvar,
             "p_max_mw": p_max_mw, "p_min_mw": p_min_mw, "q_max_mvar": q_max_mvar,
             "q_min_mvar": q_min_mvar, "in_service": in_service},
            command_id=command_id, correlation_id=correlation_id, causation_id=causation_id,
        ))


class DeleteSolarCommand(Command):
    def __init__(self, *, solar_id: str, command_id: UUID | None = None,
                 correlation_id: UUID | None = None, causation_id: UUID | None = None) -> None:
        super().__init__(**_command(
            DELETE_SOLAR,
            {"solar_id": solar_id},
            command_id=command_id, correlation_id=correlation_id, causation_id=causation_id,
        ))


__all__ = ["CREATE_SOLAR", "UPDATE_SOLAR", "DELETE_SOLAR", "CreateSolarCommand", "UpdateSolarCommand", "DeleteSolarCommand"]
