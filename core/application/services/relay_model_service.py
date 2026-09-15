"""Application service boundary for physical Relay lifecycle."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.errors import DomainError
from core.model.relay import Relay
from core.network.network import Network


class RelayModelService(ModelServiceSupport):
    """Own Application-layer mutations for physical Relay equipment."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    def create_relay(
        self,
        *,
        relay_id: str,
        relay_type: str,
        name: str = "",
        plugin_id: str | None = None,
        settings: Mapping[str, Any] | None = None,
        in_service: bool = True,
        enabled: bool = True,
        blocked: bool = False,
        transaction: Transaction,
    ) -> ApplicationResult[Relay]:
        self._require_transaction(transaction)
        self._require_id(relay_id, "relay_id")
        self._ensure_not_exists("relay", relay_id, "Relay")
        relay = Relay(
            id=relay_id,
            relay_type=relay_type,
            name=name,
            plugin_id=plugin_id,
            settings=settings,
            in_service=in_service,
            enabled=enabled,
            blocked=blocked,
        )
        self._network.add_relay(relay)
        transaction.record_undo(lambda relay=relay: self._network.remove_relay(relay))
        return self._success(relay, "relay", relay_id, f"Relay created: {relay_id}")

    def update_relay(
        self,
        *,
        relay_id: str,
        name: str | None = None,
        plugin_id: str | None = None,
        settings: Mapping[str, Any] | None = None,
        enabled: bool | None = None,
        blocked: bool | None = None,
        in_service: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Relay]:
        self._require_transaction(transaction)
        self._require_id(relay_id, "relay_id")
        relay = self._get_required("relay", relay_id, "Relay")
        self._require_type(relay, Relay, relay_id, "Relay")
        if all(value is None for value in (name, plugin_id, settings, enabled, blocked, in_service)):
            raise DomainError(code="NO_RELAY_UPDATE", message="At least one mutable Relay property must be specified.", details={"relay_id": relay_id})

        old = {
            "name": relay.name,
            "plugin_id": relay.plugin_id,
            "settings": deepcopy(relay.settings),
            "enabled": relay.enabled,
            "blocked": relay.blocked,
            "in_service": relay.in_service,
            "picked_up": relay.picked_up,
            "tripped": relay.tripped,
        }
        if name is not None:
            relay.name = name
        if plugin_id is not None:
            relay.plugin_id = relay._validate_identifier(plugin_id, "plugin_id")
        if settings is not None:
            relay.set_settings(settings)
        if enabled is not None:
            if not isinstance(enabled, bool):
                raise TypeError("enabled must be bool.")
            relay.enable() if enabled else relay.disable()
        if blocked is not None:
            if not isinstance(blocked, bool):
                raise TypeError("blocked must be bool.")
            relay.unblock() if not blocked else relay.block()
        if in_service is not None:
            if not isinstance(in_service, bool):
                raise TypeError("in_service must be bool.")
            relay.put_in_service() if in_service else relay.take_out_of_service()
        relay.validate()

        def restore() -> None:
            relay.name = old["name"]
            relay.plugin_id = old["plugin_id"]
            relay.set_settings(old["settings"])
            relay.in_service = old["in_service"]
            relay.enabled = old["enabled"]
            relay.blocked = old["blocked"]
            relay.picked_up = old["picked_up"]
            relay.tripped = old["tripped"]
            relay.validate()

        transaction.record_undo(restore)
        return self._success(relay, "relay", relay_id, f"Relay updated: {relay_id}")

    def delete_relay(self, *, relay_id: str, transaction: Transaction) -> ApplicationResult[Relay]:
        self._require_transaction(transaction)
        self._require_id(relay_id, "relay_id")
        relay = self._get_required("relay", relay_id, "Relay")
        self._require_type(relay, Relay, relay_id, "Relay")
        self._network.remove_relay(relay)
        transaction.record_undo(lambda relay=relay: self._network.add_relay(relay))
        return self._success(relay, "relay", relay_id, f"Relay deleted: {relay_id}")

    def put_relay_in_service(self, *, relay_id: str, transaction: Transaction) -> ApplicationResult[Relay]:
        return self._set_service(relay_id=relay_id, in_service=True, transaction=transaction)

    def take_relay_out_of_service(self, *, relay_id: str, transaction: Transaction) -> ApplicationResult[Relay]:
        return self._set_service(relay_id=relay_id, in_service=False, transaction=transaction)

    def _set_service(self, *, relay_id: str, in_service: bool, transaction: Transaction) -> ApplicationResult[Relay]:
        self._require_transaction(transaction)
        self._require_id(relay_id, "relay_id")
        relay = self._get_required("relay", relay_id, "Relay")
        self._require_type(relay, Relay, relay_id, "Relay")
        old = (relay.in_service, relay.picked_up, relay.tripped)
        relay.put_in_service() if in_service else relay.take_out_of_service()
        transaction.record_undo(lambda relay=relay, old=old: self._restore_service_state(relay, old))
        action = "put in service" if in_service else "taken out of service"
        return self._success(relay, "relay", relay_id, f"Relay {action}: {relay_id}")

    @staticmethod
    def _restore_service_state(relay: Relay, state: tuple[bool, bool, bool]) -> None:
        relay.in_service, relay.picked_up, relay.tripped = state
        relay.validate()


__all__ = ["RelayModelService"]
