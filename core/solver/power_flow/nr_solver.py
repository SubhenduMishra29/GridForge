"""Numerical-only Newton-Raphson AC power-flow solver."""

from __future__ import annotations

import numpy as np

from core.solver.common.jacobian import JacobianBuilder
from core.solver.common.mismatch import PowerMismatch
from core.solver.power_flow.input import PowerFlowInput
from core.solver.power_flow.q_limit_handler import QLimitHandler
from core.solver.power_flow.result import PowerFlowResult
from core.solver.power_flow.runtime_state import PowerFlowRuntimeState
from core.solver.power_flow.sparse_solver import SparseLinearSolver


class NewtonRaphsonSolver:
    """Execute Newton-Raphson using only prepared numerical contracts."""

    def __init__(self, input_data: PowerFlowInput, ybus, options, runtime_state: PowerFlowRuntimeState | None = None):
        if not isinstance(input_data, PowerFlowInput):
            raise TypeError("input_data must be PowerFlowInput.")
        if options is None or not callable(getattr(options, "validate", None)):
            raise TypeError("options must provide validate().")
        self.input = input_data
        self.Ybus = ybus
        self.options = options
        self.runtime_state = runtime_state or PowerFlowRuntimeState.from_input(input_data)
        self.linear_solver = SparseLinearSolver(regularization=options.regularization)
        self.q_handler = QLimitHandler(input_data, self.runtime_state, tolerance=options.q_limit_tolerance, ybus=ybus)
        self.history: list[float] = []
        self._converted_pv: list[dict] = []
        self._validate_contracts()

    def _validate_contracts(self):
        n = self.input.bus_count
        if getattr(self.Ybus, "shape", None) != (n, n):
            raise ValueError("Ybus dimension does not match PowerFlowInput.")
        if not hasattr(self.Ybus, "bus_ids") or tuple(self.Ybus.bus_ids) != self.input.bus_ids:
            raise ValueError("PowerFlowInput bus ordering does not match Ybus bus ordering.")
        self.runtime_state.validate(n)

    def _components(self):
        return PowerMismatch(self.input, self.Ybus, self.runtime_state), JacobianBuilder(self.input, self.Ybus, self.runtime_state)

    def _result(self, success: bool, iterations: int, error: float, message: str, mismatch_engine: PowerMismatch | None = None):
        if mismatch_engine is not None:
            vm = tuple(float(x) for x in self.runtime_state.vm)
            va = tuple(float(x) for x in self.runtime_state.va)
        else:
            vm = tuple(float(x) for x in self.runtime_state.vm)
            va = tuple(float(x) for x in self.runtime_state.va)
        return PowerFlowResult(success=success, iterations=iterations, error=float(error), pv_to_pq=tuple(self._converted_pv), history=tuple(self.history), message=message, voltage_magnitudes=vm, voltage_angles=va)

    def solve(self) -> PowerFlowResult:
        self.options.validate()
        self.linear_solver.regularization = float(self.options.regularization)
        self.q_handler.tolerance = float(self.options.q_limit_tolerance)
        self.history.clear()
        self._converted_pv.clear()
        self.q_handler.reset_history()
        self._validate_contracts()
        self.runtime_state.validate(self.input.bus_count)
        mismatch_engine, jacobian_builder = self._components()
        last_error = float("inf")
        for iteration in range(1, self.options.max_iterations + 1):
            self.runtime_state.set_iteration(iteration)
            try:
                mismatch = np.asarray(mismatch_engine.compute(), dtype=float).reshape(-1)
            except Exception as exc:
                return self._result(False, iteration, last_error, f"Mismatch calculation failed: {exc}", mismatch_engine)
            if not np.all(np.isfinite(mismatch)):
                return self._result(False, iteration, float("inf"), "Mismatch calculation produced NaN or infinite values.", mismatch_engine)
            error = self.runtime_state.set_mismatch(mismatch)
            last_error = error
            self.history.append(error)
            if self.options.verbose:
                print(f"Iteration {iteration}: Mismatch={error:.6e}")
            if error <= self.options.tolerance:
                self.runtime_state.converged = True
                self.runtime_state.message = "Converged."
                return self._result(True, iteration, error, "Converged.", mismatch_engine)
            if self.options.enforce_q_limits:
                try:
                    changed = self.q_handler.check_limits()
                except Exception as exc:
                    return self._result(False, iteration, error, f"Reactive-power limit handling failed: {exc}", mismatch_engine)
                if changed:
                    self._converted_pv.extend(changed)
                    continue
            try:
                jacobian = np.asarray(jacobian_builder.build(), dtype=float)
                expected = mismatch.size
                if jacobian.shape != (expected, expected):
                    raise ValueError(f"Jacobian dimension does not match mismatch vector: expected {(expected, expected)}, received {jacobian.shape}.")
                if not np.all(np.isfinite(jacobian)):
                    raise ValueError("Jacobian contains NaN or infinite values.")
                dx = np.asarray(self.linear_solver.solve(jacobian, mismatch), dtype=float).reshape(-1)
                if dx.size != expected or not np.all(np.isfinite(dx)):
                    raise ValueError("Newton-Raphson correction has invalid dimension or non-finite values.")
                angle_indices, voltage_indices = jacobian_builder.state_indices()
                self.runtime_state.apply_correction(angle_indices, voltage_indices, dx, self.options.damping)
            except Exception as exc:
                return self._result(False, iteration, error, f"Newton iteration failed: {exc}", mismatch_engine)
        self.runtime_state.converged = False
        self.runtime_state.message = "Maximum iterations reached."
        return self._result(False, self.options.max_iterations, last_error, "Maximum iterations reached.", mismatch_engine)

    def summary(self):
        return {
            "solver": "Newton-Raphson",
            "buses": self.input.bus_count,
            "tolerance": self.options.tolerance,
            "max_iterations": self.options.max_iterations,
            "damping": self.options.damping,
            "regularization": self.options.regularization,
            "enforce_q_limits": self.options.enforce_q_limits,
            "q_limit_tolerance": self.options.q_limit_tolerance,
            "iterations_completed": self.runtime_state.iteration,
            "last_mismatch": self.runtime_state.residual,
            "pv_to_pq_conversions": len(self._converted_pv),
        }

    def __repr__(self):
        return f"NewtonRaphsonSolver(buses={self.input.bus_count})"
