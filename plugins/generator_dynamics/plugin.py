"""Lifecycle adapter for GridForge's universal generator dynamics extension.

The Application composition root must explicitly provide a transactional
generator_dynamics_composition service. The plugin does not construct a
parallel service locator, command manager, study registry, or event bus.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, ClassVar

from core.plugin_sdk import (
    SUPPORTED_PLUGIN_API_VERSION,
    GridForgePlugin,
    HostPluginContext,
    PluginDescriptor,
    validate_plugin_descriptor,
)

PLUGIN_DESCRIPTOR = PluginDescriptor(
    plugin_id="gridforge.plugin.generator_dynamics",
    version="0.1.0",
    api_version=SUPPORTED_PLUGIN_API_VERSION,
    display_name="Universal Generator Dynamics and Instrumentation",
    capabilities=frozenset({
        "generator_catalogue",
        "synchronous_machine_dynamics",
        "prime_mover_models",
        "reduced_hydro_governor_model",
        "ggov1_parameter_contract",
        "ggov1_pid_subblock",
        "ggov1_valve_actuator_subblock",
        "ggov1_turbine_fuel_path_subblock",
        "ggov1_low_value_selector",
        "ggov1_pid_tracking_input",
        "ggov1_reduced_acceleration_limiter",
        "excitation_and_governor_configuration",
        "instrumentation_templates",
        "measurement_channel_provisioning",
        "cpu_gpu_compute_policy",
        "npu_inference_policy",
    }),
)


class GeneratorDynamicsPlugin(GridForgePlugin):
    """Explicitly activated extension; all host registrations are reversible."""

    descriptor: ClassVar[PluginDescriptor] = PLUGIN_DESCRIPTOR

    @property
    def plugin_id(self) -> str:
        return PLUGIN_DESCRIPTOR.plugin_id

    def __init__(self) -> None:
        self._release_registration: Any = None
        self._initialized = False

    def initialize(self, context: HostPluginContext) -> None:
        if self._initialized or self._release_registration is not None:
            raise RuntimeError("GeneratorDynamicsPlugin is already active or awaiting cleanup")
        if context is None or getattr(context, "application", None) is None:
            raise TypeError("initialize requires a canonical GridForge plugin context")
        metadata = getattr(context, "metadata", {})
        services = getattr(context, "services", None)
        if not isinstance(metadata, Mapping) or not isinstance(services, Mapping):
            raise TypeError("plugin context metadata and services must be mappings")
        supported = metadata.get(
            "host_supported_plugin_api_versions",
            frozenset({SUPPORTED_PLUGIN_API_VERSION}),
        )
        if isinstance(supported, str) or not isinstance(supported, (tuple, list, set, frozenset)):
            raise TypeError("host plugin API versions must be a collection of strings")
        validate_plugin_descriptor(
            self.descriptor,
            supported_api_versions=frozenset(supported),
            expected_plugin_id=self.plugin_id,
        )
        composition = services.get("generator_dynamics_composition")
        if composition is None:
            raise RuntimeError(
                "Generator dynamics activation requires the Application-owned "
                "'generator_dynamics_composition' service; no parallel service is created."
            )
        register = getattr(composition, "register_generator_extension", None)
        if not callable(register):
            raise TypeError("generator_dynamics_composition must expose register_generator_extension")
        token = register(plugin=self)
        if not callable(token):
            raise TypeError("register_generator_extension must return a callable teardown")
        self._release_registration = token
        self._initialized = True

    def shutdown(self) -> None:
        release = self._release_registration
        if release is None:
            self._initialized = False
            return
        release()
        self._release_registration = None
        self._initialized = False


__all__ = ["GeneratorDynamicsPlugin", "PLUGIN_DESCRIPTOR"]
