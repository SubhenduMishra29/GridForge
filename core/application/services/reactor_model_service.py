"""Application service boundary for Reactor mutations."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.errors import DomainError
from core.model.bus import Bus
from core.model.reactor import Reactor
from core.model.terminal import Terminal
from core.network.network import Network


class ReactorModelService(ModelServiceSupport):
    """Owns Application-layer mutation use cases for Reactor objects."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    def create_reactor(
        self,
        *,
        reactor_id: str,
        endpoint: Bus | Terminal | None = None,
        name: str = "",
        reactive_power_injection_mvar: float = -10.0,
        in_service: bool = True,
        transaction: Transaction,
    ) -> ApplicationResult[Reactor]:
        self._require_transaction(transaction)
        self._require_id(reactor_id, "reactor_id")
        if endpoint is not None:
            self._validate_endpoint(endpoint, "endpoint")
        self._ensure_not_exists("reactor", reactor_id, "Reactor")
        reactor = Reactor(
            id=reactor_id,
            name=name,
            bus=endpoint,
            reactive_power_injection_mvar=reactive_power_injection_mvar,
            in_service=in_service,
        )
        self._network.add_reactor(reactor)
        transaction.record_undo(lambda reactor=reactor: self._network.remove_reactor(reactor))
        return self._success(reactor, "reactor", reactor_id, f"Reactor created: {reactor_id}")

    def update_reactor(
        self,
        *,
        reactor_id: str,
        name: str | None = None,
        reactive_power_injection_mvar: float | None = None,
        in_service: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Reactor]:
        self._require_transaction(transaction)
        self._require_id(reactor_id, "reactor_id")
        reactor = self._get_required("reactor", reactor_id, "Reactor")
        self._require_type(reactor, Reactor, reactor_id, "Reactor")
        if all(value is None for value in (name, reactive_power_injection_mvar, in_service)):
            raise DomainError(
                code="NO_REACTOR_UPDATE",
                message="At least one mutable Reactor property must be specified.",
                details={"reactor_id": reactor_id},
            )

        old = {
            "name": reactor.name,
            "reactive_power_injection_mvar": reactor.reactive_power_injection_mvar,
            "in_service": reactor.in_service,
        }
        try:
            if name is not None:
                reactor.name = name
            if reactive_power_injection_mvar is not None:
                reactor.reactive_power_injection_mvar = reactive_power_injection_mvar
            if in_service is not None:
                reactor.in_service = in_service
            reactor.validate_parameters()
        except Exception:
            reactor.name = old["name"]
            reactor.reactive_power_injection_mvar = old["reactive_power_injection_mvar"]
            reactor.in_service = old["in_service"]
            raise

        def restore() -> None:
            reactor.name = old["name"]
            reactor.reactive_power_injection_mvar = old["reactive_power_injection_mvar"]
            reactor.in_service = old["in_service"]
            reactor.validate_parameters()

        transaction.record_undo(restore)
        return self._success(reactor, "reactor", reactor_id, f"Reactor updated: {reactor_id}")

    def delete_reactor(
        self,
        *,
        reactor_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[Reactor]:
        self._require_transaction(transaction)
        self._require_id(reactor_id, "reactor_id")
        reactor = self._get_required("reactor", reactor_id, "Reactor")
        self._require_type(reactor, Reactor, reactor_id, "Reactor")
        self._network.remove_reactor(reactor)
        transaction.record_undo(lambda reactor=reactor: self._network.add_reactor(reactor))
        return self._success(reactor, "reactor", reactor_id, f"Reactor deleted: {reactor_id}")


__all__ = ["ReactorModelService"]
