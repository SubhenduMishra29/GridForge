"""Shared headless numerical methods for GridForge V2.

Numerical methods are domain-neutral. Domain equations and study semantics
remain owned by their respective Core models or physics plugins.
"""
from core.numerics.ode import ODESolution, solve_rk4, uniform_time_grid

__all__ = ["ODESolution", "solve_rk4", "uniform_time_grid"]
