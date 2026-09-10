"""GridForge short-circuit numerical package.

Canonical execution boundary:

    ShortCircuitInput -> ShortCircuitSolver -> ShortCircuitResult

SequenceNetwork is preparation state; SequenceNetworkSnapshot is the immutable
execution representation.
"""

from .fault_types import FaultType
from .sequence_network import SequenceNetwork
from .sequence_snapshot import (
    SequenceBranchSnapshot,
    SequenceNetworkSnapshot,
    SequenceSourceSnapshot,
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
)
from .short_circuit_solver import ShortCircuitSolver
from .short_circuit import ShortCircuit

__all__ = [
    "FaultType",
    "SequenceNetwork",
    "SequenceBranchSnapshot",
    "SequenceSourceSnapshot",
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
    "ShortCircuitResult",
    "ShortCircuitSolver",
    "ShortCircuit",
]
