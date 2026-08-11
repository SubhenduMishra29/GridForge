```python
"""
GridForge - Line Flow Analysis
==============================

Deterministic engineering calculation of branch power flow.

Purpose
-------
Calculates the electrical quantities at both ends of an in-service
transmission/distribution line using the solved bus voltages.

This module is NOT a power-flow solver.

It assumes that bus voltages have already been obtained from:

    core.analysis.power_flow
        ->
    core.solver.power_flow

Responsibilities
----------------
- Calculate line terminal currents
- Calculate sending/receiving-end complex power
- Calculate active-power loss
- Calculate reactive-power balance
- Provide engineering-friendly results

Numerical solver responsibilities remain in core/solver/.

Units
-----
Input:
    r_pu, x_pu, b_pu : per-unit line parameters
    bus voltages      : per-unit complex voltages

Output:
    P, Q, losses      : per-unit quantities
    I                 : per-unit current
"""


from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

import numpy as np


# =====================================================================
# RESULT
# =====================================================================

@dataclass
class LineFlowResult:
    """
    Result of a single line-flow calculation.

    All electrical quantities are in per-unit unless otherwise noted.
    """

    line_id: Any

    from_bus: Any
    to_bus: Any

    # Terminal currents
    current_from: complex
    current_to: complex

    # Sending-end power
    p_from: float
    q_from: float

    # Receiving-end power
    p_to: float
    q_to: float

    # Losses
    p_loss: float
    q_balance: float

    # Network status
    in_service: bool = True

    # ---------------------------------------------------------------
    # Convenience properties
    # ---------------------------------------------------------------

    @property
    def s_from(self) -> complex:
        """Sending-end complex power."""
        return complex(self.p_from, self.q_from)

    @property
    def s_to(self) -> complex:
        """Receiving-end complex power."""
        return complex(self.p_to, self.q_to)

    @property
    def current_from_magnitude(self) -> float:
        """Magnitude of sending-end current in pu."""
        return float(abs(self.current_from))

    @property
    def current_to_magnitude(self) -> float:
        """Magnitude of receiving-end current in pu."""
        return float(abs(self.current_to))

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result into a JSON-friendly dictionary.
        """

        data = asdict(self)

        data["current_from"] = {
            "real": float(self.current_from.real),
            "imag": float(self.current_from.imag),
        }

        data["current_to"] = {
            "real": float(self.current_to.real),
            "imag": float(self.current_to.imag),
        }

        data["s_from"] = {
            "real": float(self.s_from.real),
            "imag": float(self.s_from.imag),
        }

        data["s_to"] = {
            "real": float(self.s_to.real),
            "imag": float(self.s_to.imag),
        }

        data["current_from_magnitude"] = self.current_from_magnitude
        data["current_to_magnitude"] = self.current_to_magnitude

        return data


# =====================================================================
# LINE FLOW CALCULATOR
# =====================================================================

class LineFlowCalculator:
    """
    Calculate electrical flow through a single network line.

    The calculation uses the standard nominal-pi line representation.

    No Network state is modified by this class.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(self, network: Any):

        if network is None:
            raise ValueError(
                "LineFlowCalculator requires a valid network."
            )

        if not hasattr(network, "buses"):
            raise ValueError(
                "Network must provide a 'buses' collection."
            )

        if not hasattr(network, "lines"):
            raise ValueError(
                "Network must provide a 'lines' collection."
            )

        if not hasattr(network, "bus_index"):
            raise ValueError(
                "Network must provide an authoritative 'bus_index'."
            )

        self.network = network

    # =================================================================
    # SINGLE LINE
    # =================================================================

    def calculate(
        self,
        line: Any,
        V: np.ndarray,
    ) -> LineFlowResult:
        """
        Calculate flow through one line.

        Parameters
        ----------
        line:
            GridForge line model.

        V:
            Complex bus-voltage vector in per-unit.

        Returns
        -------
        LineFlowResult
            Calculated terminal currents, power flows and losses.
        """

        if line is None:
            raise ValueError("line cannot be None.")

        if V is None:
            raise ValueError(
                "Bus-voltage vector V cannot be None."
            )

        if not getattr(line, "in_service", True):
            raise ValueError(
                f"Line {getattr(line, 'id', '<unknown>')} "
                "is out of service."
            )

        try:
            i = self.network.bus_index[line.from_bus.id]
            j = self.network.bus_index[line.to_bus.id]
        except (AttributeError, KeyError) as exc:
            raise ValueError(
                "Line terminals must reference buses present "
                "in the network bus_index."
            ) from exc

        V = np.asarray(V, dtype=complex).reshape(-1)

        if i >= len(V) or j >= len(V):
            raise ValueError(
                "Bus-voltage vector does not contain all "
                "line terminal buses."
            )

        Vi = V[i]
        Vj = V[j]

        # -------------------------------------------------------------
        # LINE PARAMETERS
        # -------------------------------------------------------------

        r = float(getattr(line, "r_pu"))
        x = float(getattr(line, "x_pu"))
        b = float(getattr(line, "b_pu", 0.0))

        z = complex(r, x)

        if abs(z) == 0.0:
            raise ValueError(
                f"Line {getattr(line, 'id', '<unknown>')} "
                "has zero series impedance."
            )

        y_series = 1.0 / z

        # Nominal-pi model:
        # half shunt admittance at each terminal.
        y_shunt = 1j * b / 2.0

        # -------------------------------------------------------------
        # TERMINAL CURRENTS
        # -------------------------------------------------------------

        Iij = (Vi - Vj) * y_series + Vi * y_shunt

        Iji = (Vj - Vi) * y_series + Vj * y_shunt

        # -------------------------------------------------------------
        # COMPLEX POWER
        # -------------------------------------------------------------

        Sij = Vi * np.conj(Iij)

        Sji = Vj * np.conj(Iji)

        # -------------------------------------------------------------
        # LOSSES / BALANCE
        # -------------------------------------------------------------

        p_loss = float(np.real(Sij + Sji))

        q_balance = float(np.imag(Sij + Sji))

        return LineFlowResult(
            line_id=getattr(line, "id", None),

            from_bus=line.from_bus.id,
            to_bus=line.to_bus.id,

            current_from=complex(Iij),
            current_to=complex(Iji),

            p_from=float(np.real(Sij)),
            q_from=float(np.imag(Sij)),

            p_to=float(np.real(Sji)),
            q_to=float(np.imag(Sji)),

            p_loss=p_loss,
            q_balance=q_balance,

            in_service=True,
        )

    # =================================================================
    # ALL LINES
    # =================================================================

    def calculate_all(
        self,
        V: np.ndarray,
        include_out_of_service: bool = False,
    ) -> Dict[Any, LineFlowResult]:
        """
        Calculate flow for all network lines.

        Parameters
        ----------
        V:
            Complex bus-voltage vector in per-unit.

        include_out_of_service:
            If False, out-of-service lines are skipped.

        Returns
        -------
        Dict[Any, LineFlowResult]
            Results keyed by line ID.
        """

        results: Dict[Any, LineFlowResult] = {}

        for line in self.network.lines:

            if not getattr(line, "in_service", True):

                if include_out_of_service:
                    continue

                continue

            result = self.calculate(
                line=line,
                V=V,
            )

            results[result.line_id] = result

        return results

    # =================================================================
    # SUMMARY
    # =================================================================

    def summary(
        self,
        V: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Calculate all in-service line flows and return an
        engineering summary.
        """

        results = self.calculate_all(V)

        total_p_loss = float(
            sum(result.p_loss for result in results.values())
        )

        total_q_balance = float(
            sum(result.q_balance for result in results.values())
        )

        return {
            "line_count": len(results),
            "total_p_loss_pu": total_p_loss,
            "total_q_balance_pu": total_q_balance,
            "lines": {
                line_id: result.to_dict()
                for line_id, result in results.items()
            },
        }


__all__ = [
    "LineFlowResult",
    "LineFlowCalculator",
]
```
