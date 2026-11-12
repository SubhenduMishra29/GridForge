"""GridForge universal generator dynamics plugin contracts."""
from .catalog import (
    GeneratorFamily, GeneratorNameplate, GeneratorOperatingMode,
    SynchronousMachineDynamics, ExcitationParameters, GovernorParameters,
    PrimeMoverParameters,
)
from .instrumentation import (
    GeneratorMeasurementPoint, generator_measurement_points,
    provision_generator_measurement_channels,
)
from .compute import GENERATOR_WORKLOADS, NPU_INFERENCE_WORKLOADS, select_generator_backend
from .plugin import GeneratorDynamicsPlugin, PLUGIN_DESCRIPTOR
from .controllers import (
    FirstOrderAVRParameters, FirstOrderAVR, TGOV1Governor,
    PSSParameters, WashoutLeadLagPSS, TGOV1Parameters, TGOV1SteamGovernor,
)

__all__ = [
    "GeneratorFamily", "GeneratorNameplate", "GeneratorOperatingMode",
    "SynchronousMachineDynamics", "ExcitationParameters", "GovernorParameters",
    "PrimeMoverParameters", "GeneratorMeasurementPoint", "generator_measurement_points",
    "provision_generator_measurement_channels", "GENERATOR_WORKLOADS",
    "NPU_INFERENCE_WORKLOADS", "select_generator_backend",
    "GeneratorDynamicsPlugin", "PLUGIN_DESCRIPTOR",
    "FirstOrderAVRParameters", "FirstOrderAVR", "TGOV1Governor",
    "PSSParameters", "WashoutLeadLagPSS", "TGOV1Parameters", "TGOV1SteamGovernor",
]
