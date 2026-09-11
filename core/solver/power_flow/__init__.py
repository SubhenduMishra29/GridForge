"""Power-flow numerical contracts, preparation, and solver components."""

from .input import PowerFlowBusType, PowerFlowInput
from .nr_solver import NewtonRaphsonSolver
from .q_limit_handler import QLimitHandler
from .result import PowerFlowResult
from .runtime_state import PowerFlowRuntimeState
from .solver_options import SolverOptions
from .sparse_solver import SparseLinearSolver
from .study_configuration import PowerFlowStudyConfiguration


def __getattr__(name: str):
    """Lazily expose preparation contracts to avoid package import cycles."""
    if name in {"PowerFlowPreparation", "PreparedPowerFlow"}:
        from .preparation import PowerFlowPreparation, PreparedPowerFlow
        return {
            "PowerFlowPreparation": PowerFlowPreparation,
            "PreparedPowerFlow": PreparedPowerFlow,
        }[name]
    raise AttributeError(name)


__all__ = [
    "PowerFlowBusType",
    "PowerFlowInput",
    "PowerFlowStudyConfiguration",
    "PowerFlowPreparation",
    "PreparedPowerFlow",
    "PowerFlowRuntimeState",
    "PowerFlowResult",
    "NewtonRaphsonSolver",
    "QLimitHandler",
    "SolverOptions",
    "SparseLinearSolver",
]
