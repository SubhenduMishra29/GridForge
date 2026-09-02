"""
GridForge - Power Flow Preparation
==================================

Prepares an immutable numerical power-flow study snapshot from
authoritative Core state and explicit study-side bus classifications.

The preparation boundary is shared by normal and contingency studies.
It is the only layer here that reads the live Network in order to build
PowerFlowInput and YBus. Numerical Power Flow execution receives only the
prepared result.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.model.injection import Injection
from core.numerical.ybus import YBus, YBusBuilder
from core.solver.power_flow.input import PowerFlowInput


@dataclass(frozen=True, slots=True)
class PreparedPowerFlow:
    """Immutable prepared numerical Power Flow problem."""

    input: PowerFlowInput
    ybus: YBus

    def __post_init__(self) -> None:
        if not isinstance(self.input, PowerFlowInput):
            raise TypeError("input must be a PowerFlowInput instance.")
        if not isinstance(self.ybus, YBus):
            raise TypeError("ybus must be a YBus instance.")
        if self.input.bus_ids != self.ybus.bus_ids:
            raise ValueError(
                "PowerFlowInput and YBus must use identical bus ordering."
            )


class PowerFlowPreparation:
    """Prepare Power Flow numerical contracts from Core state."""

    _INJECTION_COLLECTIONS = (
        "grids",
        "generators",
        "synchronous_machines",
        "loads",
        "motors",
        "solar",
        "batteries",
    )

    @staticmethod
    def prepare(
        network: Any,
        power_flow_configuration: PowerFlowStudyConfiguration,
    ) -> PreparedPowerFlow:
        """Build immutable Power Flow input and matching YBus."""
        preparation = PowerFlowPreparation(
            network,
            power_flow_configuration,
        )
        return preparation._prepare()

    def __init__(
        self,
        network: Any,
        power_flow_configuration: PowerFlowStudyConfiguration,
    ) -> None:
        self.network = network
        self.power_flow_configuration = power_flow_configuration
        self._validate_network()
        if not isinstance(
            power_flow_configuration,
            PowerFlowStudyConfiguration,
        ):
            raise TypeError(
                "power_flow_configuration must be a PowerFlowStudyConfiguration."
            )

    def _prepare(self) -> PreparedPowerFlow:
        buses = tuple(self.network.buses)
        if not buses:
            raise ValueError("Power Flow preparation requires at least one bus.")

        bus_ids = tuple(bus.id for bus in buses)
        classification = self._prepare_bus_types(bus_ids)

        p_spec: list[float] = []
        q_spec: list[float] = []
        q_min: list[float | None] = []
        q_max: list[float | None] = []
        initial_vm: list[float] = []
        initial_va: list[float] = []

        for bus in buses:
            p, q, minimum_q, maximum_q = self._bus_power_spec(bus)
            p_spec.append(p)
            q_spec.append(q)
            q_min.append(minimum_q)
            q_max.append(maximum_q)
            initial_vm.append(float(getattr(bus, "voltage_pu")))
            initial_va.append(float(getattr(bus, "angle_deg")))

        input_data = PowerFlowInput(
            bus_ids=bus_ids,
            bus_types=classification,
            p_spec=tuple(p_spec),
            q_spec=tuple(q_spec),
            q_min=tuple(q_min),
            q_max=tuple(q_max),
            initial_vm=tuple(initial_vm),
            initial_va=tuple(initial_va),
        )

        self.network.ensure_bus_index()
        ybus = YBusBuilder(self.network).build()

        return PreparedPowerFlow(input=input_data, ybus=ybus)

    def _prepare_bus_types(
        self,
        bus_ids: tuple[Any, ...],
    ) -> tuple:
        configured = self.power_flow_configuration.bus_types
        expected = set(bus_ids)
        supplied = set(configured)

        missing = expected - supplied
        extra = supplied - expected
        if missing or extra:
            raise ValueError(
                "Power Flow study configuration must match the case Network buses; "
                f"missing={sorted(missing, key=str)!r}, "
                f"extra={sorted(extra, key=str)!r}."
            )

        return tuple(configured[bus_id] for bus_id in bus_ids)

    def _bus_power_spec(
        self,
        bus: Any,
    ) -> tuple[float, float, float | None, float | None]:
        """Aggregate physical injection models attached to one bus."""
        p = 0.0
        q = 0.0
        q_min: float | None = None
        q_max: float | None = None

        for collection_name in self._INJECTION_COLLECTIONS:
            for equipment in getattr(self.network, collection_name, ()):
                if not isinstance(equipment, Injection):
                    continue
                if not getattr(equipment, "in_service", True):
                    continue

                terminal = getattr(equipment, "terminal", None)
                endpoint = getattr(terminal, "endpoint", None)
                if endpoint is not bus and getattr(endpoint, "id", None) != getattr(bus, "id", None):
                    continue

                ep, eq = equipment.get_power()
                p += float(ep)
                q += float(eq)

                if hasattr(equipment, "q_min"):
                    value = float(equipment.q_min)
                    q_min = value if q_min is None else q_min + value
                if hasattr(equipment, "q_max"):
                    value = float(equipment.q_max)
                    q_max = value if q_max is None else q_max + value

        return p, q, q_min, q_max

    def _validate_network(self) -> None:
        if self.network is None:
            raise ValueError("network is required for Power Flow preparation.")
        if not hasattr(self.network, "buses"):
            raise TypeError("network must expose buses.")
        if not hasattr(self.network, "ensure_bus_index"):
            raise TypeError("network must expose ensure_bus_index().")


__all__ = ["PowerFlowPreparation", "PreparedPowerFlow"]
