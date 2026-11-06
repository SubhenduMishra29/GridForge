# ============================================================
# File: core/application/services/generator_model_service.py
# GridForge V2 — Generator Model Service
# Author: Subhendu Mishra
# ============================================================

"""Application service owning Generator mutations."""

from __future__ import annotations

from core.application.errors import DomainError
from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.model.bus import Bus
from core.model.generator import Generator
from core.model.terminal import Terminal
from core.network.network import Network


class GeneratorModelService(ModelServiceSupport):
    """Own Generator mutation operations while preserving the application boundary."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    def create_generator(self, *, generator_id: str, endpoint: Bus | Terminal | None = None, p: float = 0.0, q: float = 0.0, V_setpoint: float = 1.0, q_limits: tuple[float, float] = (-float("inf"), float("inf")), name: str = "", in_service: bool = True, transaction: Transaction) -> ApplicationResult[Generator]:
        self._require_transaction(transaction); self._require_id(generator_id, "generator_id")
        if endpoint is not None: self._validate_endpoint(endpoint, "endpoint")
        self._ensure_not_exists("generator", generator_id, "Generator"); generator = Generator(id=generator_id, endpoint=endpoint, p=p, q=q, V_setpoint=V_setpoint, q_limits=q_limits, name=name, in_service=in_service); self._network.add_generator(generator); transaction.record_undo(lambda generator=generator: self._network.remove_generator(generator)); return self._success(generator, "generator", generator_id, f"Generator created: {generator_id}")

    def update_generator(
        self,
        *,
        generator_id: str,
        name: str | None = None,
        p: float | None = None,
        q: float | None = None,
        V_setpoint: float | None = None,
        q_limits: tuple[float, float] | None = None,
        in_service: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Generator]:
        self._require_transaction(transaction)
        self._require_id(generator_id, "generator_id")
        generator = self._get_required("generator", generator_id, "Generator")
        self._require_type(generator, Generator, generator_id, "Generator")

        if all(value is None for value in (name, p, q, V_setpoint, q_limits, in_service)):
            raise DomainError(
                code="NO_GENERATOR_UPDATE",
                message="At least one mutable Generator property must be specified.",
                details={"generator_id": generator_id},
            )

        old = {
            "name": generator.name,
            "p": generator.p,
            "q": generator.q,
            "V_setpoint": generator.V_setpoint,
            "q_min": generator.q_min,
            "q_max": generator.q_max,
            "in_service": generator.in_service,
        }
        service_state_changed = in_service is not None and in_service != old["in_service"]

        def restore_snapshot() -> None:
            # Restore the exact prior state even when the attempted update
            # changed Q limits before a later validation failure.
            generator.name = old["name"]
            generator.p = old["p"]
            generator.q = old["q"]
            generator.V_setpoint = old["V_setpoint"]
            generator.q_min = old["q_min"]
            generator.q_max = old["q_max"]
            generator.in_service = old["in_service"]

        try:
            if name is not None:
                generator.name = name
            if p is not None and q is not None:
                generator.set_power(p, q)
            elif p is not None:
                generator.set_active_power(p)
            elif q is not None:
                generator.set_reactive_power(q)
            if q_limits is not None:
                generator.set_q_limits(q_limits[0], q_limits[1])
            if V_setpoint is not None:
                generator.set_voltage_setpoint(V_setpoint)
            if in_service is not None:
                generator.put_in_service() if in_service else generator.take_out_of_service()
        except Exception:
            restore_snapshot()
            raise

        if service_state_changed:
            self._network.invalidate_topology()

        def restore() -> None:
            restore_snapshot()
            if service_state_changed:
                self._network.invalidate_topology()

        transaction.record_undo(restore)
        return self._success(generator, "generator", generator_id, f"Generator updated: {generator_id}")

    def delete_generator(self, *, generator_id: str, transaction: Transaction) -> ApplicationResult[Generator]:
        self._require_transaction(transaction); self._require_id(generator_id,"generator_id"); generator=self._get_required("generator",generator_id,"Generator"); self._require_type(generator,Generator,generator_id,"Generator"); self._network.remove_generator(generator); transaction.record_undo(lambda generator=generator:self._network.add_generator(generator)); return self._success(generator,"generator",generator_id,f"Generator deleted: {generator_id}")


__all__ = ["GeneratorModelService"]
