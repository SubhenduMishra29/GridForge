"""Shared numerical primitives for GridForge."""
from .backend import BackendCapability, BackendSelection, BackendKind, select_backend
from .ode import NumericalProblem, ODESolution, solve_numerical_problem, solve_rk4, uniform_time_grid

__all__ = [
    "BackendCapability",
    "BackendKind",
    "BackendSelection",
    "NumericalProblem",
    "ODESolution",
    "select_backend",
    "solve_numerical_problem",
    "solve_rk4",
    "uniform_time_grid",
]
