"""Application service boundary for Shunt mutations."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.errors import DomainError
from core.model.bus import Bus
from core.model.shunt import Shunt
from core.model.terminal import Terminal
from core.network.network import Network


class ShuntModelService(ModelServiceSupport):
    """Owns Application-layer mutation use cases for Shunt."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    def create_shunt(
        self,
        *,
        shunt_id: str,
        name: str = "",
        endpoint: Bus | Terminal | None = None,
        g_pu: float = 0.0,
        b_pu: float = 0.0,
        in_service: bool = True,
        transaction: Transaction,
    ) -> ApplicationResult[Shunt]:
        self._require_transaction(transaction)
        self._require_id(shunt_id, "shunt_id")
        if endpoint is not None:
            self._validate_endpoint(endpoint, "endpoint")
        self._ensure_not_exists("shunt", shunt_id, "Shunt")
        shunt = Shunt(
            id=shunt_id,
            name=name,
            endpoint=endpoint,
            g_pu=g_pu,
            b_pu=b_pu,
            in_service=in_service,
        )
        self._network.add_shunt(shunt)
        transaction.record_undo(lambda shunt=shunt: self._network.remove_shunt(shunt))
        return self._success(shunt, "shunt", shunt_id, f"Shunt created: {shunt_id}")

    def update_shunt(
        self,
        *,
        shunt_id: str,
        name: str | None = None,
        g_pu: float | None = None,
        b_pu: float | None = None,
        in_service: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Shunt]:
        self._require_transaction(transaction)
        self._require_id(shunt_id, "shunt_id")
        shunt = self._get_required("shunt", shunt_id, "Shunt")
        self._require_type(shunt, Shunt, shunt_id, "Shunt")
        if all(v is None for v in (name, g_pu, b_pu, in_service)):
            raise DomainError(
                code="NO_SHUNT_UPDATE",
                message="At least one mutable Shunt property must be specified.",
                details={"shunt_id": shunt_id},
            )
        old = {
            "name": shunt.name,
            "g_pu": shunt.g_pu,
            "b_pu": shunt.b_pu,
            "in_service": shunt.in_service,
        }
        if name is not None:
            shunt.name = name
        if g_pu is not None:
            shunt.g_pu = g_pu
        if b_pu is not None:
            shunt.b_pu = b_pu
        if in_service is not None:
            shunt.set_in_service(in_service)

        def restore() -> None:
            shunt.name = old["name"]
            shunt.g_pu = old["g_pu"]
            shunt.b_pu = old["b_pu"]
            shunt.set_in_service(old["in_service"])

        transaction.record_undo(restore)
        return self._success(shunt, "shunt", shunt_id, f"Shunt updated: {shunt_id}")

    def delete_shunt(
        self,
        *,
        shunt_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[Shunt]:
        self._require_transaction(transaction)
        self._require_id(shunt_id, "shunt_id")
        shunt = self._get_required("shunt", shunt_id, "Shunt")
        self._require_type(shunt, Shunt, shunt_id, "Shunt")
        self._network.remove_shunt(shunt)
        transaction.record_undo(lambda shunt=shunt: self._network.add_shunt(shunt))
        return self._success(shunt, "shunt", shunt_id, f"Shunt deleted: {shunt_id}")


__all__ = ["ShuntModelService"]
