"""
GridForge Line Flow Analysis
============================

File: core/analysis/line_flow.py
Author: Subhendu Mishra

Line terminal-flow calculations consume the detached numerical state
prepared by PowerFlowPreparation. Live Line electrical quantities are
never read by this calculator.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict

import numpy as np

from core.analysis.power_flow_preparation import PreparedBranch, PreparedPowerFlow


@dataclass
class LineFlowResult:
    """Result of a single nominal-pi line-flow calculation."""

    line_id: Any
    from_bus: Any
    to_bus: Any
    current_from: complex
    current_to: complex
    p_from: float
    q_from: float
    p_to: float
    q_to: float
    p_loss: float
    q_balance: float
    in_service: bool = True

    @property
    def s_from(self) -> complex:
        return complex(self.p_from, self.q_from)

    @property
    def s_to(self) -> complex:
        return complex(self.p_to, self.q_to)

    @property
    def current_from_magnitude(self) -> float:
        return float(abs(self.current_from))

    @property
    def current_to_magnitude(self) -> float:
        return float(abs(self.current_to))

    @property
    def s_from_magnitude(self) -> float:
        return float(abs(self.s_from))

    @property
    def s_to_magnitude(self) -> float:
        return float(abs(self.s_to))

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["current_from"] = {"real": float(self.current_from.real), "imag": float(self.current_from.imag)}
        data["current_to"] = {"real": float(self.current_to.real), "imag": float(self.current_to.imag)}
        data["s_from"] = {"real": float(self.s_from.real), "imag": float(self.s_from.imag)}
        data["s_to"] = {"real": float(self.s_to.real), "imag": float(self.s_to.imag)}
        data["current_from_magnitude"] = self.current_from_magnitude
        data["current_to_magnitude"] = self.current_to_magnitude
        data["s_from_magnitude"] = self.s_from_magnitude
        data["s_to_magnitude"] = self.s_to_magnitude
        return data


class LineFlowCalculator:
    """Calculate line flows from a detached PreparedPowerFlow snapshot."""

    _IMPEDANCE_TOLERANCE = 1.0e-12

    def __init__(self, network: Any = None, prepared: PreparedPowerFlow | None = None) -> None:
        if prepared is None:
            raise ValueError(
                "LineFlowCalculator requires a PreparedPowerFlow snapshot; "
                "live Line electrical parameters are not a numerical source."
            )
        if not isinstance(prepared, PreparedPowerFlow):
            raise TypeError("prepared must be a PreparedPowerFlow instance.")
        self.network = network
        self.prepared = prepared
        self._branches = {branch.branch_id: branch for branch in prepared.branches}
        self._bus_index = {bus_id: index for index, bus_id in enumerate(prepared.bus_ids)}

    @classmethod
    def from_prepared(cls, prepared: PreparedPowerFlow, network: Any = None) -> "LineFlowCalculator":
        return cls(network=network, prepared=prepared)

    def calculate(self, line: Any, V: np.ndarray) -> LineFlowResult:
        """Calculate one line using the matching PreparedBranch."""
        line_id = getattr(line, "id", line)
        branch = self._prepared_branch(line_id)
        return self.calculate_prepared(branch, V)

    def calculate_prepared(self, branch: PreparedBranch, V: np.ndarray) -> LineFlowResult:
        if not isinstance(branch, PreparedBranch):
            raise TypeError("branch must be a PreparedBranch instance.")
        if not branch.in_service:
            raise ValueError(f"Line '{branch.branch_id}' is out of service.")

        V = self._validate_voltage_vector(V)
        try:
            i = self._bus_index[branch.from_bus_id]
            j = self._bus_index[branch.to_bus_id]
        except KeyError as exc:
            raise ValueError(f"Prepared line '{branch.branch_id}' references an unknown bus.") from exc

        Vi, Vj = V[i], V[j]
        z = complex(branch.r_pu, branch.x_pu)
        if abs(z) <= self._IMPEDANCE_TOLERANCE:
            raise ValueError(f"Line '{branch.branch_id}' has zero or near-zero series impedance.")
        y_series = 1.0 / z
        y_shunt = 1j * branch.b_pu / 2.0
        I_from = (Vi - Vj) * y_series + Vi * y_shunt
        I_to = (Vj - Vi) * y_series + Vj * y_shunt
        S_from = Vi * np.conj(I_from)
        S_to = Vj * np.conj(I_to)
        total = S_from + S_to

        return LineFlowResult(
            line_id=branch.branch_id,
            from_bus=branch.from_bus_id,
            to_bus=branch.to_bus_id,
            current_from=complex(I_from),
            current_to=complex(I_to),
            p_from=float(S_from.real),
            q_from=float(S_from.imag),
            p_to=float(S_to.real),
            q_to=float(S_to.imag),
            p_loss=float(total.real),
            q_balance=float(total.imag),
            in_service=True,
        )

    def calculate_all(self, V: np.ndarray, include_out_of_service: bool = False) -> Dict[Any, LineFlowResult]:
        V = self._validate_voltage_vector(V)
        results: Dict[Any, LineFlowResult] = {}
        for branch in self.prepared.branches:
            if not branch.in_service:
                if include_out_of_service:
                    results[branch.branch_id] = LineFlowResult(
                        line_id=branch.branch_id,
                        from_bus=branch.from_bus_id,
                        to_bus=branch.to_bus_id,
                        current_from=0j,
                        current_to=0j,
                        p_from=0.0,
                        q_from=0.0,
                        p_to=0.0,
                        q_to=0.0,
                        p_loss=0.0,
                        q_balance=0.0,
                        in_service=False,
                    )
                continue
            results[branch.branch_id] = self.calculate_prepared(branch, V)
        return results

    def summary(self, V: np.ndarray) -> Dict[str, Any]:
        results = self.calculate_all(V)
        return {
            "line_count": len(results),
            "total_p_loss_pu": float(sum(result.p_loss for result in results.values())),
            "total_q_balance_pu": float(sum(result.q_balance for result in results.values())),
            "lines": {line_id: result.to_dict() for line_id, result in results.items()},
        }

    def _prepared_branch(self, line_id: Any) -> PreparedBranch:
        try:
            return self._branches[str(line_id)]
        except KeyError as exc:
            raise ValueError(
                f"Line '{line_id}' is absent from PreparedPowerFlow; "
                "prepare the case before calculating flow."
            ) from exc

    def _validate_voltage_vector(self, V: np.ndarray) -> np.ndarray:
        if V is None:
            raise ValueError("Bus-voltage vector V cannot be None.")
        vector = np.asarray(V, dtype=complex).reshape(-1)
        expected = len(self.prepared.bus_ids)
        if vector.size != expected:
            raise ValueError(
                "Bus-voltage vector length does not match prepared bus count: "
                f"expected {expected}, received {vector.size}."
            )
        if not np.all(np.isfinite(vector)):
            raise ValueError("Bus-voltage vector contains NaN or infinite values.")
        return vector

    def __repr__(self) -> str:
        return f"LineFlowCalculator(lines={len(self.prepared.branches)}, buses={len(self.prepared.bus_ids)})"


__all__ = ["LineFlowResult", "LineFlowCalculator"]
