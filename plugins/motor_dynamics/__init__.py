"""GridForge V2 motor dynamics extension; optional dependencies are loaded lazily."""
from .plugin import MotorDynamicsPlugin
from .catalog import MOTOR_FAMILY_PROFILES, MotorFamily, MotorFamilyProfile, MotorNameplate, MotorOperatingMode, motor_family_profile
from .instrumentation import MotorMeasurementPoint, motor_measurement_points, provision_motor_measurement_channels
from .transient_solver import (
    MotorParameters,
    MotorSimulationResult,
    cuda_available,
    solve_transient_batch,
    solve_transient_cpu,
)

__all__ = [
    "MotorDynamicsPlugin",
    "MotorFamily", "MotorFamilyProfile", "MotorNameplate", "MotorOperatingMode",
    "MOTOR_FAMILY_PROFILES", "motor_family_profile",
    "MotorMeasurementPoint", "motor_measurement_points", "provision_motor_measurement_channels",
    "MotorParameters",
    "MotorSimulationResult",
    "solve_transient_cpu",
    "solve_transient_batch",
    "cuda_available",
]
