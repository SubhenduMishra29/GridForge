```python
"""
GridForge Short Circuit Analysis
================================

File:
    core/analysis/short_circuit.py

Purpose:
    Public analysis-level facade for short-circuit / fault studies.

Numerical engine:
    core.solver.short_circuit

Supported fault types:
    - Three-phase fault
    - Line-to-ground (LG)
    - Line-to-line (LL)
    - Double-line-to-ground (LLG)

Architecture
------------

    Network
        |
        v
    ShortCircuitAnalysis
        |
        v
    ShortCircuitSolver
        |
        v
    core/solver/short_circuit/

Responsibilities
----------------
This module is responsible for:

    - providing the public short-circuit study API
    - validating basic study inputs
    - selecting the requested fault type
    - passing the study to the numerical solver
    - retaining the latest study result

This module does NOT:

    - calculate fault currents
    - construct sequence networks
    - calculate Zbus
    - calculate Thevenin equivalents
    - perform symmetrical-component mathematics
    - perform numerical fault calculations

Numerical responsibilities remain exclusively in:

    core/solver/short_circuit/

Canonical GridForge terminology:
    "Short Circuit Analysis"
"""


from __future__ import annotations

from typing import Any, Optional


from core.solver.short_circuit import (
    ShortCircuitSolver,
    FaultType,
)


class ShortCircuitAnalysis:
    """
    Public facade for short-circuit / fault studies.

    Parameters
    ----------
    network:
        GridForge Network containing the electrical system.

    sequence_network:
        Optional sequence-network representation used by the
        numerical short-circuit solver.

    Notes
    -----
    This class contains no short-circuit numerical mathematics.

    It delegates all fault calculations to
    ``core.solver.short_circuit``.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(
        self,
        network: Any,
        sequence_network: Optional[Any] = None,
    ) -> None:

        self.network = network

        self.sequence_network = sequence_network

        self.result: Any = None

        self._validate_network()

    # =============================================================
    # PUBLIC FAULT STUDY API
    # =============================================================

    def run(
        self,
        fault_type: FaultType,
        fault_bus: Any,
        Zf: float = 0.0,
    ) -> Any:
        """
        Execute a short-circuit study.

        Parameters
        ----------
        fault_type:
            FaultType identifying the requested fault.

        fault_bus:
            ID or bus reference accepted by the numerical solver.

        Zf:
            Fault impedance.

        Returns
        -------
        Any
            Result returned by the numerical short-circuit solver.

        Notes
        -----
        No numerical fault calculation is performed here.
        """

        self._validate_fault_request(
            fault_type=fault_type,
            fault_bus=fault_bus,
            Zf=Zf,
        )

        solver = ShortCircuitSolver(
            self.network,
            self.sequence_network,
        )

        self.result = solver.solve(
            fault_type,
            fault_bus,
            Zf,
        )

        return self.result

    # =============================================================
    # THREE-PHASE FAULT
    # =============================================================

    def run_three_phase_fault(
        self,
        fault_bus: Any,
        Zf: float = 0.0,
    ) -> Any:
        """
        Run a balanced three-phase fault study.
        """

        return self.run(
            FaultType.THREE_PHASE,
            fault_bus,
            Zf,
        )

    # =============================================================
    # LINE-TO-GROUND FAULT
    # =============================================================

    def run_lg_fault(
        self,
        fault_bus: Any,
        Zf: float = 0.0,
    ) -> Any:
        """
        Run a single-line-to-ground fault study.
        """

        return self.run(
            FaultType.LG,
            fault_bus,
            Zf,
        )

    # =============================================================
    # LINE-TO-LINE FAULT
    # =============================================================

    def run_ll_fault(
        self,
        fault_bus: Any,
        Zf: float = 0.0,
    ) -> Any:
        """
        Run a line-to-line fault study.
        """

        return self.run(
            FaultType.LL,
            fault_bus,
            Zf,
        )

    # =============================================================
    # DOUBLE-LINE-TO-GROUND FAULT
    # =============================================================

    def run_llg_fault(
        self,
        fault_bus: Any,
        Zf: float = 0.0,
    ) -> Any:
        """
        Run a double-line-to-ground fault study.
        """

        return self.run(
            FaultType.LLG,
            fault_bus,
            Zf,
        )

    # =============================================================
    # SUMMARY
    # =============================================================

    def summary(self) -> Any:
        """
        Return the latest short-circuit result.

        Returns
        -------
        Any
            The numerical solver result.

        If no study has been executed, a simple NOT_RUN status
        dictionary is returned.
        """

        if self.result is None:
            return {
                "status": "NOT_RUN"
            }

        return self.result

    # =============================================================
    # VALIDATION
    # =============================================================

    def _validate_network(self) -> None:
        """
        Validate the minimum Network interface required for a
        short-circuit study.

        This performs structural validation only.

        Electrical and numerical validation remain the
        responsibility of the solver layer.
        """

        if self.network is None:
            raise ValueError(
                "Short Circuit Analysis requires "
                "a valid Network."
            )

        if not hasattr(self.network, "buses"):
            raise ValueError(
                "Network is missing required 'buses' collection."
            )

        if not self.network.buses:
            raise ValueError(
                "Short Circuit Analysis requires "
                "at least one bus."
            )

    # =============================================================
    # FAULT REQUEST VALIDATION
    # =============================================================

    @staticmethod
    def _validate_fault_request(
        fault_type: FaultType,
        fault_bus: Any,
        Zf: float,
    ) -> None:
        """
        Validate the basic fault-study request.

        This deliberately avoids validating solver-specific
        electrical assumptions.
        """

        if not isinstance(
            fault_type,
            FaultType,
        ):
            raise ValueError(
                "fault_type must be an instance of FaultType."
            )

        if fault_bus is None:
            raise ValueError(
                "fault_bus cannot be None."
            )

        try:
            fault_impedance = float(Zf)

        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Zf must be a numeric fault impedance."
            ) from exc

        if fault_impedance < 0.0:
            raise ValueError(
                "Zf cannot be negative."
            )


# =====================================================================
# BACKWARD COMPATIBILITY
# =====================================================================
#
# The original public class name was:
#
#     ShortCircuitAnalyzer
#
# Keep it as an alias so existing GridForge callers continue to work.
#
# The canonical GridForge analysis API is now:
#
#     ShortCircuitAnalysis
# =====================================================================

ShortCircuitAnalyzer = ShortCircuitAnalysis


__all__ = [
    "ShortCircuitAnalysis",
    "ShortCircuitAnalyzer",
    "FaultType",
]
```
