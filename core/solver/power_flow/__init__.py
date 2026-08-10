# GridForge

# Copyright © 2026 Subhendu Mishra

# All Rights Reserved.

# Proprietary and confidential.

"""
GridForge Power Flow Solver Package
===================================

File:
core/solver/power_flow/**init**.py

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
            newton_raphson.py
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

This **init**.py exposes the public solver API only.

No numerical logic belongs here.
"""

# ============================================================

# NUMERICAL CONFIGURATION

# ============================================================

from .solver_options import SolverOptions

# ============================================================

# POWER MISMATCH

# ============================================================

from .mismatch import PowerMismatch

# ============================================================

# NEWTON-RAPHSON JACOBIAN

# ============================================================

from .jacobian import JacobianBuilder

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

from .newton_raphson import NewtonRaphsonSolver

# ============================================================

# PUBLIC PACKAGE API

# ============================================================

**all** = [
"SolverOptions",
"PowerMismatch",
"JacobianBuilder",
"SparseLinearSolver",
"QLimitHandler",
"NewtonRaphsonSolver",
]
