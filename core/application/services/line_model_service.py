"""Application service boundary for Line mutations."""

from __future__ import annotations

from core.application.results import ApplicationResult
from core.application.services._model_service_support import ModelServiceSupport
from core.application.transaction import Transaction
from core.model.bus import Bus
from core.model.line import Line
from core.model.conductor import BranchConductorSystem
from core.model.terminal import Terminal
from core.network.network import Network


class LineModelService(ModelServiceSupport):
    """Owns Application-layer mutation use cases for Line equipment."""

    def __init__(self, network: Network) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        self._network = network

    @property
    def network(self) -> Network:
        return self._network

    def create_line(
        self,
        *,
        line_id: str,
        endpoint_from: Bus | Terminal | None = None,
        endpoint_to: Bus | Terminal | None = None,
        resistance_ohm: float = 0.0,
        reactance_ohm: float = 0.0,
        shunt_susceptance_siemens: float = 0.0,
        zero_sequence_resistance_ohm: float | None = None,
        zero_sequence_reactance_ohm: float | None = None,
        conductor_system: BranchConductorSystem | None = None,
        name: str | None = None,
        rate_mva: float | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Line]:
        self._require_transaction(transaction)
        self._require_id(line_id, "line_id")
        if endpoint_from is not None:
            self._validate_endpoint(endpoint_from, "endpoint_from")
        if endpoint_to is not None:
            self._validate_endpoint(endpoint_to, "endpoint_to")
        if endpoint_from is not None and endpoint_to is not None:
            self._require_distinct_endpoints(
                endpoint_from,
                endpoint_to,
                "INVALID_LINE_ENDPOINTS",
                "Line",
                line_id,
            )
        self._ensure_not_exists("line", line_id, "Line")
        line = Line(
            id=line_id,
            endpoint_from=endpoint_from,
            endpoint_to=endpoint_to,
            resistance_ohm=resistance_ohm,
            reactance_ohm=reactance_ohm,
            shunt_susceptance_siemens=shunt_susceptance_siemens,
            zero_sequence_resistance_ohm=zero_sequence_resistance_ohm,
            zero_sequence_reactance_ohm=zero_sequence_reactance_ohm,
            conductor_system=conductor_system,
            name="" if name is None else name,
            rate_mva=rate_mva,
        )
        self._network.add_line(line)
        transaction.record_undo(lambda line=line: self._network.remove_line(line))
        return self._success(line, "line", line_id, f"Line created: {line_id}")

    def update_line(
        self,
        *,
        line_id: str,
        name: str | None = None,
        resistance_ohm: float | None = None,
        reactance_ohm: float | None = None,
        shunt_susceptance_siemens: float | None = None,
        zero_sequence_resistance_ohm: float | None = None,
        zero_sequence_reactance_ohm: float | None = None,
        conductor_system: BranchConductorSystem | None = None,
        clear_conductor_system: bool = False,
        rate_mva: float | None = None,
        in_service: bool | None = None,
        transaction: Transaction,
    ) -> ApplicationResult[Line]:
        self._require_transaction(transaction)
        self._require_id(line_id, "line_id")
        line = self._get_required("line", line_id, "Line")
        self._require_type(line, Line, line_id, "Line")
        values = (name, resistance_ohm, reactance_ohm, shunt_susceptance_siemens, zero_sequence_resistance_ohm, zero_sequence_reactance_ohm, conductor_system, rate_mva, in_service)
        if not isinstance(clear_conductor_system, bool):
            raise TypeError("clear_conductor_system must be bool.")
        if clear_conductor_system and conductor_system is not None:
            raise ValueError("Specify conductor_system or clear_conductor_system, not both.")
        if all(value is None for value in values) and not clear_conductor_system:
            raise ValueError("At least one mutable Line field must be specified.")

        old = {
            "name": line.name,
            "resistance_ohm": line.resistance_ohm,
            "reactance_ohm": line.reactance_ohm,
            "shunt_susceptance_siemens": line.shunt_susceptance_siemens,
            "zero_sequence_resistance_ohm": line.zero_sequence_resistance_ohm,
            "zero_sequence_reactance_ohm": line.zero_sequence_reactance_ohm,
            "rate_mva": line.rate_mva,
            "in_service": line.in_service,
            "conductor_system": line.conductor_system,
        }
        candidate = {
            "name": old["name"] if name is None else name,
            "resistance_ohm": old["resistance_ohm"] if resistance_ohm is None else resistance_ohm,
            "reactance_ohm": old["reactance_ohm"] if reactance_ohm is None else reactance_ohm,
            "shunt_susceptance_siemens": old["shunt_susceptance_siemens"] if shunt_susceptance_siemens is None else shunt_susceptance_siemens,
            "zero_sequence_resistance_ohm": old["zero_sequence_resistance_ohm"] if zero_sequence_resistance_ohm is None else zero_sequence_resistance_ohm,
            "zero_sequence_reactance_ohm": old["zero_sequence_reactance_ohm"] if zero_sequence_reactance_ohm is None else zero_sequence_reactance_ohm,
            "rate_mva": old["rate_mva"] if rate_mva is None else rate_mva,
            "in_service": old["in_service"] if in_service is None else in_service,
            "conductor_system": None if clear_conductor_system else (old["conductor_system"] if conductor_system is None else conductor_system),
        }

        def apply(state: dict[str, Any]) -> None:
            line.name = state["name"]
            line.resistance_ohm = state["resistance_ohm"]
            line.reactance_ohm = state["reactance_ohm"]
            line.shunt_susceptance_siemens = state["shunt_susceptance_siemens"]
            line.zero_sequence_resistance_ohm = state["zero_sequence_resistance_ohm"]
            line.zero_sequence_reactance_ohm = state["zero_sequence_reactance_ohm"]
            line.rate_mva = state["rate_mva"]
            line.set_in_service(state["in_service"])
            line.conductor_system = state["conductor_system"]
            line.validate()

        try:
            apply(candidate)
        except BaseException:
            apply(old)
            raise

        service_state_changed = (
            in_service is not None and in_service != old["in_service"]
        )
        if service_state_changed:
            self._network.invalidate_topology()

        def restore() -> None:
            apply(old)
            if service_state_changed:
                self._network.invalidate_topology()

        transaction.record_undo(restore)
        return self._success(line, "line", line_id, f"Line updated: {line_id}")

    def delete_line(
        self,
        *,
        line_id: str,
        transaction: Transaction,
    ) -> ApplicationResult[Line]:
        self._require_transaction(transaction)
        self._require_id(line_id, "line_id")
        line = self._get_required("line", line_id, "Line")
        self._require_type(line, Line, line_id, "Line")
        self._network.remove_line(line)
        transaction.record_undo(lambda line=line: self._network.add_line(line))
        return self._success(line, "line", line_id, f"Line deleted: {line_id}")


__all__ = ["LineModelService"]
