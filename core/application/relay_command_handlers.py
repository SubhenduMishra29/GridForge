"""Application handlers for physical Relay lifecycle commands."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .commands.relay_commands import (
    CREATE_RELAY, UPDATE_RELAY, DELETE_RELAY,
    PUT_RELAY_IN_SERVICE, TAKE_RELAY_OUT_OF_SERVICE,
)


class RelayCommandHandlers:
    """Resolve Relay commands to the canonical RelayModelService."""

    def __init__(self, relay_service: Any) -> None:
        if relay_service is None:
            raise ValueError("relay_service is required.")
        self._relay_service = relay_service

    def handlers(self) -> Mapping[str, Any]:
        return {
            CREATE_RELAY: self.create_relay,
            UPDATE_RELAY: self.update_relay,
            DELETE_RELAY: self.delete_relay,
            PUT_RELAY_IN_SERVICE: self.put_relay_in_service,
            TAKE_RELAY_OUT_OF_SERVICE: self.take_relay_out_of_service,
        }

    @staticmethod
    def _payload(command) -> dict[str, Any]:
        payload = dict(command.payload)
        payload.pop("element_id", None)
        return payload

    def create_relay(self, command, context, transaction):
        return self._relay_service.create_relay(transaction=transaction, **self._payload(command))

    def update_relay(self, command, context, transaction):
        return self._relay_service.update_relay(transaction=transaction, **self._payload(command))

    def delete_relay(self, command, context, transaction):
        return self._relay_service.delete_relay(transaction=transaction, **self._payload(command))

    def put_relay_in_service(self, command, context, transaction):
        return self._relay_service.put_relay_in_service(transaction=transaction, **self._payload(command))

    def take_relay_out_of_service(self, command, context, transaction):
        return self._relay_service.take_relay_out_of_service(transaction=transaction, **self._payload(command))


__all__ = ["RelayCommandHandlers"]
