"""Application service boundary for Load mutations."""

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.errors import DomainError
from core.model.load import Load
from core.network.network import Network


class LoadModelService(ModelServiceSupport):
    """Owns Application-layer mutation use cases for Load objects."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    def create_load(
        self,
        *,
        load_id: str,
        p: float = 0.0,
        q: float = 0.0,
        name: str | None = None,
        in_service: bool = True,
        transaction: Transaction,
    ) -> ApplicationResult[Load]:
        self._require_transaction(transaction)
        self._require_id(load_id, "load_id")
        self._ensure_not_exists("load", load_id, "Load")
        load = Load(
            id=load_id,
            p=p,
            q=q,
            name="" if name is None else name,
            in_service=in_service,
        )
        self._network.add_load(load)
        transaction.record_undo(lambda load=load: self._network.remove_load(load))
        return self._success(load, "load", load_id, f"Load created: {load_id}")

    def update_load(
        self,
        *,
        load_id: str,
        name: str | None = None,
        p: float | None = None,
        q: float | None = None,
        in_service: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Load]:
        self._require_transaction(transaction)
        self._require_id(load_id, "load_id")
        load = self._get_required("load", load_id, "Load")
        self._require_type(load, Load, load_id, "Load")
        if all(v is None for v in (name, p, q, in_service)):
            raise DomainError(
                code="NO_LOAD_UPDATE",
                message="At least one mutable Load property must be specified.",
                details={"load_id": load_id},
            )

        old = {
            "name": load.name,
            "p": load.p,
            "q": load.q,
            "in_service": load.in_service,
        }
        if name is not None:
            load.name = name
        if p is not None:
            load.p = p
        if q is not None:
            load.q = q
        if in_service is not None:
            load.set_in_service(in_service)

        def restore() -> None:
            load.name = old["name"]
            load.p = old["p"]
            load.q = old["q"]
            load.set_in_service(old["in_service"])

        transaction.record_undo(restore)
        return self._success(load, "load", load_id, f"Load updated: {load_id}")

    def delete_load(
        self,
        *,
        load_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[Load]:
        self._require_transaction(transaction)
        self._require_id(load_id, "load_id")
        load = self._get_required("load", load_id, "Load")
        self._require_type(load, Load, load_id, "Load")
        self._network.remove_load(load)
        transaction.record_undo(lambda load=load: self._network.add_load(load))
        return self._success(load, "load", load_id, f"Load deleted: {load_id}")


__all__ = ["LoadModelService"]
