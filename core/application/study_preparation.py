# ============================================================
# File: core/application/study_preparation.py
# GridForge V2 — Application Study Preparation Boundary
# Author: Subhendu Mishra
# ============================================================
"""Application-owned bridge from active project state to detached study inputs."""

from __future__ import annotations

from typing import Any, Callable

from core.analysis.power_flow_preparation import PreparedPowerFlow, PowerFlowPreparation
from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration
from core.analysis.short_circuit_preparation import ShortCircuitPreparation
from core.analysis.short_circuit_configuration import ShortCircuitStudyConfiguration
from core.solver.short_circuit.input import ShortCircuitInput


NetworkProvider = Callable[[], Any]


class StudyPreparationService:
    """Prepare detached Core study snapshots without exposing live Core objects to handlers."""

    def __init__(self, network_provider: NetworkProvider) -> None:
        if not callable(network_provider):
            raise TypeError("network_provider must be callable.")
        self._network_provider = network_provider

    def prepare_power_flow(self, configuration: PowerFlowStudyConfiguration) -> PreparedPowerFlow:
        if not isinstance(configuration, PowerFlowStudyConfiguration):
            raise TypeError("configuration must be PowerFlowStudyConfiguration.")
        return PowerFlowPreparation.prepare(self._network_provider(), configuration)

    def prepare_short_circuit(self, configuration: ShortCircuitStudyConfiguration) -> ShortCircuitInput:
        if not isinstance(configuration, ShortCircuitStudyConfiguration):
            raise TypeError("configuration must be ShortCircuitStudyConfiguration.")
        preparation = ShortCircuitPreparation(
            self._network_provider(),
            base_mva=configuration.metadata.get("base_mva"),
        )
        return preparation.prepare(
            configuration.fault_type,
            configuration.fault_bus_id,
            configuration.fault_impedance,
            elements=configuration.element_ids or None,
        )


__all__ = ["NetworkProvider", "StudyPreparationService"]
