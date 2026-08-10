```python
"""
GridForge Transformer Flow Analysis

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.

File:
    core/analysis/transformer_flow.py

Purpose
-------
Calculate electrical power flow through two-winding transformers.

Supported:
    - Active/in-service transformers
    - Off-nominal tap ratio
    - Phase-shifting transformers
    - Complex transformer ratio
    - Bidirectional P/Q flow
    - Transformer losses
    - Transformer loading

Architecture
------------
Network
    │
    ▼
TransformerFlowCalculator
    │
    └── uses frozen Transformer model

This module is an analysis-level calculation component.

It does NOT:
    - Build Ybus
    - Solve power flow
    - Modify transformer model state
    - Perform optimization
    - Perform fault calculations

Transformer electrical parameters are taken directly from the
frozen GridForge Transformer model.

The transformer series impedance is already represented in
per-unit.

The complex transformer ratio is:

    a = tap * exp(jθ)

For the standard off-nominal transformer model:

    I_from = y / conj(a) * (V_from / a - V_to)

    I_to   = y * (V_to - V_from / a)

where:

    y = 1 / (r + jx)

Power is calculated as:

    S_from = V_from * conj(I_from)

    S_to   = V_to * conj(I_to)

All power results are returned in per-unit.
"""

from __future__ import annotations

import numpy as np


class TransformerFlowCalculator:
    """
    Calculate transformer terminal power flows.

    Parameters
    ----------
    network:
        GridForge Network instance.

    Notes
    -----
    The calculator expects the network to expose:

        network.transformers
        network.bus_index

    Voltage magnitudes are supplied in per-unit.

    Voltage angles are supplied in radians.
    """

    def __init__(self, network):
        self.network = network

        if network is None:
            raise ValueError(
                "Transformer flow calculation requires a valid Network."
            )

        if not hasattr(network, "transformers"):
            raise ValueError(
                "Network missing 'transformers' collection."
            )

        if not hasattr(network, "bus_index"):
            raise ValueError(
                "Network missing 'bus_index' mapping."
            )

        self.bus_index = network.bus_index

    # =========================================================
    # PUBLIC API
    # =========================================================

    def compute(self, Vm, Va):
        """
        Calculate transformer flows for the complete network.

        Parameters
        ----------
        Vm:
            Bus voltage magnitudes in pu.

        Va:
            Bus voltage angles in radians.

        Returns
        -------
        list[dict]
            One result dictionary per transformer.

        Notes
        -----
        Out-of-service transformers are skipped.
        """

        Vm = np.asarray(Vm, dtype=float)
        Va = np.asarray(Va, dtype=float)

        self._validate_voltage_arrays(Vm, Va)

        results = []

        for transformer in self.network.transformers:

            if not getattr(transformer, "in_service", True):
                continue

            results.append(
                self._transformer_flow(
                    transformer,
                    Vm,
                    Va,
                )
            )

        return results

    # =========================================================
    # CORE CALCULATION
    # =========================================================

    def _transformer_flow(self, transformer, Vm, Va):
        """
        Calculate terminal currents and powers for one transformer.
        """

        # -----------------------------------------------------
        # Validate terminal objects
        # -----------------------------------------------------

        if not hasattr(transformer, "bus_from"):
            raise ValueError(
                f"Transformer '{getattr(transformer, 'id', transformer)}' "
                "is missing 'bus_from'."
            )

        if not hasattr(transformer, "bus_to"):
            raise ValueError(
                f"Transformer '{getattr(transformer, 'id', transformer)}' "
                "is missing 'bus_to'."
            )

        from_bus = transformer.bus_from
        to_bus = transformer.bus_to

        # -----------------------------------------------------
        # Bus indices
        # -----------------------------------------------------

        try:
            i = self.bus_index[from_bus.id]
            j = self.bus_index[to_bus.id]

        except KeyError as exc:
            raise ValueError(
                f"Transformer '{getattr(transformer, 'id', transformer)}' "
                f"references a bus missing from network.bus_index: {exc}"
            ) from exc

        # -----------------------------------------------------
        # Bus voltages
        # -----------------------------------------------------

        V_from = (
            Vm[i]
            *
            np.exp(1j * Va[i])
        )

        V_to = (
            Vm[j]
            *
            np.exp(1j * Va[j])
        )

        # -----------------------------------------------------
        # Transformer impedance
        #
        # Frozen Transformer model:
        #
        #     r
        #     x
        #
        # Both are already in per-unit.
        # -----------------------------------------------------

        r = float(transformer.r)
        x = float(transformer.x)

        z = complex(r, x)

        if abs(z) < 1e-12:
            raise ValueError(
                f"Zero impedance transformer detected: "
                f"{getattr(transformer, 'id', transformer)}"
            )

        y = 1.0 / z

        # -----------------------------------------------------
        # Complex transformer ratio
        #
        # Frozen Transformer exposes:
        #
        #     complex_tap
        #
        #     a = tap * exp(jθ)
        # -----------------------------------------------------

        if not hasattr(transformer, "complex_tap"):
            raise ValueError(
                f"Transformer '{getattr(transformer, 'id', transformer)}' "
                "does not expose 'complex_tap'."
            )

        a = complex(transformer.complex_tap)

        if abs(a) < 1e-12:
            raise ValueError(
                f"Transformer '{getattr(transformer, 'id', transformer)}' "
                "has an invalid zero complex tap."
            )

        # -----------------------------------------------------
        # Terminal currents
        #
        # Standard off-nominal transformer formulation:
        #
        # I_from =
        #     y / conj(a) * (V_from / a - V_to)
        #
        # I_to =
        #     y * (V_to - V_from / a)
        #
        # This preserves the correct complex tap behaviour.
        # -----------------------------------------------------

        I_from = (
            y
            / np.conj(a)
            *
            (
                V_from / a
                -
                V_to
            )
        )

        I_to = (
            y
            *
            (
                V_to
                -
                V_from / a
            )
        )

        # -----------------------------------------------------
        # Complex power
        # -----------------------------------------------------

        S_from = V_from * np.conj(I_from)
        S_to = V_to * np.conj(I_to)

        P_from = float(S_from.real)
        Q_from = float(S_from.imag)

        P_to = float(S_to.real)
        Q_to = float(S_to.imag)

        # -----------------------------------------------------
        # Losses
        # -----------------------------------------------------

        P_loss = P_from + P_to
        Q_loss = Q_from + Q_to

        S_from_mag = abs(S_from)
        S_to_mag = abs(S_to)

        # -----------------------------------------------------
        # Transformer loading
        #
        # rate_mva belongs to the frozen Transformer model.
        #
        # Loading percentage is based on the maximum terminal
        # apparent power.
        # -----------------------------------------------------

        rate_mva = getattr(
            transformer,
            "rate_mva",
            None,
        )

        loading_mva = None
        loading_percent = None

        if rate_mva is not None:

            rate_mva = float(rate_mva)

            if rate_mva <= 0.0:
                raise ValueError(
                    f"Transformer '{getattr(transformer, 'id', transformer)}' "
                    "has an invalid rate_mva."
                )

            base_mva = self._get_base_mva()

            loading_mva = (
                max(
                    S_from_mag,
                    S_to_mag,
                )
                *
                base_mva
            )

            loading_percent = (
                loading_mva
                /
                rate_mva
                *
                100.0
            )

        # -----------------------------------------------------
        # Result
        # -----------------------------------------------------

        return {
            "transformer": getattr(
                transformer,
                "id",
                None,
            ),

            "from_bus": from_bus.id,

            "to_bus": to_bus.id,

            "tap_ratio": float(
                transformer.tap_ratio
            ),

            "phase_shift_deg": float(
                transformer.phase_shift_deg
            ),

            # Terminal powers in pu
            "P_from_to": P_from,
            "Q_from_to": Q_from,

            "P_to_from": P_to,
            "Q_to_from": Q_to,

            # Losses in pu
            "P_loss": P_loss,
            "Q_loss": Q_loss,

            # Apparent power in pu
            "S_from_pu": S_from_mag,
            "S_to_pu": S_to_mag,

            # Physical loading
            "loading_mva": loading_mva,
            "loading_percent": loading_percent,

            # Terminal currents in pu
            "I_from_pu": abs(I_from),
            "I_to_pu": abs(I_to),
        }

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_voltage_arrays(self, Vm, Va):
        """
        Validate supplied bus-voltage arrays.
        """

        expected = len(self.network.buses)

        if len(Vm) != expected:
            raise ValueError(
                "Voltage magnitude array length does not match "
                "network bus count."
            )

        if len(Va) != expected:
            raise ValueError(
                "Voltage angle array length does not match "
                "network bus count."
            )

        if not np.all(np.isfinite(Vm)):
            raise ValueError(
                "Voltage magnitude array contains non-finite values."
            )

        if not np.all(np.isfinite(Va)):
            raise ValueError(
                "Voltage angle array contains non-finite values."
            )

        if np.any(Vm < 0.0):
            raise ValueError(
                "Voltage magnitude cannot be negative."
            )

    # =========================================================
    # BASE MVA
    # =========================================================

    def _get_base_mva(self):
        """
        Obtain the system MVA base.

        The frozen Network should expose its PerUnitSystem through:

            network.per_unit.base_mva
        """

        if not hasattr(self.network, "per_unit"):
            raise ValueError(
                "Network missing 'per_unit' system required "
                "for transformer loading calculation."
            )

        pu = self.network.per_unit

        if not hasattr(pu, "base_mva"):
            raise ValueError(
                "Network per-unit system missing 'base_mva'."
            )

        base_mva = float(pu.base_mva)

        if base_mva <= 0.0:
            raise ValueError(
                "Per-unit base MVA must be positive."
            )

        return base_mva

    # =========================================================
    # SUMMARY
    # =========================================================

    def summary(self):
        """
        Return a structural summary of transformer flow analysis.
        """

        return {
            "transformers": len(
                self.network.transformers
            ),
            "active_transformers": sum(
                1
                for transformer
                in self.network.transformers
                if getattr(
                    transformer,
                    "in_service",
                    True,
                )
            ),
        }
```
