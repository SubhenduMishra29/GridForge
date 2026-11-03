"""GridForge short-circuit numerical package.

Canonical execution boundary:

    ShortCircuitInput -> ShortCircuitSolver -> ShortCircuitResult

SequenceNetwork is preparation state; SequenceNetworkSnapshot is the immutable
execution representation. Phase-domain solver exports are loaded lazily because
their immutable preparation snapshots are owned by core.analysis. Eagerly
loading them here would make package initialization cyclic when Analysis imports
the short-circuit facade.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from .fault_types import FaultType
from .sequence_network import SequenceNetwork
from .sequence_snapshot import (
    SequenceBranchSnapshot,
    SequenceNetworkSnapshot,
    SequenceSourceSnapshot,
    SequenceTransformerZeroShuntSnapshot,
    SequenceTransformerZeroTwoBusSnapshot,
)
from .impedance_matrix import ImpedanceMatrix
from .symmetrical_fault import SymmetricalFault
from .unsymmetrical_fault import UnsymmetricalFault
from .input import ShortCircuitInput
from .result import (
    ContributionStatus,
    ShortCircuitStatus,
    ShortCircuitBranchCurrent,
    ShortCircuitEquipmentCurrent,
    ShortCircuitResult,
    ShortCircuitSourceContribution,
    ShortCircuitTerminalCurrent,
    ShortCircuitConductorCurrent,
    ShortCircuitTransformerDeltaLoopCurrent,
)
from .short_circuit_solver import ShortCircuitSolver
from .short_circuit import ShortCircuit
from .rl_transient import (
    RLPhaseEquivalent, RLTransientSample, RLPhaseTransient,
    RLTransientFaultResult, solve_rl_fault_transient,
)

_PHASE_DOMAIN_EXPORTS = frozenset({
    "PhaseDomainSourceEquivalent",
    "PhaseDomainMultiConductorSource",
    "PhaseDomainGroundedMultiConductorSource",
    "PhaseDomainTransformerMultiport",
    "PhaseDomainFaultConnection",
    "PhaseDomainShortCircuitCase",
    "PhaseDomainShortCircuitSolution",
    "PhaseDomainShortCircuitSolver",
})


def __getattr__(name: str) -> Any:
    """Resolve Analysis-backed phase-domain snapshot types on first use."""
    if name in _PHASE_DOMAIN_EXPORTS:
        module = import_module(".phase_domain_solver", __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _PHASE_DOMAIN_EXPORTS)


__all__ = [
    "FaultType",
    "SequenceNetwork",
    "SequenceBranchSnapshot",
    "SequenceSourceSnapshot",
    "SequenceTransformerZeroShuntSnapshot",
    "SequenceTransformerZeroTwoBusSnapshot",
    "SequenceNetworkSnapshot",
    "ImpedanceMatrix",
    "SymmetricalFault",
    "UnsymmetricalFault",
    "ShortCircuitInput",
    "ShortCircuitStatus",
    "ContributionStatus",
    "ShortCircuitSourceContribution",
    "ShortCircuitEquipmentCurrent",
    "ShortCircuitBranchCurrent",
    "ShortCircuitTerminalCurrent",
    "ShortCircuitConductorCurrent",
    "ShortCircuitTransformerDeltaLoopCurrent",
    "ShortCircuitResult",
    "ShortCircuitSolver",
    "PhaseDomainSourceEquivalent",
    "PhaseDomainMultiConductorSource",
    "PhaseDomainGroundedMultiConductorSource",
    "PhaseDomainTransformerMultiport",
    "PhaseDomainFaultConnection",
    "PhaseDomainShortCircuitCase",
    "PhaseDomainShortCircuitSolution",
    "PhaseDomainShortCircuitSolver",
    "ShortCircuit",
    "RLPhaseEquivalent", "RLTransientSample", "RLPhaseTransient",
    "RLTransientFaultResult", "solve_rl_fault_transient",
]
