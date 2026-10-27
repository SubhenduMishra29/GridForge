"""Shared numerical primitives for GridForge."""
from .backend import BackendCapability, BackendSelection, BackendKind, select_backend
from .ode import ODESolution, solve_rk4, uniform_time_grid

__all__ = [
    "BackendCapability",
    "BackendKind",
    "BackendSelection",
    "ODESolution",
    "select_backend",
    "solve_rk4",
    "uniform_time_grid",
]
