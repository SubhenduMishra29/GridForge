"""Application service boundary for Cable mutations."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.errors import DomainError
from core.model.bus import Bus
from core.model.cable import Cable
from core.model.terminal import Terminal
from core.network.network import Network


class CableModelService(ModelServiceSupport):
    """Owns Application-layer mutation use cases for Cable."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    def create_cable(
        self,
        *,
        cable_id: str,
        endpoint_from: Bus | Terminal | None = None,
        endpoint_to: Bus | Terminal | None = None,
        name: str = "",
        length_km: float = 0.0,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        r1_ohm_per_km: float = 0.0,
        x1_ohm_per_km: float = 0.0,
        b1_us_per_km: float = 0.0,
        r0_ohm_per_km: float | None = None,
        x0_ohm_per_km: float | None = None,
        b0_us_per_km: float | None = None,
        in_service: bool = True,
        transaction: Transaction,
    ) -> ApplicationResult[Cable]:
        self._require_transaction(transaction)
        self._require_id(cable_id, "cable_id")
        if endpoint_from is not None:
            self._validate_endpoint(endpoint_from, "endpoint_from")
        if endpoint_to is not None:
            self._validate_endpoint(endpoint_to, "endpoint_to")
        if endpoint_from is not None and endpoint_to is not None:
            self._require_distinct_endpoints(
                endpoint_from,
                endpoint_to,
                "INVALID_CABLE_ENDPOINTS",
                "Cable",
                cable_id,
            )
        self._ensure_not_exists("cable", cable_id, "Cable")
        cable = Cable(
            id=cable_id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            name=name,
            length_km=length_km,
            rated_voltage_kv=rated_voltage_kv,
            rated_current_a=rated_current_a,
            r1_ohm_per_km=r1_ohm_per_km,
            x1_ohm_per_km=x1_ohm_per_km,
            b1_us_per_km=b1_us_per_km,
            r0_ohm_per_km=r0_ohm_per_km,
            x0_ohm_per_km=x0_ohm_per_km,
            b0_us_per_km=b0_us_per_km,
            in_service=in_service,
        )
        self._network.add_cable(cable)
        transaction.record_undo(lambda cable=cable: self._network.remove_cable(cable))
        return self._success(cable, "cable", cable_id, f"Cable created: {cable_id}")

    def update_cable(
        self,
        *,
        cable_id: str,
        name: str | None = None,
        length_km: float | None = None,
        rated_voltage_kv: float | None = None,
        rated_current_a: float | None = None,
        r1_ohm_per_km: float | None = None,
        x1_ohm_per_km: float | None = None,
        b1_us_per_km: float | None = None,
        r0_ohm_per_km: float | None = None,
        x0_ohm_per_km: float | None = None,
        b0_us_per_km: float | None = None,
        in_service: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Cable]:
        self._require_transaction(transaction)
        self._require_id(cable_id, "cable_id")
        cable = self._get_required("cable", cable_id, "Cable")
        self._require_type(cable, Cable, cable_id, "Cable")
        if all(
            value is None
            for value in (
                name,
                length_km,
                rated_voltage_kv,
                rated_current_a,
                r1_ohm_per_km,
                x1_ohm_per_km,
                b1_us_per_km,
                r0_ohm_per_km,
                x0_ohm_per_km,
                b0_us_per_km,
                in_service,
            )
        ):
            raise DomainError(
                code="NO_CABLE_UPDATE",
                message="At least one mutable Cable property must be specified.",
                details={"cable_id": cable_id},
            )

        old = {
            key: getattr(cable, key)
            for key in (
                "name",
                "length_km",
                "rated_voltage_kv",
                "rated_current_a",
                "r1_ohm_per_km",
                "x1_ohm_per_km",
                "b1_us_per_km",
                "r0_ohm_per_km",
                "x0_ohm_per_km",
                "b0_us_per_km",
                "in_service",
            )
        }
        for key, value in (
            ("name", name),
            ("length_km", length_km),
            ("rated_voltage_kv", rated_voltage_kv),
            ("rated_current_a", rated_current_a),
            ("r1_ohm_per_km", r1_ohm_per_km),
            ("x1_ohm_per_km", x1_ohm_per_km),
            ("b1_us_per_km", b1_us_per_km),
            ("r0_ohm_per_km", r0_ohm_per_km),
            ("x0_ohm_per_km", x0_ohm_per_km),
            ("b0_us_per_km", b0_us_per_km),
        ):
            if value is not None:
                setattr(cable, key, value)
        if in_service is not None:
            cable.set_in_service(in_service)

        def restore() -> None:
            for key, value in old.items():
                if key == "in_service":
                    cable.set_in_service(value)
                else:
                    setattr(cable, key, value)

        transaction.record_undo(restore)
        return self._success(cable, "cable", cable_id, f"Cable updated: {cable_id}")

    def delete_cable(
        self,
        *,
        cable_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[Cable]:
        self._require_transaction(transaction)
        self._require_id(cable_id, "cable_id")
        cable = self._get_required("cable", cable_id, "Cable")
        self._require_type(cable, Cable, cable_id, "Cable")
        self._network.remove_cable(cable)
        transaction.record_undo(lambda cable=cable: self._network.add_cable(cable))
        return self._success(cable, "cable", cable_id, f"Cable deleted: {cable_id}")


__all__ = ["CableModelService"]
