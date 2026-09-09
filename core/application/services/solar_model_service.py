"""Application service boundary for Solar mutations."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.errors import DomainError
from core.model.bus import Bus
from core.model.solar import Solar
from core.model.terminal import Terminal
from core.network.network import Network


class SolarModelService(ModelServiceSupport):
    """Owns Application-layer mutation use cases for Solar objects."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    def create_solar(
        self,
        *,
        solar_id: str,
        endpoint: Bus | Terminal | None = None,
        name: str = "",
        p_mw: float = 0.0,
        q_mvar: float = 0.0,
        p_max_mw: float | None = None,
        p_min_mw: float = 0.0,
        q_max_mvar: float | None = None,
        q_min_mvar: float | None = None,
        in_service: bool = True,
        transaction: Transaction,
    ) -> ApplicationResult[Solar]:
        self._require_transaction(transaction)
        self._require_id(solar_id, "solar_id")
        if endpoint is not None:
            self._validate_endpoint(endpoint, "endpoint")
        self._ensure_not_exists("solar", solar_id, "Solar")
        solar = Solar(
            id=solar_id,
            name=name,
            endpoint=endpoint,
            p_mw=p_mw,
            q_mvar=q_mvar,
            p_max_mw=p_max_mw,
            p_min_mw=p_min_mw,
            q_max_mvar=q_max_mvar,
            q_min_mvar=q_min_mvar,
            in_service=in_service,
        )
        self._network.add_solar(solar)
        transaction.record_undo(lambda solar=solar: self._network.remove_solar(solar))
        return self._success(solar, "solar", solar_id, f"Solar created: {solar_id}")

    def update_solar(
        self,
        *,
        solar_id: str,
        name: str | None = None,
        p_mw: float | None = None,
        q_mvar: float | None = None,
        p_max_mw: float | None = None,
        p_min_mw: float | None = None,
        q_max_mvar: float | None = None,
        q_min_mvar: float | None = None,
        in_service: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Solar]:
        self._require_transaction(transaction)
        self._require_id(solar_id, "solar_id")
        solar = self._get_required("solar", solar_id, "Solar")
        self._require_type(solar, Solar, solar_id, "Solar")
        values = (name, p_mw, q_mvar, p_max_mw, p_min_mw, q_max_mvar, q_min_mvar, in_service)
        if all(value is None for value in values):
            raise DomainError(
                code="NO_SOLAR_UPDATE",
                message="At least one mutable Solar property must be specified.",
                details={"solar_id": solar_id},
            )

        old = {
            "name": solar.name,
            "p_mw": solar.p_mw,
            "q_mvar": solar.q_mvar,
            "p_max_mw": solar.p_max_mw,
            "p_min_mw": solar.p_min_mw,
            "q_max_mvar": solar.q_max_mvar,
            "q_min_mvar": solar.q_min_mvar,
            "in_service": solar.in_service,
        }
        try:
            if name is not None:
                solar.name = name
            if p_mw is not None:
                solar.p_mw = p_mw
            if q_mvar is not None:
                solar.q_mvar = q_mvar
            if p_min_mw is not None:
                solar.p_min_mw = p_min_mw
            if p_max_mw is not None:
                solar.p_max_mw = p_max_mw
            if q_min_mvar is not None:
                solar.q_min_mvar = q_min_mvar
            if q_max_mvar is not None:
                solar.q_max_mvar = q_max_mvar
            if in_service is not None:
                solar.set_in_service(in_service)
            solar.validate_parameters()
        except Exception:
            solar.name = old["name"]
            solar.p_mw = old["p_mw"]
            solar.q_mvar = old["q_mvar"]
            solar.p_max_mw = old["p_max_mw"]
            solar.p_min_mw = old["p_min_mw"]
            solar.q_max_mvar = old["q_max_mvar"]
            solar.q_min_mvar = old["q_min_mvar"]
            solar.in_service = old["in_service"]
            raise

        def restore() -> None:
            solar.name = old["name"]
            solar.p_mw = old["p_mw"]
            solar.q_mvar = old["q_mvar"]
            solar.p_max_mw = old["p_max_mw"]
            solar.p_min_mw = old["p_min_mw"]
            solar.q_max_mvar = old["q_max_mvar"]
            solar.q_min_mvar = old["q_min_mvar"]
            solar.in_service = old["in_service"]
            solar.validate_parameters()

        transaction.record_undo(restore)
        return self._success(solar, "solar", solar_id, f"Solar updated: {solar_id}")

    def delete_solar(
        self,
        *,
        solar_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[Solar]:
        self._require_transaction(transaction)
        self._require_id(solar_id, "solar_id")
        solar = self._get_required("solar", solar_id, "Solar")
        self._require_type(solar, Solar, solar_id, "Solar")
        self._network.remove_solar(solar)
        transaction.record_undo(lambda solar=solar: self._network.add_solar(solar))
        return self._success(solar, "solar", solar_id, f"Solar deleted: {solar_id}")


__all__ = ["SolarModelService"]
