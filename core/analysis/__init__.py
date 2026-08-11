```python
"""
GridForge Analysis Layer
========================

File:
    core/analysis/__init__.py

Purpose
-------
Public entry point for the GridForge Analysis Layer.

The analysis layer provides engineering study APIs over the
frozen GridForge model and network infrastructure.

Architecture
------------

    core/model/
        ↓
    core/network/
        ↓
    core/analysis/
        ↓
    core/solver/

The Analysis Layer:
    - provides public study interfaces
    - validates analysis-level inputs
    - coordinates engineering calculations
    - delegates numerical mathematics to core.solver

The Analysis Layer does NOT:
    - own the electrical model
    - own network topology
    - build numerical solver algorithms
    - implement Newton-Raphson mathematics
    - implement sparse linear algebra
    - implement fault mathematics

Canonical public analysis APIs
------------------------------

    PowerFlowAnalysis
    LineFlowCalculator
    TransformerFlowCalculator
    ShortCircuitAnalysis
    ContingencyAnalysis

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations


# =====================================================================
# POWER FLOW
# =====================================================================

from core.analysis.power_flow import (
    PowerFlowAnalysis,
)


# =====================================================================
# LINE FLOW
# =====================================================================

from core.analysis.line_flow import (
    LineFlowCalculator,
    LineFlowResult,
)


# =====================================================================
# TRANSFORMER FLOW
# =====================================================================

from core.analysis.transformer_flow import (
    TransformerFlowCalculator,
)


# =====================================================================
# SHORT CIRCUIT
# =====================================================================

from core.analysis.short_circuit import (
    ShortCircuitAnalysis,
    ShortCircuitAnalyzer,
    FaultType,
)


# =====================================================================
# CONTINGENCY
# =====================================================================

from core.analysis.contingency import (
    ContingencyAnalysis,
    ContingencyResult,
    ContingencyCaseResult,
    ContingencyViolation,
)


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    # ---------------------------------------------------------------
    # Power Flow
    # ---------------------------------------------------------------

    "PowerFlowAnalysis",

    # ---------------------------------------------------------------
    # Line Flow
    # ---------------------------------------------------------------

    "LineFlowCalculator",
    "LineFlowResult",

    # ---------------------------------------------------------------
    # Transformer Flow
    # ---------------------------------------------------------------

    "TransformerFlowCalculator",

    # ---------------------------------------------------------------
    # Short Circuit
    # ---------------------------------------------------------------

    "ShortCircuitAnalysis",
    "ShortCircuitAnalyzer",
    "FaultType",

    # ---------------------------------------------------------------
    # Contingency
    # ---------------------------------------------------------------

    "ContingencyAnalysis",
    "ContingencyResult",
    "ContingencyCaseResult",
    "ContingencyViolation",
]
```
