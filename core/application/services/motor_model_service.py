"""Application service boundary for Motor mutations."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.errors import DomainError
from core.model.bus import Bus
from core.model.motor import Motor
from core.model.terminal import Terminal
from core.network.network import Network


class MotorModelService(ModelServiceSupport):
    """Owns Application-layer mutation use cases for Motor objects."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    def create_motor(
        self,
        *,
        motor_id: str,
        endpoint: Bus | Terminal | None = None,
        rated_mva: float = 1.0,
        rated_kv: float = 1.0,
        power_factor: float = 0.9,
        p: float = 0.0,
        q: float = 0.0,
        efficiency: float = 1.0,
        slip: float = 0.0,
        starting_current_pu: float = 0.0,
        running: bool = False,
        in_service: bool = True,
        name: str = "",
        transaction: Transaction,
    ) -> ApplicationResult[Motor]:
        self._require_transaction(transaction)
        self._require_id(motor_id, "motor_id")
        if endpoint is not None:
            self._validate_endpoint(endpoint, "endpoint")
        self._ensure_not_exists("motor", motor_id, "Motor")
        motor = Motor(
            id=motor_id,
            endpoint=endpoint,
            rated_mva=rated_mva,
            rated_kv=rated_kv,
            power_factor=power_factor,
            p=p,
            q=q,
            efficiency=efficiency,
            slip=slip,
            starting_current_pu=starting_current_pu,
            running=running,
            in_service=in_service,
            name=name,
        )
        self._network.add_motor(motor)
        transaction.record_undo(lambda motor=motor: self._network.remove_motor(motor))
        return self._success(motor, "motor", motor_id, f"Motor created: {motor_id}")

    def update_motor(
        self,
        *,
        motor_id: str,
        rated_mva: float | None = None,
        rated_kv: float | None = None,
        power_factor: float | None = None,
        p: float | None = None,
        q: float | None = None,
        efficiency: float | None = None,
        slip: float | None = None,
        starting_current_pu: float | None = None,
        running: bool | None = None,
        in_service: bool | None = None,
        name: str | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Motor]:
        self._require_transaction(transaction)
        self._require_id(motor_id, "motor_id")
        motor = self._get_required("motor", motor_id, "Motor")
        self._require_type(motor, Motor, motor_id, "Motor")
        values = (rated_mva, rated_kv, power_factor, p, q, efficiency, slip,
                  starting_current_pu, running, in_service, name)
        if all(value is None for value in values):
            raise DomainError(
                code="NO_MOTOR_UPDATE",
                message="At least one mutable Motor property must be specified.",
                details={"motor_id": motor_id},
            )

        old = {
            "rated_mva": motor.rated_mva,
            "rated_kv": motor.rated_kv,
            "power_factor": motor.power_factor,
            "p": motor.p,
            "q": motor.q,
            "efficiency": motor.efficiency,
            "slip": motor.slip,
            "starting_current_pu": motor.starting_current_pu,
            "running": motor.running,
            "in_service": motor.in_service,
            "name": motor.name,
        }
        try:
            if name is not None:
                motor.name = name
            if rated_mva is not None:
                motor.rated_mva = rated_mva
            if rated_kv is not None:
                motor.rated_kv = rated_kv
            if power_factor is not None:
                motor.set_power_factor(power_factor)
            if p is not None or q is not None:
                motor.set_power(
                    motor.p if p is None else p,
                    motor.q if q is None else q,
                )
            if efficiency is not None:
                motor.set_efficiency(efficiency)
            if slip is not None:
                motor.set_slip(slip)
            if starting_current_pu is not None:
                motor.set_starting_current(starting_current_pu)
            if in_service is not None:
                motor.put_in_service() if in_service else motor.take_out_of_service()
            if running is not None:
                if running and not motor.in_service:
                    raise DomainError(
                        code="MOTOR_CANNOT_RUN_OUT_OF_SERVICE",
                        message="Motor cannot be running while out of service.",
                        details={"motor_id": motor_id},
                    )
                motor.start() if running else motor.stop()
            motor.validate_parameters()
        except Exception:
            motor.rated_mva = old["rated_mva"]
            motor.rated_kv = old["rated_kv"]
            motor.power_factor = old["power_factor"]
            motor.p = old["p"]
            motor.q = old["q"]
            motor.efficiency = old["efficiency"]
            motor.slip = old["slip"]
            motor.starting_current_pu = old["starting_current_pu"]
            motor.running = old["running"]
            motor.in_service = old["in_service"]
            motor.name = old["name"]
            raise

        def restore() -> None:
            motor.rated_mva = old["rated_mva"]
            motor.rated_kv = old["rated_kv"]
            motor.power_factor = old["power_factor"]
            motor.p = old["p"]
            motor.q = old["q"]
            motor.efficiency = old["efficiency"]
            motor.slip = old["slip"]
            motor.starting_current_pu = old["starting_current_pu"]
            motor.running = old["running"]
            motor.in_service = old["in_service"]
            motor.name = old["name"]
            motor.validate_parameters()

        transaction.record_undo(restore)
        return self._success(motor, "motor", motor_id, f"Motor updated: {motor_id}")

    def delete_motor(
        self,
        *,
        motor_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[Motor]:
        self._require_transaction(transaction)
        self._require_id(motor_id, "motor_id")
        motor = self._get_required("motor", motor_id, "Motor")
        self._require_type(motor, Motor, motor_id, "Motor")
        self._network.remove_motor(motor)
        transaction.record_undo(lambda motor=motor: self._network.add_motor(motor))
        return self._success(motor, "motor", motor_id, f"Motor deleted: {motor_id}")


__all__ = ["MotorModelService"]
