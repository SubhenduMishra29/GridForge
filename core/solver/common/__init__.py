"""
GridForge Common Solver Infrastructure

Shared numerical components used by multiple solver domains.

Modules
-------
mismatch
    AC power injection and Newton-Raphson mismatch calculation.

jacobian
    Analytical Newton-Raphson Jacobian assembly.

These modules are intentionally located outside individual solver
packages because they represent reusable numerical infrastructure.

Current consumers include:

    core/solver/power_flow
    core/solver/contingency
    core/solver/dynamics
    future solver modules

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from .mismatch import PowerMismatch
from .jacobian import JacobianBuilder


__all__ = [
    "PowerMismatch",
    "JacobianBuilder",
]
