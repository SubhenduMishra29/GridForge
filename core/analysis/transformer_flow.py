```python
"""
GridForge - Transformer Flow Analysis
=====================================

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.

File
----
core/analysis/transformer_flow.py

Purpose
-------
Deterministic engineering calculation of transformer terminal power
flows, losses, and loading.

Supported
---------
- In-service two-winding transformers
- Off-nominal tap ratio
- Phase-shifting transformers
- Complex transformer ratio
- Bidirectional P/Q flow
- Transformer losses
- Transformer loading

Architecture
------------
Network
    |
    v
TransformerFlowCalculator
    |
    +-- frozen Transformer model

This module is an analysis-level calculation component.

It does NOT:
    - Build Ybus
    - Solve power flow
    - Modify transformer model state
    - Perform optimization
    - Perform fault calculations

The transformer series impedance and complex tap ratio are obtained
directly from the frozen GridForge Transformer model.

Transformer series impedance is represented in per-unit.

The complex transformer ratio is:

    a = tap * exp(j*theta)

For the standard off-nominal transformer formulation:

    I_from = y / conj(a) * (V_from / a - V_to)

    I_to   = y * (V_to - V_from / a)

where:

    y = 1 / (r + j*x)

Complex power is:

    S_from = V_from * conj(I_from)

    S_to   = V_to * conj(I_to)

All electrical power and current quantities are returned in per-unit.

Physical transformer loading is returned in MVA and percent when
the frozen Transformer model provides rate_mva.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

import numpy as np


# =====================================================================
# RESULT
# =====================================================================

@dataclass
class TransformerFlowResult:
    """
    Result of a single transformer-flow calculation.

    Electrical quantities are in per-unit unless explicitly marked
    otherwise.
    """

    transformer_id: Any

    from_bus: Any
    to_bus: Any

    # Transformer operating point
    tap_ratio: float
    phase_shift_deg: float

    # Terminal powers
    p_from: float
    q_from: float

    p_to: float
    q_to: float

    # Losses
    p_loss: float
    q_loss: float

    # Apparent power
    s_from_pu: float
    s_to_pu: float

    # Terminal current magnitudes
    i_from_pu: float
    i_to_pu: float

    # Physical loading
    loading_mva: Optional[float] = None
    loading_percent: Optional[float] = None

    in_service: bool = True

    # -----------------------------------------------------------------
    # Convenience properties
    # -----------------------------------------------------------------

    @property
    def s_from(self) -> complex:
        """Sending-side complex power in pu."""
        return complex(self.p_from, self.q_from)

    @property
    def s_to(self) -> complex:
        """Receiving-side complex power in pu."""
        return complex(self.p_to, self.q_to)

    # -----------------------------------------------------------------
    # Serialization
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result to a JSON-friendly dictionary.
        """

        data = asdict(self)

        data["s_from"] = {
            "real": float(self.s_from.real),
            "imag": float(self.s_from.imag),
        }

        data["s_to"] = {
            "real": float(self.s_to.real),
            "imag": float(self.s_to.imag),
        }

        return data


# =====================================================================
# TRANSFORMER FLOW CALCULATOR
# =====================================================================

class TransformerFlowCalculator:
    """
    Calculate transformer terminal power flows.

    Parameters
    ----------
    network:
        GridForge Network instance.

    Notes
    -----
    The calculator expects:

        network.transformers
        network.buses
        network.bus_index

    Bus voltage magnitudes are supplied in per-unit.

    Bus voltage angles are supplied in radians.

    No Network or Transformer state is modified.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(self, network: Any):

        if network is None:
            raise ValueError(
                "Transformer flow calculation requires a valid Network."
            )

        if not hasattr(network, "transformers"):
            raise ValueError(
                "Network missing 'transformers' collection."
            )

        if not hasattr(network, "buses"):
            raise ValueError(
                "Network missing 'buses' collection."
            )

        if not hasattr(network, "bus_index"):
            raise ValueError(
                "Network missing 'bus_index' mapping."
            )

        self.network = network

    # =================================================================
    # PUBLIC API
    # =================================================================

    def calculate(
        self,
        Vm: np.ndarray,
        Va: np.ndarray,
        include_out_of_service: bool = False,
    ) -> Dict[Any, TransformerFlowResult]:
        """
        Calculate transformer flows for the complete network.

        Parameters
        ----------
        Vm:
            Bus voltage magnitudes in pu.

        Va:
            Bus voltage angles in radians.

        include_out_of_service:
            If False, out-of-service transformers are skipped.

        Returns
        -------
        dict
            Results keyed by transformer ID.
        """

        Vm = np.asarray(Vm, dtype=float).reshape(-1)
        Va = np.asarray(Va, dtype=float).reshape(-1)

        self._validate_voltage_arrays(Vm, Va)

        results: Dict[Any, TransformerFlowResult] = {}

        for transformer in self.network.transformers:

            in_service = getattr(
                transformer,
                "in_service",
                True,
            )

            if not in_service and not include_out_of_service:
                continue

            if not in_service:
                continue

            result = self._calculate_transformer(
                transformer,
                Vm,
                Va,
            )

            results[result.transformer_id] = result

        return results

    # =================================================================
    # SINGLE TRANSFORMER
    # =================================================================

    def calculate_one(
        self,
        transformer: Any,
        Vm: np.ndarray,
        Va: np.ndarray,
    ) -> TransformerFlowResult:
        """
        Calculate flow through one transformer.
        """

        Vm = np.asarray(Vm, dtype=float).reshape(-1)
        Va = np.asarray(Va, dtype=float).reshape(-1)

        self._validate_voltage_arrays(Vm, Va)

        if not getattr(transformer, "in_service", True):
            raise ValueError(
                f"Transformer "
                f"'{getattr(transformer, 'id', transformer)}' "
                "is out of service."
            )

        return self._calculate_transformer(
            transformer,
            Vm,
            Va,
        )

    # =================================================================
    # CORE CALCULATION
    # =================================================================

    def _calculate_transformer(
        self,
        transformer: Any,
        Vm: np.ndarray,
        Va: np.ndarray,
    ) -> TransformerFlowResult:
        """
        Calculate terminal currents, powers, losses and loading for
        one transformer.
        """

        transformer_id = getattr(
            transformer,
            "id",
            None,
        )

        # -------------------------------------------------------------
        # TERMINALS
        # -------------------------------------------------------------

        if not hasattr(transformer, "bus_from"):
            raise ValueError(
                f"Transformer '{transformer_id}' "
                "is missing 'bus_from'."
            )

        if not hasattr(transformer, "bus_to"):
            raise ValueError(
                f"Transformer '{transformer_id}' "
                "is missing 'bus_to'."
            )

        from_bus = transformer.bus_from
        to_bus = transformer.bus_to

        if from_bus is None or to_bus is None:
            raise ValueError(
                f"Transformer '{transformer_id}' "
                "has an invalid terminal bus."
            )

        # -------------------------------------------------------------
        # BUS INDICES
        # -------------------------------------------------------------

        try:
            i = self.network.bus_index[from_bus.id]
            j = self.network.bus_index[to_bus.id]

        except (KeyError, AttributeError) as exc:
            raise ValueError(
                f"Transformer '{transformer_id}' references a bus "
                "missing from network.bus_index."
            ) from exc

        # -------------------------------------------------------------
        # VOLTAGE VECTOR VALIDATION
        # -------------------------------------------------------------

        if i < 0 or i >= len(Vm):
            raise ValueError(
                f"Invalid from-bus index {i} for transformer "
                f"'{transformer_id}'."
            )

        if j < 0 or j >= len(Vm):
            raise ValueError(
                f"Invalid to-bus index {j} for transformer "
                f"'{transformer_id}'."
            )

        # -------------------------------------------------------------
        # COMPLEX BUS VOLTAGES
        # -------------------------------------------------------------

        V_from = Vm[i] * np.exp(1j * Va[i])
        V_to = Vm[j] * np.exp(1j * Va[j])

        # -------------------------------------------------------------
        # SERIES IMPEDANCE
        # -------------------------------------------------------------

        try:
            r = float(transformer.r)
            x = float(transformer.x)

        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Transformer '{transformer_id}' has invalid "
                "series impedance parameters."
            ) from exc

        z = complex(r, x)

        if abs(z) < 1e-12:
            raise ValueError(
                f"Transformer '{transformer_id}' "
                "has zero series impedance."
            )

        y = 1.0 / z

        # -------------------------------------------------------------
        # COMPLEX TRANSFORMER RATIO
        # -------------------------------------------------------------

        if not hasattr(transformer, "complex_tap"):
            raise ValueError(
                f"Transformer '{transformer_id}' "
                "does not expose 'complex_tap'."
            )

        try:
            a = complex(transformer.complex_tap)

        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Transformer '{transformer_id}' "
                "has an invalid complex tap ratio."
            ) from exc

        if abs(a) < 1e-12:
            raise ValueError(
                f"Transformer '{transformer_id}' "
                "has a zero complex tap ratio."
            )

        # -------------------------------------------------------------
        # TERMINAL CURRENTS
        #
        # Standard complex off-nominal transformer model:
        #
        #     I_from = y/conj(a) * (V_from/a - V_to)
        #
        #     I_to   = y * (V_to - V_from/a)
        # -------------------------------------------------------------

        I_from = (
            y
            / np.conj(a)
            * (
                V_from / a
                - V_to
            )
        )

        I_to = (
            y
            * (
                V_to
                - V_from / a
            )
        )

        # -------------------------------------------------------------
        # COMPLEX POWER
        # -------------------------------------------------------------

        S_from = V_from * np.conj(I_from)
        S_to = V_to * np.conj(I_to)

        P_from = float(S_from.real)
        Q_from = float(S_from.imag)

        P_to = float(S_to.real)
        Q_to = float(S_to.imag)

        S_from_mag = float(abs(S_from))
        S_to_mag = float(abs(S_to))

        # -------------------------------------------------------------
        # LOSSES
        # -------------------------------------------------------------

        P_loss = P_from + P_to
        Q_loss = Q_from + Q_to

        # -------------------------------------------------------------
        # TRANSFORMER LOADING
        # -------------------------------------------------------------

        rate_mva = getattr(
            transformer,
            "rate_mva",
            None,
        )

        loading_mva: Optional[float] = None
        loading_percent: Optional[float] = None

        if rate_mva is not None:

            try:
                rate_mva = float(rate_mva)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Transformer '{transformer_id}' "
                    "has an invalid rate_mva."
                ) from exc

            if rate_mva <= 0.0:
                raise ValueError(
                    f"Transformer '{transformer_id}' "
                    "has a non-positive rate_mva."
                )

            base_mva = self._get_base_mva()

            loading_mva = (
                max(
                    S_from_mag,
                    S_to_mag,
                )
                * base_mva
            )

            loading_percent = (
                loading_mva
                / rate_mva
                * 100.0
            )

        # -------------------------------------------------------------
        # MODEL METADATA
        # -------------------------------------------------------------

        tap_ratio = self._get_optional_float(
            transformer,
            "tap_ratio",
            default=abs(a),
        )

        phase_shift_deg = self._get_optional_float(
            transformer,
            "phase_shift_deg",
            default=float(
                np.angle(a, deg=True)
            ),
        )

        # -------------------------------------------------------------
        # RESULT
        # -------------------------------------------------------------

        return TransformerFlowResult(
            transformer_id=transformer_id,

            from_bus=from_bus.id,
            to_bus=to_bus.id,

            tap_ratio=tap_ratio,
            phase_shift_deg=phase_shift_deg,

            p_from=P_from,
            q_from=Q_from,

            p_to=P_to,
            q_to=Q_to,

            p_loss=P_loss,
            q_loss=Q_loss,

            s_from_pu=S_from_mag,
            s_to_pu=S_to_mag,

            i_from_pu=float(abs(I_from)),
            i_to_pu=float(abs(I_to)),

            loading_mva=loading_mva,
            loading_percent=loading_percent,

            in_service=True,
        )

    # =================================================================
    # VALIDATION
    # =================================================================

    def _validate_voltage_arrays(
        self,
        Vm: np.ndarray,
        Va: np.ndarray,
    ) -> None:
        """
        Validate bus-voltage arrays against the frozen Network.
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

    # =================================================================
    # BASE MVA
    # =================================================================

    def _get_base_mva(self) -> float:
        """
        Obtain the system MVA base from the frozen Network
        per-unit system.
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

        try:
            base_mva = float(pu.base_mva)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Network per-unit base MVA is invalid."
            ) from exc

        if not np.isfinite(base_mva) or base_mva <= 0.0:
            raise ValueError(
                "Per-unit base MVA must be finite and positive."
            )

        return base_mva

    # =================================================================
    # OPTIONAL MODEL VALUE
    # =================================================================

    @staticmethod
    def _get_optional_float(
        obj: Any,
        attribute: str,
        default: float,
    ) -> float:
        """
        Return an optional model attribute as a finite float.

        If the attribute is absent, use the supplied default.
        """

        value = getattr(obj, attribute, default)

        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Transformer attribute '{attribute}' "
                "must be numeric."
            ) from exc

        if not np.isfinite(value):
            raise ValueError(
                f"Transformer attribute '{attribute}' "
                "must be finite."
            )

        return value

    # =================================================================
    # SUMMARY
    # =================================================================

    def summary(self) -> Dict[str, int]:
        """
        Return structural information about transformer availability.

        This method does not perform electrical calculations.
        """

        total = len(self.network.transformers)

        active = sum(
            1
            for transformer in self.network.transformers
            if getattr(
                transformer,
                "in_service",
                True,
            )
        )

        return {
            "transformers": total,
            "active_transformers": active,
        }


__all__ = [
    "TransformerFlowResult",
    "TransformerFlowCalculator",
]
```
