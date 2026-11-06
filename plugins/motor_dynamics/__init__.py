"""GridForge V2 motor dynamics extension; optional dependencies are loaded lazily."""
from .plugin import MotorDynamicsPlugin
from .transient_solver import (
    MotorParameters,
    MotorSimulationResult,
    cuda_available,
    solve_transient_batch,
    solve_transient_cpu,
)

__all__ = [
    "MotorDynamicsPlugin",
    "MotorParameters",
    "MotorSimulationResult",
    "solve_transient_cpu",
    "solve_transient_batch",
    "cuda_available",
]
