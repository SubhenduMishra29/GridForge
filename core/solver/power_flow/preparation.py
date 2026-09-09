"""Compatibility facade for the authoritative Power Flow preparation boundary.

Author: Subhendu Mishra

Power Flow preparation belongs to the Analysis boundary. The solver package
must not maintain a competing engineering-to-PU preparation implementation.
This module preserves the historical instance-based ``prepare()`` API while
delegating all preparation to ``core.analysis.power_flow_preparation``.
"""

from __future__ import annotations

from typing import Any

from core.analysis.power_flow_preparation import (
    PowerFlowPreparation as _AnalysisPowerFlowPreparation,
    PreparedPowerFlow,
)
from core.analysis.power_flow_configuration import PowerFlowStudyConfiguration


class PowerFlowPreparation:
    """Compatibility facade over the authoritative Analysis preparation."""

    def __init__(
        self,
        network: Any,
        configuration: PowerFlowStudyConfiguration,
    ) -> None:
        self._delegate = _AnalysisPowerFlowPreparation(network, configuration)

    def prepare(self) -> PreparedPowerFlow:
        """Return the immutable numerical snapshot prepared by Analysis."""
        return self._delegate._prepare()


__all__ = ["PowerFlowPreparation", "PreparedPowerFlow"]
