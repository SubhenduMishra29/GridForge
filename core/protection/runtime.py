"""Application-facing protection runtime composition boundary."""

from __future__ import annotations

from typing import Any, Mapping

from core.network.network import Network

from .factory import ProtectionFactory
from .project_configuration import ProtectionProjectConfiguration
from .protection_system import ProtectionSystem
from .relay_input import DerivedRelayMeasurement, RelayInput
from .input_contracts import validate_protection_input_contracts
from .configuration_fingerprint import canonical_configuration_value


class ProtectionRuntime:
    """Compose project protection configuration against authoritative Core objects."""

    def __init__(
        self,
        network: Network,
        configuration: ProtectionProjectConfiguration,
        *,
        activation_generation: int,
    ) -> None:
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        if not isinstance(configuration, ProtectionProjectConfiguration):
            raise TypeError("configuration must be ProtectionProjectConfiguration.")
        if isinstance(activation_generation, bool) or not isinstance(activation_generation, int) or activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer.")
        self._network = network
        self._configuration = configuration
        self._project_id = str(configuration.project_id)
        self._activation_generation = activation_generation
        self._system = ProtectionSystem()
        self._channels: dict[str, Any] = {}
        self._composed_configuration_snapshot: Any | None = None

    @property
    def activation_generation(self) -> int:
        """Project lifecycle generation for which this runtime was composed."""
        return self._activation_generation

    @property
    def project_id(self) -> str:
        """Project identity captured from the configuration at construction."""
        return self._project_id

    @property
    def network(self) -> Network:
        return self._network

    @property
    def system(self) -> ProtectionSystem:
        return self._system

    @property
    def configuration(self) -> ProtectionProjectConfiguration:
        return self._configuration

    @property
    def channels(self) -> Mapping[str, Any]:
        """Exact channel objects used by the current runtime composition."""
        return dict(self._channels)

    @property
    def configuration_matches_composition(self) -> bool:
        """Whether mutable project configuration still matches the composed runtime."""
        snapshot = self._composed_configuration_snapshot
        if snapshot is None:
            return False
        try:
            return canonical_configuration_value(self._configuration.to_dict()) == snapshot
        except (TypeError, ValueError):
            return False

    def compose(self, channels: Mapping[str, Any]) -> ProtectionSystem:
        """Rebuild runtime composition from project configuration and live channels."""
        if not isinstance(channels, Mapping):
            raise TypeError("channels must be a mapping of channel IDs to MeasurementChannel objects.")

        # Invalidate the previously composed system before any validation or
        # construction work. A failed recomposition must never leave an older
        # system publicly evaluable under a changed configuration or channel
        # mapping. Application transactions retain the previous runtime object
        # separately and restore it through their existing undo/rollback path.
        self._system = ProtectionSystem()
        self._channels = {}
        self._composed_configuration_snapshot = None

        contract_diagnostics = validate_protection_input_contracts(self._configuration, channels)
        if contract_diagnostics:
            raise ValueError("Protection input-contract validation failed before composition: " + " | ".join(contract_diagnostics))
        configuration_snapshot = canonical_configuration_value(self._configuration.to_dict())

        composed_system = ProtectionSystem()
        composed_channels = dict(channels)
        for item in self._configuration.elements:
            relay = self._network.get_by_id("relay", item.relay_id)
            relay_inputs: dict[str, RelayInput] = {}
            for name, channel_id in item.input_channel_ids.items():
                try:
                    channel = channels[channel_id]
                except KeyError as exc:
                    raise KeyError(
                        f"MeasurementChannel '{channel_id}' required by protection element "
                        f"'{item.element_id}' is not available."
                    ) from exc
                relay_inputs[name] = RelayInput(name, channel)

            if item.function_code in {"50N", "51N"}:
                if item.residual_current_input is None:
                    raise ValueError(
                        f"ANSI {item.function_code} element '{item.element_id}' requires an explicit residual_current_input configuration."
                    )
                if "residual_current" in item.input_channel_ids:
                    raise ValueError(
                        "Residual current is a derived relay input and must not be configured as a physical MeasurementChannel."
                    )
                derived_source = DerivedRelayMeasurement(
                    f"derived:{item.element_id}:residual_current"
                )
                relay_inputs["residual_current"] = RelayInput(
                    "residual_current",
                    derived_source,
                    description="Application-resolved residual-current phasor",
                    metadata={"source_kind": "DERIVED_RESIDUAL_CURRENT"},
                )

            element = ProtectionFactory.create_element(
                relay=relay,
                element_id=item.element_id,
                function_code=item.function_code,
                relay_inputs=relay_inputs,
                settings=item.settings,
                enabled=item.enabled,
                blocked=item.blocked,
                name=item.name,
                priority=item.priority,
                metadata=item.metadata,
            )
            composed_system.add_element(element)
        # The aggregate itself is mutable (transactional updates replace
        # entries in-place), so object identity alone cannot prove that the
        # currently composed system reflects its current contents.
        self._system = composed_system
        self._channels = composed_channels
        self._composed_configuration_snapshot = configuration_snapshot
        return self._system


__all__ = ["ProtectionRuntime"]
