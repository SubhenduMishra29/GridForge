```python
"""
GridForge Line Flow Analysis
============================

File:
    core/analysis/line_flow.py

Purpose
-------
Deterministic engineering calculation of branch power flow.

This module calculates electrical quantities at both terminals of an
in-service network line using solved bus voltages.

This module is NOT a power-flow solver.

The bus voltages are assumed to have already been obtained from:

    core.analysis.power_flow
        ->
    core.solver.power_flow

Responsibilities
----------------
- Calculate line terminal currents
- Calculate sending-end and receiving-end complex power
- Calculate active-power loss
- Calculate reactive-power balance
- Provide engineering-friendly line-flow results

Numerical solver responsibilities remain in core/solver/.

Electrical Model
----------------
The line is represented by the standard nominal-pi model:

    y_series = 1 / (r + jx)

    y_shunt = jb / 2

Terminal currents:

    I_from = (V_from - V_to) * y_series
             + V_from * y_shunt

    I_to   = (V_to - V_from) * y_series
             + V_to * y_shunt

Terminal complex powers:

    S_from = V_from * conj(I_from)

    S_to   = V_to * conj(I_to)

All electrical quantities are calculated in per-unit.

Architecture
------------
Network
    |
    v
LineFlowCalculator
    |
    v
LineFlowResult

The calculation does not modify Network, Bus, or Line state.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict

import numpy as np


# =====================================================================
# RESULT
# =====================================================================


@dataclass
class LineFlowResult:
    """
    Result of a single line-flow calculation.

    Electrical quantities are in per-unit unless explicitly stated.
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

    # Loss / reactive balance
    p_loss: float
    q_balance: float

    # Network status
    in_service: bool = True

    # -----------------------------------------------------------------
    # Convenience properties
    # -----------------------------------------------------------------

    @property
    def s_from(self) -> complex:
        """Sending-end complex power in pu."""
        return complex(self.p_from, self.q_from)

    @property
    def s_to(self) -> complex:
        """Receiving-end complex power in pu."""
        return complex(self.p_to, self.q_to)

    @property
    def current_from_magnitude(self) -> float:
        """Sending-end current magnitude in pu."""
        return float(abs(self.current_from))

    @property
    def current_to_magnitude(self) -> float:
        """Receiving-end current magnitude in pu."""
        return float(abs(self.current_to))

    @property
    def s_from_magnitude(self) -> float:
        """Sending-end apparent power magnitude in pu."""
        return float(abs(self.s_from))

    @property
    def s_to_magnitude(self) -> float:
        """Receiving-end apparent power magnitude in pu."""
        return float(abs(self.s_to))

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result to a serialization-friendly dictionary.

        Complex numbers are represented as real/imaginary pairs.
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

        data["current_from_magnitude"] = (
            self.current_from_magnitude
        )

        data["current_to_magnitude"] = (
            self.current_to_magnitude
        )

        data["s_from_magnitude"] = (
            self.s_from_magnitude
        )

        data["s_to_magnitude"] = (
            self.s_to_magnitude
        )

        return data


# =====================================================================
# LINE FLOW CALCULATOR
# =====================================================================


class LineFlowCalculator:
    """
    Calculate electrical flow through GridForge network lines.

    The calculation uses the standard nominal-pi line representation.

    No Network, Bus, or Line state is modified.
    """

    _IMPEDANCE_TOLERANCE = 1.0e-12

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(self, network: Any) -> None:

        if network is None:
            raise ValueError(
                "LineFlowCalculator requires a valid Network."
            )

        required = (
            "buses",
            "lines",
            "bus_index",
        )

        for attribute in required:

            if not hasattr(network, attribute):
                raise ValueError(
                    "Network is missing required "
                    f"attribute '{attribute}'."
                )

        if not network.buses:
            raise ValueError(
                "LineFlowCalculator requires at least one bus."
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
        Calculate electrical flow through one line.

        Parameters
        ----------
        line:
            GridForge Line model instance.

        V:
            Complex bus-voltage vector in per-unit.

        Returns
        -------
        LineFlowResult
            Terminal currents, power flows, and losses.

        Raises
        ------
        ValueError
            If the line, voltage vector, terminal buses, or line
            electrical parameters are invalid.
        """

        if line is None:
            raise ValueError(
                "line cannot be None."
            )

        if V is None:
            raise ValueError(
                "Bus-voltage vector V cannot be None."
            )

        line_id = getattr(
            line,
            "id",
            "<unknown>",
        )

        # -------------------------------------------------------------
        # SERVICE STATE
        # -------------------------------------------------------------

        if not getattr(
            line,
            "in_service",
            True,
        ):
            raise ValueError(
                f"Line '{line_id}' is out of service."
            )

        # -------------------------------------------------------------
        # TERMINALS
        # -------------------------------------------------------------

        if not hasattr(
            line,
            "from_bus",
        ):
            raise ValueError(
                f"Line '{line_id}' is missing 'from_bus'."
            )

        if not hasattr(
            line,
            "to_bus",
        ):
            raise ValueError(
                f"Line '{line_id}' is missing 'to_bus'."
            )

        from_bus = line.from_bus
        to_bus = line.to_bus

        if not hasattr(from_bus, "id"):
            raise ValueError(
                f"Line '{line_id}' from_bus is missing 'id'."
            )

        if not hasattr(to_bus, "id"):
            raise ValueError(
                f"Line '{line_id}' to_bus is missing 'id'."
            )

        # -------------------------------------------------------------
        # AUTHORITATIVE BUS INDEX
        # -------------------------------------------------------------

        try:

            i = self.network.bus_index[
                from_bus.id
            ]

            j = self.network.bus_index[
                to_bus.id
            ]

        except KeyError as exc:

            raise ValueError(
                f"Line '{line_id}' references a bus that "
                "is not present in network.bus_index."
            ) from exc

        # -------------------------------------------------------------
        # VOLTAGE VECTOR
        # -------------------------------------------------------------

        V = np.asarray(
            V,
            dtype=complex,
        ).reshape(-1)

        expected = len(
            self.network.buses
        )

        if V.size != expected:
            raise ValueError(
                "Bus-voltage vector length does not match "
                f"network bus count: expected {expected}, "
                f"received {V.size}."
            )

        if not np.all(
            np.isfinite(V)
        ):
            raise ValueError(
                "Bus-voltage vector contains NaN or "
                "infinite values."
            )

        Vi = V[i]
        Vj = V[j]

        # -------------------------------------------------------------
        # LINE PARAMETERS
        # -------------------------------------------------------------

        for attribute in (
            "r_pu",
            "x_pu",
        ):

            if not hasattr(
                line,
                attribute,
            ):
                raise ValueError(
                    f"Line '{line_id}' is missing "
                    f"required parameter '{attribute}'."
                )

        try:

            r = float(
                line.r_pu
            )

            x = float(
                line.x_pu
            )

            b = float(
                getattr(
                    line,
                    "b_pu",
                    0.0,
                )
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                f"Line '{line_id}' contains invalid "
                "electrical parameters."
            ) from exc

        if not np.all(
            np.isfinite(
                [
                    r,
                    x,
                    b,
                ]
            )
        ):
            raise ValueError(
                f"Line '{line_id}' contains non-finite "
                "electrical parameters."
            )

        # -------------------------------------------------------------
        # SERIES IMPEDANCE
        # -------------------------------------------------------------

        z = complex(
            r,
            x,
        )

        if abs(z) <= self._IMPEDANCE_TOLERANCE:
            raise ValueError(
                f"Line '{line_id}' has zero or near-zero "
                "series impedance."
            )

        y_series = 1.0 / z

        # -------------------------------------------------------------
        # NOMINAL-PI SHUNT
        # -------------------------------------------------------------

        y_shunt = (
            1j * b / 2.0
        )

        # -------------------------------------------------------------
        # TERMINAL CURRENTS
        # -------------------------------------------------------------

        I_from = (
            (Vi - Vj)
            * y_series
            +
            Vi * y_shunt
        )

        I_to = (
            (Vj - Vi)
            * y_series
            +
            Vj * y_shunt
        )

        # -------------------------------------------------------------
        # TERMINAL COMPLEX POWER
        # -------------------------------------------------------------

        S_from = (
            Vi
            * np.conj(I_from)
        )

        S_to = (
            Vj
            * np.conj(I_to)
        )

        # -------------------------------------------------------------
        # LOSSES / REACTIVE BALANCE
        # -------------------------------------------------------------

        S_total = (
            S_from
            +
            S_to
        )

        p_loss = float(
            np.real(S_total)
        )

        q_balance = float(
            np.imag(S_total)
        )

        # -------------------------------------------------------------
        # RESULT
        # -------------------------------------------------------------

        return LineFlowResult(
            line_id=line_id,

            from_bus=from_bus.id,
            to_bus=to_bus.id,

            current_from=complex(
                I_from
            ),

            current_to=complex(
                I_to
            ),

            p_from=float(
                np.real(S_from)
            ),

            q_from=float(
                np.imag(S_from)
            ),

            p_to=float(
                np.real(S_to)
            ),

            q_to=float(
                np.imag(S_to)
            ),

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
        Calculate flows for network lines.

        Parameters
        ----------
        V:
            Complex bus-voltage vector in per-unit.

        include_out_of_service:
            If False, out-of-service lines are omitted.

            If True, out-of-service lines are returned with zero
            terminal current and zero power flow and with
            ``in_service=False``.

        Returns
        -------
        dict
            Results keyed by line ID.
        """

        results: Dict[
            Any,
            LineFlowResult,
        ] = {}

        for line in self.network.lines:

            line_id = getattr(
                line,
                "id",
                None,
            )

            in_service = getattr(
                line,
                "in_service",
                True,
            )

            if not in_service:

                if not include_out_of_service:
                    continue

                if line_id is None:
                    raise ValueError(
                        "Out-of-service line is missing an ID."
                    )

                if not hasattr(
                    line,
                    "from_bus",
                ) or not hasattr(
                    line,
                    "to_bus",
                ):
                    raise ValueError(
                        f"Line '{line_id}' is missing "
                        "terminal bus information."
                    )

                results[line_id] = (
                    LineFlowResult(
                        line_id=line_id,

                        from_bus=line.from_bus.id,
                        to_bus=line.to_bus.id,

                        current_from=0.0 + 0.0j,
                        current_to=0.0 + 0.0j,

                        p_from=0.0,
                        q_from=0.0,

                        p_to=0.0,
                        q_to=0.0,

                        p_loss=0.0,
                        q_balance=0.0,

                        in_service=False,
                    )
                )

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

        results = self.calculate_all(
            V
        )

        total_p_loss = float(
            sum(
                result.p_loss
                for result in results.values()
            )
        )

        total_q_balance = float(
            sum(
                result.q_balance
                for result in results.values()
            )
        )

        return {
            "line_count": len(
                results
            ),

            "total_p_loss_pu": (
                total_p_loss
            ),

            "total_q_balance_pu": (
                total_q_balance
            ),

            "lines": {
                line_id: result.to_dict()
                for line_id, result
                in results.items()
            },
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Developer-friendly representation.
        """

        return (
            "LineFlowCalculator("
            f"lines={len(self.network.lines)}, "
            f"buses={len(self.network.buses)}"
            ")"
        )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "LineFlowResult",
    "LineFlowCalculator",
]
```
