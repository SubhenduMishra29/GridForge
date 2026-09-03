"""Preparation boundary from authoritative Core/Network state to numerical contracts."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from core.network.endpoint import resolve_terminal_bus
from core.numerical.ybus import YBus, YBusBuilder

from .input import PowerFlowInput
from .study_configuration import PowerFlowStudyConfiguration


@dataclass(frozen=True, slots=True)
class PreparedPowerFlow:
    """Immutable numerical package produced by power-flow preparation."""

    input: PowerFlowInput
    ybus: YBus

    def __post_init__(self) -> None:
        if not isinstance(self.input, PowerFlowInput):
            raise TypeError("input must be PowerFlowInput.")
        if not isinstance(self.ybus, YBus):
            raise TypeError("ybus must be YBus.")
        if self.ybus.shape != (self.input.bus_count, self.input.bus_count):
            raise ValueError("Prepared YBus dimension does not match PowerFlowInput.")
        if self.ybus.bus_ids != self.input.bus_ids:
            raise ValueError("Prepared YBus ordering does not match PowerFlowInput.")

    @property
    def input_data(self) -> PowerFlowInput:
        """Compatibility/readability alias for the numerical input."""

        return self.input


class PowerFlowPreparation:
    """Convert an authoritative Network into numerical power-flow contracts.

    Preparation is deliberately read-only with respect to electrical model
    state. It consumes the Network's already-valid BusIndex and uses the
    existing YBusBuilder; it never assigns bus types, changes equipment state,
    or stores references to the live Network in the returned result.
    """

    def __init__(
        self,
        network: Any,
        configuration: PowerFlowStudyConfiguration,
    ) -> None:
        if network is None:
            raise ValueError("PowerFlowPreparation requires a Network.")
        if not isinstance(configuration, PowerFlowStudyConfiguration):
            raise TypeError(
                "configuration must be PowerFlowStudyConfiguration."
            )
        self.network = network
        self.configuration = configuration

    def prepare(self) -> PreparedPowerFlow:
        """Prepare immutable numerical input and a derived YBus."""

        buses = tuple(getattr(self.network, "buses", ()))
        if not buses:
            raise ValueError("Cannot prepare power flow for a Network with no buses.")

        bus_ids = tuple(str(bus.id) for bus in buses)
        if len(set(bus_ids)) != len(bus_ids):
            raise ValueError("Network bus IDs must be unique.")

        configured_ids = tuple(bus_id for bus_id, _ in self.configuration.bus_types)
        if set(configured_ids) != set(bus_ids):
            raise ValueError(
                "Power-flow study configuration must contain exactly the "
                "current Network bus IDs."
            )

        index = getattr(self.network, "index", None)
        if index is None or getattr(index, "valid", False) is not True:
            raise RuntimeError(
                "Network BusIndex must be valid before power-flow preparation."
            )
        mapping = getattr(index, "mapping", None)
        if mapping is None or set(mapping) != set(bus_ids):
            raise RuntimeError("Network BusIndex does not match current bus membership.")

        p_spec, q_spec, q_min, q_max = self._collect_injections(buses)
        initial_vm = tuple(self._finite_positive(getattr(bus, "voltage_pu", 1.0), f"Bus '{bus.id}' voltage_pu") for bus in buses)
        initial_va = tuple(
            math.radians(self._finite(getattr(bus, "angle_deg", 0.0), f"Bus '{bus.id}' angle_deg"))
            for bus in buses
        )

        input_data = PowerFlowInput(
            bus_ids=bus_ids,
            bus_types=tuple(
                self.configuration.type_of(bus_id)
                for bus_id in bus_ids
            ),
            p_spec=tuple(p_spec),
            q_spec=tuple(q_spec),
            q_min=tuple(q_min),
            q_max=tuple(q_max),
            initial_vm=initial_vm,
            initial_va=initial_va,
        )

        ybus = YBusBuilder(self.network).build()
        return PreparedPowerFlow(input=input_data, ybus=ybus)

    def _collect_injections(self, buses: tuple[Any, ...]) -> tuple[list[float], list[float], list[float | None], list[float | None]]:
        bus_ids = {str(bus.id) for bus in buses}
        generation: dict[str, float] = {bus_id: 0.0 for bus_id in bus_ids}
        reactive_generation: dict[str, float] = {bus_id: 0.0 for bus_id in bus_ids}
        load_p: dict[str, float] = {bus_id: 0.0 for bus_id in bus_ids}
        load_q: dict[str, float] = {bus_id: 0.0 for bus_id in bus_ids}
        q_mins: dict[str, float] = {}
        q_maxs: dict[str, float] = {}
        has_generator: dict[str, bool] = {bus_id: False for bus_id in bus_ids}

        for generator in getattr(self.network, "generators", ()):
            if not bool(getattr(generator, "in_service", True)):
                continue
            bus_id = self._element_bus_id(generator)
            if bus_id not in bus_ids:
                raise ValueError(f"Generator '{getattr(generator, 'id', generator)}' resolves outside the Network buses.")
            p = self._finite(getattr(generator, "p", 0.0), f"Generator '{generator.id}' p")
            q = self._finite(getattr(generator, "q", 0.0), f"Generator '{generator.id}' q")
            generation[bus_id] += p
            reactive_generation[bus_id] += q
            has_generator[bus_id] = True
            q_min = self._finite(getattr(generator, "q_min", -float("inf")), f"Generator '{generator.id}' q_min")
            q_max = self._finite(getattr(generator, "q_max", float("inf")), f"Generator '{generator.id}' q_max")
            q_mins[bus_id] = q_mins.get(bus_id, 0.0) + q_min
            q_maxs[bus_id] = q_maxs.get(bus_id, 0.0) + q_max

        for load in getattr(self.network, "loads", ()):
            if not bool(getattr(load, "in_service", True)):
                continue
            bus_id = self._element_bus_id(load)
            if bus_id not in bus_ids:
                raise ValueError(f"Load '{getattr(load, 'id', load)}' resolves outside the Network buses.")
            p = self._finite(getattr(load, "p", 0.0), f"Load '{load.id}' p")
            q = self._finite(getattr(load, "q", 0.0), f"Load '{load.id}' q")
            load_p[bus_id] += p
            load_q[bus_id] += q

        scale = self.configuration.base_mva
        p_spec = [(generation[bus_id] - load_p[bus_id]) / scale for bus_id in (str(bus.id) for bus in buses)]
        q_spec = [(reactive_generation[bus_id] - load_q[bus_id]) / scale for bus_id in (str(bus.id) for bus in buses)]

        q_min: list[float | None] = []
        q_max: list[float | None] = []
        for bus_id in (str(bus.id) for bus in buses):
            if has_generator[bus_id]:
                q_min.append(q_mins[bus_id] / scale)
                q_max.append(q_maxs[bus_id] / scale)
            else:
                q_min.append(None)
                q_max.append(None)

        return p_spec, q_spec, q_min, q_max

    @staticmethod
    def _element_bus_id(element: Any) -> str:
        terminal = getattr(element, "terminal", None)
        if terminal is None:
            raise ValueError(
                f"Element '{getattr(element, 'id', element)}' does not provide an authoritative terminal."
            )
        try:
            bus = resolve_terminal_bus(terminal)
        except Exception as exc:
            raise ValueError(
                f"Element '{getattr(element, 'id', element)}' has an unresolved terminal."
            ) from exc
        bus_id = getattr(bus, "id", None)
        if not isinstance(bus_id, str) or not bus_id:
            raise ValueError(
                f"Element '{getattr(element, 'id', element)}' resolves to an invalid bus."
            )
        return bus_id

    @staticmethod
    def _finite(value: Any, name: str) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be numeric.") from exc
        if not math.isfinite(numeric):
            raise ValueError(f"{name} must be finite.")
        return numeric

    @classmethod
    def _finite_positive(cls, value: Any, name: str) -> float:
        numeric = cls._finite(value, name)
        if numeric <= 0.0:
            raise ValueError(f"{name} must be greater than zero.")
        return numeric


__all__ = ["PowerFlowPreparation", "PreparedPowerFlow"]
