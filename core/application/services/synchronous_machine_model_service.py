"""Application service boundary for SynchronousMachine mutations."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.errors import DomainError
from core.model.bus import Bus
from core.model.synchronous_machine import SynchronousMachine
from core.model.terminal import Terminal
from core.network.network import Network


class SynchronousMachineModelService(ModelServiceSupport):
    """Owns Application-layer mutation use cases for SynchronousMachine."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    def create_synchronous_machine(
        self,
        *,
        synchronous_machine_id: str,
        endpoint: Bus | Terminal | None = None,
        name: str = "",
        active_power_injection_mw: float = 0.0,
        reactive_power_injection_mvar: float = 0.0,
        rated_power_mva: float | None = None,
        rated_voltage_kv: float | None = None,
        frequency_hz: float = 50.0,
        in_service: bool = True,
        transaction: Transaction,
    ) -> ApplicationResult[SynchronousMachine]:
        self._require_transaction(transaction)
        self._require_id(synchronous_machine_id, "synchronous_machine_id")
        if endpoint is not None:
            self._validate_endpoint(endpoint, "endpoint")
        self._ensure_not_exists("synchronous_machine", synchronous_machine_id, "SynchronousMachine")
        machine = SynchronousMachine(
            id=synchronous_machine_id,
            name=name,
            endpoint=endpoint,
            active_power_injection_mw=active_power_injection_mw,
            reactive_power_injection_mvar=reactive_power_injection_mvar,
            rated_power_mva=rated_power_mva,
            rated_voltage_kv=rated_voltage_kv,
            frequency_hz=frequency_hz,
            in_service=in_service,
        )
        self._network.add_synchronous_machine(machine)
        transaction.record_undo(lambda machine=machine: self._network.remove_synchronous_machine(machine))
        return self._success(machine, "synchronous_machine", synchronous_machine_id, f"SynchronousMachine created: {synchronous_machine_id}")

    def update_synchronous_machine(
        self,
        *,
        synchronous_machine_id: str,
        name: str | None = None,
        active_power_injection_mw: float | None = None,
        reactive_power_injection_mvar: float | None = None,
        rated_power_mva: float | None = None,
        rated_voltage_kv: float | None = None,
        frequency_hz: float | None = None,
        in_service: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[SynchronousMachine]:
        self._require_transaction(transaction)
        self._require_id(synchronous_machine_id, "synchronous_machine_id")
        machine = self._get_required("synchronous_machine", synchronous_machine_id, "SynchronousMachine")
        self._require_type(machine, SynchronousMachine, synchronous_machine_id, "SynchronousMachine")
        values = (name, active_power_injection_mw, reactive_power_injection_mvar, rated_power_mva,
                  rated_voltage_kv, frequency_hz, in_service)
        if all(value is None for value in values):
            raise DomainError(
                code="NO_SYNCHRONOUS_MACHINE_UPDATE",
                message="At least one mutable SynchronousMachine property must be specified.",
                details={"synchronous_machine_id": synchronous_machine_id},
            )

        old = {
            "name": machine.name,
            "active_power_injection_mw": machine.active_power_injection_mw,
            "reactive_power_injection_mvar": machine.reactive_power_injection_mvar,
            "rated_power_mva": machine.rated_power_mva,
            "rated_voltage_kv": machine.rated_voltage_kv,
            "frequency_hz": machine.frequency_hz,
            "in_service": machine.in_service,
        }
        try:
            if name is not None:
                machine.name = name
            if active_power_injection_mw is not None or reactive_power_injection_mvar is not None:
                machine.set_power(
                    machine.active_power_injection_mw if active_power_injection_mw is None else active_power_injection_mw,
                    machine.reactive_power_injection_mvar if reactive_power_injection_mvar is None else reactive_power_injection_mvar,
                )
            if rated_power_mva is not None:
                machine.rated_power_mva = rated_power_mva
            if rated_voltage_kv is not None:
                machine.rated_voltage_kv = rated_voltage_kv
            if frequency_hz is not None:
                machine.frequency_hz = frequency_hz
            if in_service is not None:
                machine.put_in_service() if in_service else machine.take_out_of_service()
            machine.validate_parameters()
        except Exception:
            machine.name = old["name"]
            machine.active_power_injection_mw = old["active_power_injection_mw"]
            machine.reactive_power_injection_mvar = old["reactive_power_injection_mvar"]
            machine.rated_power_mva = old["rated_power_mva"]
            machine.rated_voltage_kv = old["rated_voltage_kv"]
            machine.frequency_hz = old["frequency_hz"]
            machine.in_service = old["in_service"]
            raise

        def restore() -> None:
            machine.name = old["name"]
            machine.active_power_injection_mw = old["active_power_injection_mw"]
            machine.reactive_power_injection_mvar = old["reactive_power_injection_mvar"]
            machine.rated_power_mva = old["rated_power_mva"]
            machine.rated_voltage_kv = old["rated_voltage_kv"]
            machine.frequency_hz = old["frequency_hz"]
            machine.in_service = old["in_service"]
            machine.validate_parameters()

        transaction.record_undo(restore)
        return self._success(machine, "synchronous_machine", synchronous_machine_id, f"SynchronousMachine updated: {synchronous_machine_id}")

    def delete_synchronous_machine(
        self,
        *,
        synchronous_machine_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[SynchronousMachine]:
        self._require_transaction(transaction)
        self._require_id(synchronous_machine_id, "synchronous_machine_id")
        machine = self._get_required("synchronous_machine", synchronous_machine_id, "SynchronousMachine")
        self._require_type(machine, SynchronousMachine, synchronous_machine_id, "SynchronousMachine")
        self._network.remove_synchronous_machine(machine)
        transaction.record_undo(lambda machine=machine: self._network.add_synchronous_machine(machine))
        return self._success(machine, "synchronous_machine", synchronous_machine_id, f"SynchronousMachine deleted: {synchronous_machine_id}")


__all__ = ["SynchronousMachineModelService"]
