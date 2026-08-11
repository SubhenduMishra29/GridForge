```python
"""
GridForge - Short Circuit Analysis
==================================

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.

File
----
core/analysis/short_circuit.py

Purpose
-------
Public analysis-level facade for short-circuit and fault studies.

Numerical engine
----------------
core.solver.short_circuit

Supported fault types
---------------------
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
- delegating the study to the numerical solver
- retaining the latest study result

This module does NOT:

- calculate fault currents
- construct sequence networks
- calculate Zbus
- calculate Thevenin equivalents
- perform symmetrical-component mathematics
- perform numerical fault calculations

All numerical responsibilities remain in:

    core/solver/short_circuit/

Canonical GridForge terminology
--------------------------------
Short Circuit Analysis
"""

from __future__ import annotations

from typing import Any, Optional

from core.solver.short_circuit import (
    FaultType,
    ShortCircuitSolver,
)


class ShortCircuitAnalysis:
    """
    Public facade for short-circuit and fault studies.

    Parameters
    ----------
    network:
        GridForge Network containing the electrical system.

    sequence_network:
        Optional sequence-network representation accepted by the
        numerical short-circuit solver.

    Notes
    -----
    This class contains no short-circuit numerical mathematics.

    All fault calculations are delegated to:

        core.solver.short_circuit.ShortCircuitSolver
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        network: Any,
        sequence_network: Optional[Any] = None,
    ) -> None:

        self.network = network
        self.sequence_network = sequence_network
        self.result: Any = None

        self._validate_network()

    # =================================================================
    # MAIN API
    # =================================================================

    def run(
        self,
        fault_type: FaultType,
        fault_bus: Any,
        Zf: complex = 0.0,
    ) -> Any:
        """
        Execute a short-circuit study.

        Parameters
        ----------
        fault_type:
            FaultType identifying the requested fault.

        fault_bus:
            Bus ID or bus reference accepted by the numerical solver.

        Zf:
            Fault impedance.

            Real or complex impedance values are accepted.

        Returns
        -------
        Any
            Result returned by ShortCircuitSolver.
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

    # =================================================================
    # THREE-PHASE FAULT
    # =================================================================

    def run_three_phase_fault(
        self,
        fault_bus: Any,
        Zf: complex = 0.0,
    ) -> Any:
        """
        Run a balanced three-phase fault study.
        """

        return self.run(
            FaultType.THREE_PHASE,
            fault_bus,
            Zf,
        )

    # =================================================================
    # LINE-TO-GROUND FAULT
    # =================================================================

    def run_lg_fault(
        self,
        fault_bus: Any,
        Zf: complex = 0.0,
    ) -> Any:
        """
        Run a single-line-to-ground fault study.
        """

        return self.run(
            FaultType.LG,
            fault_bus,
            Zf,
        )

    # =================================================================
    # LINE-TO-LINE FAULT
    # =================================================================

    def run_ll_fault(
        self,
        fault_bus: Any,
        Zf: complex = 0.0,
    ) -> Any:
        """
        Run a line-to-line fault study.
        """

        return self.run(
            FaultType.LL,
            fault_bus,
            Zf,
        )

    # =================================================================
    # DOUBLE-LINE-TO-GROUND FAULT
    # =================================================================

    def run_llg_fault(
        self,
        fault_bus: Any,
        Zf: complex = 0.0,
    ) -> Any:
        """
        Run a double-line-to-ground fault study.
        """

        return self.run(
            FaultType.LLG,
            fault_bus,
            Zf,
        )

    # =================================================================
    # RESULT ACCESS
    # =================================================================

    def summary(self) -> Any:
        """
        Return the latest short-circuit result.

        If no study has been executed, return a NOT_RUN status.
        """

        if self.result is None:
            return {
                "status": "NOT_RUN",
            }

        return self.result

    # =================================================================
    # NETWORK VALIDATION
    # =================================================================

    def _validate_network(self) -> None:
        """
        Validate the minimum Network interface required by the
        analysis facade.

        Electrical and numerical validation remain the responsibility
        of the solver layer.
        """

        if self.network is None:
            raise ValueError(
                "Short Circuit Analysis requires a valid Network."
            )

        if not hasattr(self.network, "buses"):
            raise ValueError(
                "Network is missing required 'buses' collection."
            )

        if len(self.network.buses) == 0:
            raise ValueError(
                "Short Circuit Analysis requires at least one bus."
            )

    # =================================================================
    # FAULT REQUEST VALIDATION
    # =================================================================

    def _validate_fault_request(
        self,
        fault_type: FaultType,
        fault_bus: Any,
        Zf: complex,
    ) -> None:
        """
        Validate the basic fault-study request.

        This method deliberately avoids solver-specific electrical
        validation.
        """

        if not isinstance(fault_type, FaultType):
            raise ValueError(
                "fault_type must be an instance of FaultType."
            )

        if fault_bus is None:
            raise ValueError(
                "fault_bus cannot be None."
            )

        # -------------------------------------------------------------
        # Fault impedance
        # -------------------------------------------------------------

        try:
            impedance = complex(Zf)

        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Zf must be a numeric fault impedance."
            ) from exc

        if not (
            np_isfinite(impedance.real)
            and np_isfinite(impedance.imag)
        ):
            raise ValueError(
                "Zf must contain finite real and imaginary components."
            )

    # =================================================================
    # FAULT BUS VALIDATION
    # =================================================================

    def _validate_fault_bus(self, fault_bus: Any) -> None:
        """
        Validate a fault-bus identifier when the Network exposes
        a bus_index mapping.

        Solver-specific bus resolution remains in the solver layer.
        """

        if not hasattr(self.network, "bus_index"):
            return

        bus_index = self.network.bus_index

        if fault_bus in bus_index:
            return

        for bus in self.network.buses:

            if fault_bus is bus:
                return

            if getattr(bus, "id", None) == fault_bus:
                return

        raise ValueError(
            f"Fault bus '{fault_bus}' was not found in the Network."
        )


# =====================================================================
# NUMERIC HELPER
# =====================================================================

def np_isfinite(value: float) -> bool:
    """
    Small local finite-value helper.

    Avoids introducing NumPy as a dependency solely for scalar
    validation in this public facade.
    """

    return value == value and abs(value) != float("inf")


# =====================================================================
# BACKWARD COMPATIBILITY
# =====================================================================

# Original public class name:
#
#     ShortCircuitAnalyzer
#
# The canonical GridForge API is now:
#
#     ShortCircuitAnalysis
#
# Existing callers can continue using the original name.

ShortCircuitAnalyzer = ShortCircuitAnalysis


__all__ = [
    "ShortCircuitAnalysis",
    "ShortCircuitAnalyzer",
    "FaultType",
]
```
