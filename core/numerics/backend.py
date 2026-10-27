"""Backend-neutral capability and dispatch policy for numerical workloads.

This module deliberately does not probe devices or import accelerator runtimes.
Plugins/application adapters provide capability facts; this policy selects a
backend deterministically and records why alternatives were not selected.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, Literal, Protocol

if TYPE_CHECKING:
    from .ode import NumericalProblem, ODESolution

BackendKind = Literal["cpu", "gpu", "npu"]


@dataclass(frozen=True)
class BackendCapability:
    """Facts supplied by a runtime adapter for one compute backend."""

    name: str
    kind: BackendKind
    available: bool
    supported_workloads: frozenset[str]
    minimum_workload_size: int = 1
    precision_modes: frozenset[str] = frozenset({"float64"})

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("backend name must be non-empty")
        if self.kind not in ("cpu", "gpu", "npu"):
            raise ValueError("backend kind must be cpu, gpu, or npu")
        if isinstance(self.minimum_workload_size, bool) or not isinstance(
            self.minimum_workload_size, int
        ) or self.minimum_workload_size < 1:
            raise ValueError("minimum_workload_size must be a positive integer")
        if not self.supported_workloads:
            raise ValueError("supported_workloads must not be empty")
        if not self.precision_modes:
            raise ValueError("precision_modes must not be empty")


@dataclass(frozen=True)
class BackendSelection:
    """Selection result with a stable explanation suitable for diagnostics."""

    requested: str
    selected: BackendCapability
    reason: str
    rejected: tuple[tuple[str, str], ...]


def select_backend(
    capabilities: Iterable[BackendCapability],
    *,
    workload: str,
    workload_size: int = 1,
    precision: str = "float64",
    requested: str = "auto",
    preference: tuple[str, ...] = ("gpu", "npu", "cpu"),
) -> BackendSelection:
    """Select a compatible backend without importing or probing runtimes.

    The caller must provide a CPU capability if CPU fallback is required.
    Explicit requests are honored only when the requested capability is
    available and supports the workload, precision, and minimum batch size.
    An incompatible explicit request falls back to CPU if available, otherwise
    raises ValueError. The returned rejection reasons should be surfaced in
    application/study diagnostics rather than silently discarded.
    """
    if not isinstance(workload, str) or not workload.strip():
        raise ValueError("workload must be a non-empty string")
    if isinstance(workload_size, bool) or not isinstance(workload_size, int) or workload_size < 1:
        raise ValueError("workload_size must be a positive integer")
    if not isinstance(precision, str) or not precision.strip():
        raise ValueError("precision must be a non-empty string")
    if requested != "auto" and requested not in ("cpu", "gpu", "npu"):
        raise ValueError("requested must be auto, cpu, gpu, or npu")

    items = tuple(capabilities)
    names = [item.name for item in items]
    if len(names) != len(set(names)):
        raise ValueError("backend capability names must be unique")
    if not items:
        raise ValueError("at least one backend capability is required")

    rejected: list[tuple[str, str]] = []

    def reason_for(item: BackendCapability) -> str | None:
        if not item.available:
            return "runtime_unavailable"
        if workload not in item.supported_workloads:
            return "workload_unsupported"
        if precision not in item.precision_modes:
            return "precision_unsupported"
        if workload_size < item.minimum_workload_size:
            return "workload_below_minimum"
        return None

    ordered: list[BackendCapability]
    if requested == "auto":
        rank = {kind: i for i, kind in enumerate(preference)}
        ordered = sorted(items, key=lambda item: (rank.get(item.kind, len(rank)), item.name))
    else:
        ordered = sorted(
            items,
            key=lambda item: (item.kind != requested, item.name),
        )

    compatible: list[BackendCapability] = []
    for item in ordered:
        issue = reason_for(item)
        if issue is None:
            compatible.append(item)
        else:
            rejected.append((item.name, issue))

    if requested != "auto":
        explicit = next((item for item in items if item.kind == requested), None)
        if explicit is not None and explicit in compatible:
            return BackendSelection(requested, explicit, "explicit_request_supported", tuple(rejected))
        cpu = next((item for item in items if item.kind == "cpu" and item in compatible), None)
        if cpu is None:
            raise ValueError(
                f"requested backend {requested!r} is unsupported and no compatible CPU fallback exists"
            )
        return BackendSelection(requested, cpu, "explicit_request_cpu_fallback", tuple(rejected))

    if not compatible:
        raise ValueError("no available backend supports the requested workload and precision")
    return BackendSelection(requested, compatible[0], "automatic_capability_selection", tuple(rejected))


@dataclass(frozen=True)
class NumericalExecution:
    """Validated solution plus transparent dispatch/fallback metadata."""

    solution: "ODESolution"
    selection: BackendSelection
    executed_backend: str
    fallback_failure: str | None = None


def execute_numerical_problem(
    problem: "NumericalProblem",
    adapters: Iterable["NumericalBackendAdapter"],
    *,
    requested: str = "auto",
    preference: tuple[str, ...] = ("gpu", "npu", "cpu"),
) -> NumericalExecution:
    """Dispatch one shared ODE problem through registered backend adapters.

    The CPU adapter is the reference fallback. A non-CPU adapter failure or
    incompatible result is recorded and retried on a compatible CPU adapter.
    This helper validates the adapter result contract but cannot prove that an
    accelerator's derivative implementation is physically equivalent to the
    supplied Python derivative; workload compatibility must be declared by
    the adapter.
    """
    from .ode import NumericalProblem, ODESolution, uniform_time_grid

    if not isinstance(problem, NumericalProblem):
        raise TypeError("problem must be a NumericalProblem")
    registered = tuple(adapters)
    if not registered:
        raise ValueError("at least one numerical backend adapter is required")
    for adapter in registered:
        if not isinstance(adapter.capability, BackendCapability):
            raise TypeError("adapter capability must be BackendCapability")
        if not callable(getattr(adapter, "solve", None)):
            raise TypeError("every backend adapter must implement solve(problem)")

    selection = select_backend(
        (adapter.capability for adapter in registered),
        workload=problem.workload,
        workload_size=int(np.asarray(problem.initial_state).size),
        precision=problem.precision,
        requested=requested,
        preference=preference,
    )
    by_name = {adapter.capability.name: adapter for adapter in registered}
    selected = by_name[selection.selected.name]

    def run(adapter: "NumericalBackendAdapter") -> "ODESolution":
        solution = adapter.solve(problem)
        if not isinstance(solution, ODESolution):
            raise TypeError("backend adapter must return ODESolution")
        expected_times, expected_step = uniform_time_grid(
            problem.duration_s, problem.maximum_step_s
        )
        if solution.state_count != np.asarray(problem.initial_state).size:
            raise ValueError("backend returned an incompatible state count")
        if solution.time_s.shape != expected_times.shape or not np.array_equal(
            solution.time_s, expected_times
        ):
            raise ValueError("backend returned a time grid that violates the shared ODE contract")
        expected_size = expected_times.size * solution.state_count
        if solution.state_data.ndim != 1 or solution.state_data.size != expected_size:
            raise ValueError("backend returned an invalid flat state buffer")
        if not np.isfinite(solution.state_data).all():
            raise FloatingPointError("backend returned non-finite states")
        if not isfinite(float(solution.sample_period_s)) or not np.isclose(
            solution.sample_period_s, expected_step, rtol=0.0, atol=0.0
        ):
            raise ValueError("backend returned an incompatible sample period")
        return solution

    try:
        solution = run(selected)
        return NumericalExecution(solution, selection, selected.capability.name)
    except Exception as exc:
        if selected.capability.kind == "cpu":
            raise
        cpu = next(
            (
                adapter for adapter in registered
                if adapter.capability.kind == "cpu"
                and adapter.capability.available
                and problem.workload in adapter.capability.supported_workloads
                and problem.precision in adapter.capability.precision_modes
                and problem.initial_state is not None
            ),
            None,
        )
        if cpu is None:
            raise RuntimeError(
                f"backend {selected.capability.name!r} failed and no compatible CPU adapter exists"
            ) from exc
        solution = run(cpu)
        return NumericalExecution(
            solution,
            selection,
            cpu.capability.name,
            f"{type(exc).__name__}: {str(exc)[:512]}",
        )



class NumericalBackendAdapter(Protocol):
    """Contract implemented by CPU/GPU/NPU adapters for compatible problems.

    Adapters must report capability facts without making the shared policy
    probe hardware. solve() must preserve the problem's state ordering, time
    grid, precision declaration, and input-sampling semantics, or reject the
    problem explicitly. Implementations own runtime-specific failures.
    """

    @property
    def capability(self) -> BackendCapability:
        """Return the adapter's current runtime capability declaration."""
        ...

    def solve(self, problem: "NumericalProblem") -> "ODESolution":
        """Execute a compatible numerical problem and return its solution."""
        ...


__all__ = ["BackendCapability", "BackendSelection", "BackendKind", "NumericalBackendAdapter", "NumericalExecution", "execute_numerical_problem", "select_backend"]
