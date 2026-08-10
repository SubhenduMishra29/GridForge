```python
# GridForge
# Copyright © 2026 Subhendu Mishra
# All Rights Reserved.
# Proprietary and confidential.

"""
GridForge Transformer Flow Analysis
===================================

File:
    core/analysis/transformer_flow.py

Purpose:
    Calculate steady-state electrical quantities for network
    transformers using the same transformer model used by
    GridForge YBusBuilder.

Calculates:

    - Pij
    - Qij
    - Pji
    - Qji
    - Active-power loss
    - Reactive-power balance

Supported transformer features:

    - Per-unit impedance
    - Off-nominal tap ratio
    - Phase-shifting transformer
    - Complex tap ratio

Architecture:

    Network
        │
        ├── frozen Transformer model
        │
        ├── solved bus voltages
        │
        └── transformer parameters
                │
                ▼
        TransformerFlowCalculator

This module performs analytical transformer-flow calculations.

It does NOT:

    - Solve power flow
    - Build Ybus
    - Modify transformer parameters
    - Perform Newton-Raphson iterations
    - Perform fault calculations

IMPORTANT
---------
The transformer equations here must remain consistent with
core/network/ybus.py.

For:

    a = tap * exp(jθ)

the Y-bus transformer stamp is:

    Yii = y / |a|²
    Yij = -y / a*
    Yji = -y / a
    Yjj = y

Therefore:

    Iij = (Vi / |a|² - Vj / a*) * y
    Iji = (Vj - Vi / a) * y
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np


class TransformerFlowCalculator:
    """
    Calculate steady-state power flows for network transformers.

    Parameters
    ----------
    network:
        GridForge Network instance.

    Notes
    -----
    Transformer impedance and system quantities are expressed
    in per-unit on the Network system base.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(self, network: Any) -> None:

        if network is None:
            raise ValueError(
                "TransformerFlowCalculator requires a valid Network."
            )

        self.network = network

        required_attributes = (
            "buses",
            "transformers",
            "bus_index",
            "per_unit",
        )

        for attribute in required_attributes:

            if not hasattr(network, attribute):
                raise ValueError(
                    "Network is missing required "
                    f"attribute '{attribute}'."
                )

    # =========================================================
    # PUBLIC API
    # =========================================================

    def compute(
        self,
        Vm,
        Va,
    ) -> List[Dict[str, Any]]:
        """
        Calculate transformer flows for the supplied
        solved bus-voltage state.

        Parameters
        ----------
        Vm:
            Voltage magnitudes in pu.

        Va:
            Voltage angles in radians.

        Returns
        -------
        list of dict
            One result dictionary for every in-service
            transformer.
        """

        Vm = np.asarray(Vm, dtype=float)
        Va = np.asarray(Va, dtype=float)

        self._validate_voltage_state(Vm, Va)

        # Network owns the authoritative bus indexing.
        self.network.rebuild_bus_index()

        results: List[Dict[str, Any]] = []

        for trafo in self.network.transformers:

            if not getattr(
                trafo,
                "in_service",
                True,
            ):
                continue

            results.append(
                self._flow(
                    trafo,
                    Vm,
                    Va,
                )
            )

        return results

    # =========================================================
    # TRANSFORMER FLOW
    # =========================================================

    def _flow(
        self,
        trafo: Any,
        Vm: np.ndarray,
        Va: np.ndarray,
    ) -> Dict[str, Any]:
        """
        Calculate the two-terminal transformer power flow.

        Transformer model:

            a = tap * exp(jθ)

        Series admittance:

            y = 1 / (r + jx)

        Terminal currents:

            Iij = (Vi / |a|² - Vj / a*) y

            Iji = (Vj - Vi / a) y

        Complex powers:

            Sij = Vi * conj(Iij)

            Sji = Vj * conj(Iji)
        """

        # -----------------------------------------------------
        # Validate transformer interface.
        # -----------------------------------------------------

        required_attributes = (
            "from_bus",
            "to_bus",
            "r_pu",
            "x_pu",
        )

        for attribute in required_attributes:

            if not hasattr(trafo, attribute):
                raise ValueError(
                    "Transformer is missing required "
                    f"attribute '{attribute}'."
                )

        # -----------------------------------------------------
        # Resolve terminal bus IDs.
        # -----------------------------------------------------

        from_bus = trafo.from_bus
        to_bus = trafo.to_bus

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
        # Resolve bus indices.
        # -----------------------------------------------------

        try:
            i = self.network.bus_index[from_bus_id]
        except KeyError as exc:
            raise ValueError(
                f"Transformer references unknown "
                f"from-bus '{from_bus_id}'."
            ) from exc

        try:
            j = self.network.bus_index[to_bus_id]
        except KeyError as exc:
            raise ValueError(
                f"Transformer references unknown "
                f"to-bus '{to_bus_id}'."
            ) from exc

        # -----------------------------------------------------
        # Complex bus voltages.
        # -----------------------------------------------------

        Vi = Vm[i] * np.exp(1j * Va[i])
        Vj = Vm[j] * np.exp(1j * Va[j])

        # -----------------------------------------------------
        # Transformer series impedance.
        # -----------------------------------------------------

        r = float(trafo.r_pu)
        x = float(trafo.x_pu)

        z = complex(r, x)

        if abs(z) < 1e-12:
            raise ValueError(
                "Zero impedance transformer detected: "
                f"{getattr(trafo, 'id', trafo)}"
            )

        y = 1.0 / z

        # -----------------------------------------------------
        # Complex tap ratio.
        #
        # a = tap * exp(jθ)
        # -----------------------------------------------------

        tap = float(
            getattr(
                trafo,
                "tap_ratio",
                1.0,
            )
        )

        if tap <= 0.0:
            raise ValueError(
                "Transformer tap ratio must be positive."
            )

        phase_shift_deg = float(
            getattr(
                trafo,
                "phase_shift_deg",
                0.0,
            )
        )

        phase_shift_rad = np.deg2rad(
            phase_shift_deg
        )

        a = tap * np.exp(
            1j * phase_shift_rad
        )

        if abs(a) < 1e-12:
            raise ValueError(
                "Transformer complex tap ratio cannot be zero."
            )

        # -----------------------------------------------------
        # Terminal currents.
        #
        # IMPORTANT:
        # These equations exactly correspond to the transformer
        # Y-bus stamp in core/network/ybus.py.
        # -----------------------------------------------------

        Iij = (
            Vi / (abs(a) ** 2)
            - Vj / np.conj(a)
        ) * y

        Iji = (
            Vj
            - Vi / a
        ) * y

        # -----------------------------------------------------
        # Optional transformer shunt.
        #
        # Must match YBusBuilder:
        #
        #     +j*b_shunt/2
        #
        # on each terminal.
        # -----------------------------------------------------

        b_shunt = float(
            getattr(
                trafo,
                "b_shunt_pu",
                0.0,
            )
        )

        y_shunt_half = 1j * (
            b_shunt / 2.0
        )

        Iij += Vi * y_shunt_half
        Iji += Vj * y_shunt_half

        # -----------------------------------------------------
        # Complex power.
        # -----------------------------------------------------

        Sij = Vi * np.conj(Iij)
        Sji = Vj * np.conj(Iji)

        Pij = float(Sij.real)
        Qij = float(Sij.imag)

        Pji = float(Sji.real)
        Qji = float(Sji.imag)

        # -----------------------------------------------------
        # Power balance.
        #
        # Active power loss should normally be non-negative
        # for a passive transformer with positive resistance.
        #
        # Reactive balance includes transformer shunt effects,
        # so it is not necessarily a positive "loss".
        # -----------------------------------------------------

        P_loss = Pij + Pji
        Q_balance = Qij + Qji

        return {
            "transformer": getattr(
                trafo,
                "id",
                getattr(
                    trafo,
                    "name",
                    None,
                ),
            ),

            "from_bus": from_bus_id,
            "to_bus": to_bus_id,

            "tap_ratio": tap,
            "phase_shift_deg": phase_shift_deg,

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

        This is structural validation only.

        Numerical convergence validation belongs to the
        power-flow solver.
        """

        n = len(
            self.network.buses
        )

        if Vm.ndim != 1:
            raise ValueError(
                "Voltage magnitude array Vm must "
                "be one-dimensional."
            )

        if Va.ndim != 1:
            raise ValueError(
                "Voltage angle array Va must "
                "be one-dimensional."
            )

        if len(Vm) != n:
            raise ValueError(
                f"Voltage magnitude array length "
                f"{len(Vm)} does not match "
                f"network bus count {n}."
            )

        if len(Va) != n:
            raise ValueError(
                f"Voltage angle array length "
                f"{len(Va)} does not match "
                f"network bus count {n}."
            )

        if not np.all(
            np.isfinite(Vm)
        ):
            raise ValueError(
                "Voltage magnitude array contains "
                "non-finite values."
            )

        if not np.all(
            np.isfinite(Va)
        ):
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
        Return a concise transformer-flow summary.
        """

        return {
            "transformers": len(
                getattr(
                    self.network,
                    "transformers",
                    [],
                )
            ),
            "system_base_mva": getattr(
                self.network,
                "base_mva",
                None,
            ),
            "parameter_basis": "per_unit",
            "model": "off_nominal_complex_tap",
        }


__all__ = [
    "TransformerFlowCalculator",
]
```
