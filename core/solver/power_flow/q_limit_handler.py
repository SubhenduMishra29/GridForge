"""
GridForge Reactive Power Limit Handler
======================================

File:
    core/solver/power_flow/q_limit_handler.py

GridForge Power Flow Engine v1.0
--------------------------------

Reactive-power limit handling for PV buses during AC
Newton-Raphson power-flow solution.

Responsibilities
----------------
- Detect reactive-power limit violations on PV buses.
- Convert violating PV buses to PQ buses.
- Clamp Q_spec to Q_min or Q_max.
- Preserve deterministic PV -> PQ transitions.
- Provide conversion diagnostics.

This module does NOT:
- Perform Newton-Raphson iteration.
- Build Ybus.
- Assemble the Jacobian.
- Solve linear systems.
- Modify network topology.
- Perform contingency analysis.
- Perform short-circuit analysis.
- Perform protection calculations.
- Perform dynamic simulation.

Reactive power is calculated through the shared reference
numerical component:

    core.solver.common.mismatch.PowerMismatch

Bus classification remains owned by the canonical GridForge
Bus model.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from core.solver.common.mismatch import PowerMismatch


class QLimitHandler:
    """
    Handle generator reactive-power limits during AC
    Newton-Raphson power-flow calculations.

    Parameters
    ----------
    network:
        GridForge Network instance containing the ordered
        collection of Bus objects.

    tolerance:
        Non-negative tolerance used when comparing calculated
        reactive power against Q_min and Q_max.

    Notes
    -----
    Only buses currently classified as PV are candidates for
    conversion.

    A violating PV bus undergoes:

        PV -> PQ

    and its specified reactive power is clamped to the violated
    limit.

    Example
    -------
    If:

        Q_calculated > Q_max

    then:

        bus.Q_spec = bus.Q_max
        bus -> PQ

    Likewise, if:

        Q_calculated < Q_min

    then:

        bus.Q_spec = bus.Q_min
        bus -> PQ

    The Newton-Raphson solver is responsible for rebuilding the
    mismatch/Jacobian structure after this state transition.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        network: Any,
        tolerance: float = 1.0e-8,
    ) -> None:
        """
        Initialize the reactive-power limit handler.
        """

        if network is None:
            raise ValueError(
                "Network cannot be None."
            )

        if not hasattr(
            network,
            "buses",
        ):
            raise ValueError(
                "Network must provide a 'buses' collection."
            )

        if isinstance(
            tolerance,
            bool,
        ) or not isinstance(
            tolerance,
            (int, float),
        ):
            raise TypeError(
                "tolerance must be a real number."
            )

        tolerance = float(
            tolerance
        )

        if not np.isfinite(
            tolerance
        ):
            raise ValueError(
                "tolerance must be finite."
            )

        if tolerance < 0.0:
            raise ValueError(
                "tolerance cannot be negative."
            )

        self.network = network
        self.buses = network.buses
        self.tolerance = tolerance

        # Diagnostic history only.
        #
        # This does not represent authoritative network state.
        self.converted: list[dict[str, Any]] = []

    # =========================================================
    # BUS INTERFACE VALIDATION
    # =========================================================

    def _validate_bus_interface(
        self,
        bus: Any,
    ) -> None:
        """
        Validate the minimum Bus interface required for
        reactive-power limit handling.
        """

        if not hasattr(
            bus,
            "Q_spec",
        ):
            raise ValueError(
                "Bus must provide 'Q_spec' "
                "for reactive-power limit handling."
            )

        if not hasattr(
            bus,
            "is_pv",
        ):
            raise ValueError(
                "Bus must provide an 'is_pv()' method."
            )

        if not callable(
            bus.is_pv,
        ):
            raise ValueError(
                "Bus 'is_pv' must be callable."
            )

        if not hasattr(
            bus,
            "Q_min",
        ):
            raise ValueError(
                "PV bus must provide 'Q_min'."
            )

        if not hasattr(
            bus,
            "Q_max",
        ):
            raise ValueError(
                "PV bus must provide 'Q_max'."
            )

    # =========================================================
    # YBUS ACCESS
    # =========================================================

    def _get_ybus(self):
        """
        Return the network Ybus.

        Ybus ownership remains with the Network layer.
        """

        Ybus = getattr(
            self.network,
            "Ybus",
            None,
        )

        if Ybus is None:
            raise ValueError(
                "Network Ybus has not been built."
            )

        if not hasattr(
            Ybus,
            "shape",
        ):
            raise ValueError(
                "Network Ybus must provide a matrix shape."
            )

        n = len(
            self.buses
        )

        expected_shape = (
            n,
            n,
        )

        if Ybus.shape != expected_shape:
            raise ValueError(
                "Ybus dimension does not match network "
                f"bus count: expected {expected_shape}, "
                f"received {Ybus.shape}."
            )

        return Ybus

    # =========================================================
    # REACTIVE POWER CALCULATION
    # =========================================================

    def _calculate_q(self) -> np.ndarray:
        """
        Calculate the current AC reactive-power injection
        for every bus.

        PowerMismatch is the shared numerical reference for
        the power-flow formulation.
        """

        Ybus = self._get_ybus()

        mismatch_engine = PowerMismatch(
            self.network,
            Ybus,
        )

        _, Q = mismatch_engine.compute_power()

        Q = np.asarray(
            Q,
            dtype=float,
        ).reshape(-1)

        expected_size = len(
            self.buses
        )

        if Q.size != expected_size:
            raise ValueError(
                "Calculated reactive-power vector has "
                "incorrect dimension: "
                f"expected {expected_size}, "
                f"received {Q.size}."
            )

        if not np.all(
            np.isfinite(Q)
        ):
            raise ValueError(
                "Calculated reactive-power vector contains "
                "NaN or infinite values."
            )

        return Q

    # =========================================================
    # LIMIT VALIDATION
    # =========================================================

    def _validate_limits(
        self,
        bus: Any,
    ) -> tuple[float, float]:
        """
        Validate and return:

            (Q_min, Q_max)
        """

        try:
            q_min = float(
                bus.Q_min
            )

            q_max = float(
                bus.Q_max
            )

        except (
            TypeError,
            ValueError,
        ) as exc:

            raise ValueError(
                "Bus reactive-power limits must be "
                "real numerical values."
            ) from exc

        if not np.isfinite(
            q_min
        ):
            raise ValueError(
                f"Bus '{getattr(bus, 'id', bus)}' "
                "has non-finite Q_min."
            )

        if not np.isfinite(
            q_max
        ):
            raise ValueError(
                f"Bus '{getattr(bus, 'id', bus)}' "
                "has non-finite Q_max."
            )

        if q_min > q_max:
            raise ValueError(
                f"Bus '{getattr(bus, 'id', bus)}' has "
                "Q_min greater than Q_max."
            )

        return (
            q_min,
            q_max,
        )

    # =========================================================
    # PV -> PQ CONVERSION
    # =========================================================

    def _convert_to_pq(
        self,
        bus: Any,
        bus_index: int,
        q_value: float,
        q_limit: float,
        limit_type: str,
    ) -> dict[str, Any]:
        """
        Convert one PV bus to PQ and clamp Q_spec.
        """

        if limit_type not in (
            "Qmin",
            "Qmax",
        ):
            raise ValueError(
                "limit_type must be 'Qmin' or 'Qmax'."
            )

        # -----------------------------------------------------
        # Clamp specified reactive power first.
        # -----------------------------------------------------

        bus.Q_spec = float(
            q_limit
        )

        # -----------------------------------------------------
        # Perform canonical Bus state transition.
        # -----------------------------------------------------

        set_pq = getattr(
            bus,
            "set_pq",
            None,
        )

        if callable(
            set_pq,
        ):

            set_pq()

        else:

            set_type = getattr(
                bus,
                "set_type",
                None,
            )

            if not callable(
                set_type,
            ):
                raise ValueError(
                    "Bus must provide either 'set_pq()' "
                    "or 'set_type()' for PV-to-PQ conversion."
                )

            set_type(
                "PQ"
            )

        # -----------------------------------------------------
        # Verify conversion.
        # -----------------------------------------------------

        is_pq = getattr(
            bus,
            "is_pq",
            None,
        )

        if callable(
            is_pq,
        ):

            if not is_pq():
                raise RuntimeError(
                    "Bus PV-to-PQ conversion failed."
                )

        elif hasattr(
            bus,
            "type",
        ):

            if str(
                bus.type
            ).upper() != "PQ":
                raise RuntimeError(
                    "Bus PV-to-PQ conversion failed."
                )

        return {
            "bus_index": int(
                bus_index
            ),
            "bus_id": getattr(
                bus,
                "id",
                bus_index,
            ),
            "q_calculated": float(
                q_value
            ),
            "q_limit": float(
                q_limit
            ),
            "limit": limit_type,
            "from_type": "PV",
            "to_type": "PQ",
        }

    # =========================================================
    # CHECK LIMITS
    # =========================================================

    def check_limits(
        self,
    ) -> list[dict[str, Any]]:
        """
        Check reactive-power limits on all current PV buses.

        Returns
        -------
        list[dict]
            Conversion records for buses changed from PV to PQ.

        Notes
        -----
        Reactive power is calculated exactly once for the current
        network state.

        Each PV bus can be converted at most once during this
        invocation.

        A bus converted to PQ is skipped by subsequent calls
        unless another higher-level mechanism explicitly changes
        it back to PV.
        """

        if len(
            self.buses
        ) == 0:
            return []

        # -----------------------------------------------------
        # Calculate Q once for the complete current state.
        # -----------------------------------------------------

        Q = self._calculate_q()

        changed: list[dict[str, Any]] = []

        # -----------------------------------------------------
        # Evaluate buses in deterministic network order.
        # -----------------------------------------------------

        for bus_index, bus in enumerate(
            self.buses
        ):

            is_pv = getattr(
                bus,
                "is_pv",
                None,
            )

            if not callable(
                is_pv,
            ):
                raise ValueError(
                    "Bus must provide an 'is_pv()' method."
                )

            # -------------------------------------------------
            # Only PV buses participate.
            # -------------------------------------------------

            if not is_pv():
                continue

            self._validate_bus_interface(
                bus
            )

            q_min, q_max = self._validate_limits(
                bus
            )

            q_calculated = float(
                Q[bus_index]
            )

            # -------------------------------------------------
            # Upper limit.
            # -------------------------------------------------

            if q_calculated > (
                q_max
                +
                self.tolerance
            ):

                record = self._convert_to_pq(
                    bus=bus,
                    bus_index=bus_index,
                    q_value=q_calculated,
                    q_limit=q_max,
                    limit_type="Qmax",
                )

                changed.append(
                    record
                )

                continue

            # -------------------------------------------------
            # Lower limit.
            # -------------------------------------------------

            if q_calculated < (
                q_min
                -
                self.tolerance
            ):

                record = self._convert_to_pq(
                    bus=bus,
                    bus_index=bus_index,
                    q_value=q_calculated,
                    q_limit=q_min,
                    limit_type="Qmin",
                )

                changed.append(
                    record
                )

        # -----------------------------------------------------
        # Preserve diagnostic history.
        # -----------------------------------------------------

        self.converted.extend(
            changed
        )

        return changed

    # =========================================================
    # RESET
    # =========================================================

    def reset_history(
        self,
    ) -> None:
        """
        Clear diagnostic conversion history.

        This method does not alter any Bus state.
        """

        self.converted.clear()

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(
        self,
    ) -> dict[str, Any]:
        """
        Return concise Q-limit handling diagnostics.
        """

        pv_count = 0
        pq_count = 0

        for bus in self.buses:

            is_pv = getattr(
                bus,
                "is_pv",
                None,
            )

            if callable(
                is_pv,
            ) and is_pv():

                pv_count += 1

                continue

            is_pq = getattr(
                bus,
                "is_pq",
                None,
            )

            if callable(
                is_pq,
            ) and is_pq():

                pq_count += 1

        return {
            "handler": "QLimitHandler",
            "buses": len(
                self.buses
            ),
            "pv_buses": pv_count,
            "pq_buses": pq_count,
            "tolerance": float(
                self.tolerance
            ),
            "conversions": len(
                self.converted
            ),
        }

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            "QLimitHandler("
            f"buses={len(self.buses)}, "
            f"tolerance={self.tolerance}"
            ")"
        )


__all__ = [
    "QLimitHandler",
]
