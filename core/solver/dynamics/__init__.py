"""
GridForge Dynamic Solver
========================

GridForge V2 dynamic simulation subsystem.

Public API
----------

The dynamics package provides:

    - dynamic state representation;
    - numerical integration;
    - synchronous-machine models;
    - multi-machine coordination;
    - swing-equation dynamics;
    - event scheduling;
    - DAE coordination;
    - transient-stability study orchestration.

Architecture
------------

    transient_stability
            │
            ▼
        dae_solver
            │
       ┌────┴────┐
       ▼         ▼
    multimachine integrator
       │
       ▼
 machine_models
       │
       ▼
 swing_equation

The package deliberately does not include AVR, governor, or PSS
implementations. Such control-system models belong to separate
dynamic-control components/plugins and are not hard-coded into the
core dynamic solver.
"""


# ======================================================================
# STATE
# ======================================================================

from .state_vector import (
    DynamicState,
)


# ======================================================================
# NUMERICAL INTEGRATION
# ======================================================================

from .integrator import (
    Integrator,
    RK4Integrator,
    TrapezoidalIntegrator,
)


# ======================================================================
# MACHINE DYNAMICS
# ======================================================================

from .swing_equation import (
    SwingEquation,
)

from .machine_models import (
    ClassicalMachine,
)


# ======================================================================
# MULTI-MACHINE SYSTEM
# ======================================================================

from .multimachine import (
    MultiMachineSystem,
)


# ======================================================================
# EVENTS
# ======================================================================

from .events import (
    Event,
    EventExecution,
    EventManager,
)


# ======================================================================
# DAE SOLVER
# ======================================================================

from .dae_solver import (
    NetworkSolver,
    MechanicalPowerMap,
    DAESolverError,
    DAEConfigurationError,
    DAEAlgebraicError,
    DAENumericalError,
    DAESolution,
    DAESolver,
)


# ======================================================================
# TRANSIENT STABILITY
# ======================================================================

from .transient_stability import (
    ComplexVoltageMap,
    TransientStabilityError,
    SimulationConfigurationError,
    SimulationNumericalError,
    TransientStabilityConfig,
    SimulationSnapshot,
    TransientStabilityResult,
    TransientStabilityStudy,
    create_transient_stability_study,
)


# ======================================================================
# PUBLIC API
# ======================================================================

__all__ = [

    # --------------------------------------------------------------
    # State
    # --------------------------------------------------------------

    "DynamicState",

    # --------------------------------------------------------------
    # Integration
    # --------------------------------------------------------------

    "Integrator",
    "RK4Integrator",
    "TrapezoidalIntegrator",

    # --------------------------------------------------------------
    # Machine dynamics
    # --------------------------------------------------------------

    "SwingEquation",
    "ClassicalMachine",

    # --------------------------------------------------------------
    # Multi-machine system
    # --------------------------------------------------------------

    "MultiMachineSystem",

    # --------------------------------------------------------------
    # Events
    # --------------------------------------------------------------

    "Event",
    "EventExecution",
    "EventManager",

    # --------------------------------------------------------------
    # DAE solver
    # --------------------------------------------------------------

    "NetworkSolver",
    "MechanicalPowerMap",
    "DAESolverError",
    "DAEConfigurationError",
    "DAEAlgebraicError",
    "DAENumericalError",
    "DAESolution",
    "DAESolver",

    # --------------------------------------------------------------
    # Transient stability
    # --------------------------------------------------------------

    "ComplexVoltageMap",
    "TransientStabilityError",
    "SimulationConfigurationError",
    "SimulationNumericalError",
    "TransientStabilityConfig",
    "SimulationSnapshot",
    "TransientStabilityResult",
    "TransientStabilityStudy",
    "create_transient_stability_study",
]
```
