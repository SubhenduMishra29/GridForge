```python
"""
GridForge Line Flow Analysis
============================

File:
    core/analysis/line_flow.py

Purpose:
    Calculate steady-state electrical quantities for network
    transmission/distribution lines using the same nominal
    pi-model used by GridForge YBusBuilder.

Calculates:

    - Pij
    - Qij
    - Pji
    - Qji
    - Active-power loss
    - Reactive-power net balance

Architecture:

    Network
        │
        ├── frozen Line model
        │
        ├── PerUnitSystem
        │
        └── solved bus voltages
                │
                ▼
        LineFlowCalculator

This module performs analytical line-flow calculations only.

It does NOT:

    - Solve power flow
    - Build Ybus
    - Modify the network model
    - Perform Newton-Raphson iterations
    - Perform fault calculations

Electrical line parameters are consumed in per-unit form,
consistent with the frozen GridForge Line model and YBusBuilder.
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np


class LineFlowCalculator:
    """
    Calculate steady-state power flows for network lines.

    Parameters
    ----------
    network:
        GridForge Network instance.

    Notes
    -----
    The calculator uses the same nominal pi-model convention
    as ``core.network.ybus.YBusBuilder``.

    Line parameters:

        r_pu
        x_pu
        b_pu

    Bus voltages:

        Vm -> voltage magnitude in pu
        Va -> voltage angle in radians

    Returned powers are in per-unit on the Network system base.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(self, network: Any) -> None:

        if network is None:
            raise ValueError(
                "LineFlowCalculator requires a valid Network."
            )

        self.network = network

        # -----------------------------------------------------
        # Required Network interfaces.
        # -----------------------------------------------------

        required_attributes = (
            "buses",
            "lines",
            "bus_index",
            "per_unit",
        )

        for attribute in required_attributes:

            if not hasattr(network, attribute):
                raise ValueError(
                    "Network is missing required "
                    f"attribute '{attribute}'."
                )

        self.pu = network.per_unit

    # =========================================================
    # PUBLIC API
    # =========================================================

    def compute(
        self,
        Vm,
        Va,
    ) -> List[Dict[str, Any]]:
        """
        Calculate line flows for the supplied solved bus state.

        Parameters
        ----------
        Vm:
            Array-like voltage magnitudes in pu.

        Va:
            Array-like voltage angles in radians.

        Returns
        -------
        list of dict
            One result dictionary for every in-service line.

        Raises
        ------
        ValueError
            If voltage arrays are inconsistent with the
            Network bus count.
        """

        Vm = np.asarray(Vm, dtype=float)
        Va = np.asarray(Va, dtype=float)

        self._validate_voltage_state(Vm, Va)

        # -----------------------------------------------------
        # Network owns the authoritative bus index.
        # -----------------------------------------------------

        self.network.rebuild_bus_index()

        results: List[Dict[str, Any]] = []

        for line in self.network.lines:

            # Out-of-service lines do not participate in
            # electrical flow calculations.
            if not getattr(line, "in_service", True):
                continue

            results.append(
                self._line_flow(
                    line,
                    Vm,
                    Va,
                )
            )

        return results

    # =========================================================
    # LINE CALCULATION
    # =========================================================

    def _line_flow(
        self,
        line: Any,
        Vm: np.ndarray,
        Va: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Calculate the two-terminal power flow of one line.

        Uses the nominal pi-model:

                    b/2
                     │
            i ───────┴─────── j
                 series
               admittance
                     │
                    b/2
        """

        # -----------------------------------------------------
        # Validate line interface.
        # -----------------------------------------------------

        required_attributes = (
            "from_bus",
            "to_bus",
            "r_pu",
            "x_pu",
        )

        for attribute in required_attributes:

            if not hasattr(line, attribute):
                raise ValueError(
                    f"Line is missing required "
                    f"attribute '{attribute}'."
                )

        # -----------------------------------------------------
        # Resolve bus IDs.
        #
        # Frozen Network/Line architecture may represent
        # terminals through Bus objects.
        # -----------------------------------------------------

        from_bus = line.from_bus
        to_bus = line.to_bus

        from_bus_id = (
            from_bus.id
            if hasattr(from_bus, "id")
            else from_bus
        )

        to_bus_id = (
            to_bus.id
            if hasattr(to_bus, "id")
            else to_bus
        )

        # -----------------------------------------------------
        # Obtain authoritative Network bus indices.
        # -----------------------------------------------------

        try:
            i = self.network.bus_index[from_bus_id]
        except KeyError as exc:
            raise ValueError(
                f"Line references unknown from-bus "
                f"'{from_bus_id}'."
            ) from exc

        try:
            j = self.network.bus_index[to_bus_id]
        except KeyError as exc:
            raise ValueError(
                f"Line references unknown to-bus "
                f"'{to_bus_id}'."
            ) from exc

        # -----------------------------------------------------
        # Bus voltages.
        # -----------------------------------------------------

        Vi = Vm[i] * np.exp(1j * Va[i])
        Vj = Vm[j] * np.exp(1j * Va[j])

        # -----------------------------------------------------
        # Series impedance.
        #
        # The frozen Line model stores impedance directly
        # in per-unit form.
        # -----------------------------------------------------

        r = float(line.r_pu)
        x = float(line.x_pu)

        z = complex(r, x)

        if abs(z) < 1e-12:
            raise ValueError(
                f"Zero impedance line detected: "
                f"{getattr(line, 'id', line)}"
            )

        y_series = 1.0 / z

        # -----------------------------------------------------
        # Line charging.
        #
        # b_pu represents the total line shunt susceptance.
        # Half is placed at each terminal.
        # -----------------------------------------------------

        b_pu = float(
            getattr(line, "b_pu", 0.0)
        )

        y_shunt_half = 1j * (b_pu / 2.0)

        # -----------------------------------------------------
        # Terminal currents.
        #
        # This is identical to the nominal pi-model convention
        # used by YBusBuilder.
        # -----------------------------------------------------

        Iij = (
            (Vi - Vj) * y_series
            + Vi * y_shunt_half
        )

        Iji = (
            (Vj - Vi) * y_series
            + Vj * y_shunt_half
        )

        # -----------------------------------------------------
        # Complex power.
        #
        # S = V * conjugate(I)
        # -----------------------------------------------------

        Sij = Vi * np.conj(Iij)
        Sji = Vj * np.conj(Iji)

        Pij = float(Sij.real)
        Qij = float(Sij.imag)

        Pji = float(Sji.real)
        Qji = float(Sji.imag)

        # -----------------------------------------------------
        # Net line quantities.
        #
        # Active loss:
        #
        #     Ploss = Pij + Pji
        #
        # Reactive balance includes the shunt charging effect,
        # therefore the quantity is called Q_balance rather
        # than assuming it is always a positive "loss".
        # -----------------------------------------------------

        P_loss = Pij + Pji
        Q_balance = Qij + Qji

        return {
            "line": getattr(
                line,
                "id",
                getattr(line, "name", None),
            ),

            "from_bus": from_bus_id,
            "to_bus": to_bus_id,

            "P_from_to": Pij,
            "Q_from_to": Qij,

            "P_to_from": Pji,
            "Q_to_from": Qji,

            "P_loss": P_loss,
            "Q_balance": Q_balance,

            "in_service": True,
        }

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_voltage_state(
        self,
        Vm: np.ndarray,
        Va: np.ndarray,
    ) -> None:
        """
        Validate the supplied solved voltage state.

        Numerical convergence validation belongs to the
        power-flow solver. This method only checks structural
        consistency.
        """

        n = len(self.network.buses)

        if Vm.ndim != 1:
            raise ValueError(
                "Voltage magnitude array Vm must be one-dimensional."
            )

        if Va.ndim != 1:
            raise ValueError(
                "Voltage angle array Va must be one-dimensional."
            )

        if len(Vm) != n:
            raise ValueError(
                f"Voltage magnitude array length {len(Vm)} "
                f"does not match network bus count {n}."
            )

        if len(Va) != n:
            raise ValueError(
                f"Voltage angle array length {len(Va)} "
                f"does not match network bus count {n}."
            )

        if not np.all(np.isfinite(Vm)):
            raise ValueError(
                "Voltage magnitude array contains "
                "non-finite values."
            )

        if not np.all(np.isfinite(Va)):
            raise ValueError(
                "Voltage angle array contains "
                "non-finite values."
            )

        if np.any(Vm <= 0.0):
            raise ValueError(
                "Voltage magnitudes must be positive."
            )

    # =========================================================
    # SUMMARY
    # =========================================================

    def summary(self) -> Dict[str, Any]:
        """
        Return a concise calculator summary.
        """

        return {
            "lines": len(
                getattr(
                    self.network,
                    "lines",
                    [],
                )
            ),
            "system_base_mva": getattr(
                self.network,
                "base_mva",
                None,
            ),
            "parameter_basis": "per_unit",
            "model": "nominal_pi",
        }


__all__ = [
    "LineFlowCalculator",
]
```
