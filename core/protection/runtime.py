"""Application-facing protection runtime composition boundary."""

from __future__ import annotations

from typing import Any, Mapping

from core.network.network import Network

from .factory import ProtectionFactory
from .project_configuration import ProtectionProjectConfiguration
from .protection_system import ProtectionSystem
from .relay_input import RelayInput


class ProtectionRuntime:
    """Compose the project protection configuration against authoritative Core objects."""

    def __init__(self, network: Network, configuration: ProtectionProjectConfiguration) -> None:
        if not isinstance(network, Network): raise TypeError("network must be a Network.")
        if not isinstance(configuration, ProtectionProjectConfiguration): raise TypeError("configuration must be ProtectionProjectConfiguration.")
        self._network = network
        self._configuration = configuration
        self._system = ProtectionSystem()

    @property
    def system(self) -> ProtectionSystem:
        return self._system

    @property
    def configuration(self) -> ProtectionProjectConfiguration:
        return self._configuration

    def compose(self, channels: Mapping[str, Any]) -> ProtectionSystem:
        """Rebuild the runtime composition from project configuration and live channels."""
        self._system = ProtectionSystem()
        for item in self._configuration.elements:
            relay = self._network.get_by_id("relay", item.relay_id)
            relay_inputs = {
                name: RelayInput(name, channels[channel_id])
                for name, channel_id in item.input_channel_ids.items()
            }
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
            self._system.add_element(element)
        return self._system


__all__ = ["ProtectionRuntime"]
