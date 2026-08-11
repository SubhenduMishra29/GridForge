# GridForge

# Copyright © 2026 Subhendu Mishra

# All Rights Reserved.

# Proprietary and confidential.

"""
GridForge Power Flow Solver Package
===================================

File:
core/solver/power_flow/__init__.py

## Purpose

Public interface for the GridForge numerical AC power-flow
solver package.

This package contains the numerical engine used by:

```
core/analysis/power_flow.py
```

## Architecture

```
core/analysis/power_flow.py
            │
            ▼
core/solver/power_flow/
            │
    ┌───────┼───────────────────────┐
    │       │       │       │       │
    ▼       ▼       ▼       ▼       ▼
 options  mismatch jacobian sparse  Q-limit
    │       │       │       │       │
    └───────┴───────┴───────┴───────┘
                    │
                    ▼
            nr_solver.py
```

## Public Components

SolverOptions
Numerical configuration for the power-flow solver.

PowerMismatch
Calculates active/reactive power mismatches.

JacobianBuilder
Builds the Newton-Raphson Jacobian matrix.

SparseLinearSolver
Solves the Newton-Raphson linear system.

QLimitHandler
Handles generator reactive-power limits and PV/PQ
bus conversion.

NewtonRaphsonSolver
Main numerical AC power-flow engine.

## Design Rule

This __init__.py exposes the public solver API only.

No numerical logic belongs here.
"""

# ============================================================
# NUMERICAL CONFIGURATION
# ============================================================

from .solver_options import SolverOptions

# ============================================================
# POWER MISMATCH
#
# Shared numerical infrastructure, physically located under
# core/solver/common/. Imported here via its absolute path
# rather than a local relative import.
# ============================================================

from core.solver.common.mismatch import PowerMismatch

# ============================================================
# NEWTON-RAPHSON JACOBIAN
#
# Shared numerical infrastructure, physically located under
# core/solver/common/. Imported here via its absolute path
# rather than a local relative import.
# ============================================================

from core.solver.common.jacobian import JacobianBuilder

# ============================================================
# SPARSE LINEAR SOLVER
# ============================================================

from .sparse_solver import SparseLinearSolver

# ============================================================
# GENERATOR REACTIVE POWER LIMITS
# ============================================================

from .q_limit_handler import QLimitHandler

# ============================================================
# MAIN NEWTON-RAPHSON ENGINE
# ============================================================

from .nr_solver import NewtonRaphsonSolver

# ============================================================
# PUBLIC PACKAGE API
# ============================================================

__all__ = [
    "SolverOptions",
    "PowerMismatch",
    "JacobianBuilder",
    "SparseLinearSolver",
    "QLimitHandler",
    "NewtonRaphsonSolver",
]
