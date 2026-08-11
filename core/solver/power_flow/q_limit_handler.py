```python
"""
GridForge Reactive Power Limit Handler
======================================

File:
    core/solver/power_flow/q_limit_handler.py

Industrial PV/PQ Reactive Power Limit Handler

Responsibilities
----------------
- Detect reactive-power limit violations on PV buses.
- Convert violating PV buses to PQ buses.
- Clamp the specified reactive power to Qmin/Qmax.
- Preserve deterministic PV -> PQ state transitions.
- Provide diagnostics describing converted buses.

This module is part of the Power Flow numerical orchestration
layer.

It does NOT:
- Perform Newton-Raphson iteration.
- Build Ybus.
- Calculate Ybus.
- Assemble the Jacobian.
- Solve linear systems.
- Modify network topology.
- Perform contingency analysis.
- Perform short-circuit analysis.
- Perform protection decisions.

The actual AC power calculation is delegated to the shared
reference numerical component:

    core.solver.common.mismatch.PowerMismatch

Bus classification remains owned by the unified GridForge
Bus model.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

import numpy as np

from core.solver.common.mismatch import PowerMismatch


class QLimitHandler:
    """
    Handle generator reactive-power limits during AC
    Newton-Raphson power-flow calculations.

    Parameters
    ----------
    network:
        GridForge Network object containing the ordered
        collection of Bus objects.

    tolerance:
        Numerical tolerance used when comparing calculated
        reactive power against Qmin/Qmax.

    Notes
    -----
    Only PV buses are considered for conversion.

    A bus already classified as PQ is never converted again.

    The handler performs the following state transition:

        PV
         |
         | Q > Qmax
         | Q < Qmin
         v
        PQ

    When a limit is violated, the specified reactive power
    is clamped to the violated limit.

    Example:

        Q > Qmax

        bus.Q_spec = bus.Q_max
        bus -> PQ

    or:

        Q < Qmin

        bus.Q_spec = bus.Q_min
        bus -> PQ

    The solver then rebuilds its mismatch/Jacobian structure
    on the next Newton-Raphson iteration.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        network,
        tolerance: float = 1.0e-8,
    ):
        """
        Initialize the reactive-power limit handler.

        Parameters
        ----------
        network:
            GridForge Network object.

        tolerance:
            Non-negative numerical tolerance for Q-limit
            comparisons.

        Raises
        ------
        ValueError
            If the network is invalid or tolerance is invalid.

        TypeError
            If tolerance has an invalid type.
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
        self.tolerance = tolerance

        self.buses = network.buses

        # -----------------------------------------------------
        # Record of buses converted during the current solver
        # lifecycle.
        #
        # This is diagnostic information only.
        # -----------------------------------------------------

        self.converted = []

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_bus_interface(
        self,
        bus,
    ) -> None:
        """
        Validate the minimum Bus interface required by the
        Q-limit handler.

        The unified Bus model is expected to provide:

            bus.Q_spec
            bus.is_pv()

        and reactive limits:

            bus.Q_min
            bus.Q_max

        Raises
        ------
        ValueError
            If required information is unavailable.
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
    # YBUS VALIDATION
    # =========================================================

    def _get_ybus(
        self,
    ):
        """
        Return the network Ybus.

        Ybus ownership remains outside this module.

        Returns
        -------
        matrix-like
            Network Ybus matrix.

        Raises
        ------
        ValueError
            If Ybus is unavailable or has an invalid shape.
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

        if Ybus.shape != (
            n,
            n,
        ):
            raise ValueError(
                "Ybus dimension does not match network bus "
                f"count: expected {(n, n)}, "
                f"received {Ybus.shape}."
            )

        return Ybus

    # =========================================================
    # POWER CALCULATION
    # =========================================================

    def _calculate_q(
        self,
    ):
        """
        Calculate current AC bus reactive-power injections.

        The shared PowerMismatch reference implementation is
        deliberately used so that Q-limit handling follows the
        same electrical convention as the Newton-Raphson
        mismatch and Jacobian.

        Returns
        -------
        np.ndarray
            Calculated Q injection for every bus.
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

        if Q.size != len(
            self.buses
        ):
            raise ValueError(
                "Calculated reactive-power vector has "
                "incorrect dimension."
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
        bus,
    ):
        """
        Validate and return the reactive-power limits.

        Returns
        -------
        tuple[float, float]
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
        ) or not np.isfinite(
            q_max
        ):
            raise ValueError(
                "Bus reactive-power limits must be finite."
            )

        if q_min > q_max:
            raise ValueError(
                "Bus Q_min cannot be greater than Q_max."
            )

        return q_min, q_max

    # =========================================================
    # BUS CONVERSION
    # =========================================================

    def _convert_to_pq(
        self,
        bus,
        bus_index: int,
        q_value: float,
        q_limit: float,
        limit_type: str,
    ) -> dict:
        """
        Convert a PV bus to PQ and clamp its Q specification.

        Parameters
        ----------
        bus:
            Bus object.

        bus_index:
            Index in network.buses.

        q_value:
            Calculated reactive injection before conversion.

        q_limit:
            Limit at which the bus is clamped.

        limit_type:
            Either ``"Qmin"`` or ``"Qmax"``.

        Returns
        -------
        dict
            Conversion diagnostic record.

        Notes
        -----
        This method intentionally performs only the state
        transition required by the power-flow formulation.

        The solver remains responsible for continuing the
        Newton-Raphson iteration after the classification
        changes.
        """

        # -----------------------------------------------------
        # Clamp specified reactive power.
        # -----------------------------------------------------

        bus.Q_spec = float(
            q_limit
        )

        # -----------------------------------------------------
        # Change bus classification.
        #
        # The unified Bus model is expected to expose a
        # conversion method.
        # -----------------------------------------------------

        if hasattr(
            bus,
            "set_pq",
        ) and callable(
            bus.set_pq,
        ):

            bus.set_pq()

        elif hasattr(
            bus,
            "set_type",
        ) and callable(
            bus.set_type,
        ):

            bus.set_type(
                "PQ"
            )

        else:
            raise ValueError(
                "Bus must provide either 'set_pq()' or "
                "'set_type()' to perform PV-to-PQ conversion."
            )

        # -----------------------------------------------------
        # Verify the state transition.
        # -----------------------------------------------------

        if hasattr(
            bus,
            "is_pq",
        ) and callable(
            bus.is_pq,
        ):

            if not bus.is_pq():
                raise RuntimeError(
                    "Bus PV-to-PQ conversion failed."
                )

        record = {
            "bus_index": int(
                bus_index
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

        return record

    # =========================================================
    # CHECK LIMITS
    # =========================================================

    def check_limits(
        self,
    ) -> list:
        """
        Check reactive-power limits on all PV buses.

        Returns
        -------
        list[dict]
            List of buses converted from PV to PQ during this
            call.

            An empty list means no conversion occurred.

        Notes
        -----
        The method calculates Q once for the current network
        state and evaluates every PV bus against its limits.

        At most one conversion occurs per bus during a single
        call.

        Once converted to PQ, a bus is no longer considered
        by subsequent calls unless some higher-level mechanism
        explicitly changes it back to PV.
        """

        if len(
            self.buses
        ) == 0:
            return []

        Q = self._calculate_q()

        changed = []

        for i, bus in enumerate(
            self.buses
        ):

            # -------------------------------------------------
            # Only PV buses are candidates.
            # -------------------------------------------------

            if not hasattr(
                bus,
                "is_pv",
            ):
                raise ValueError(
                    "Bus must provide an 'is_pv()' method."
                )

            if not bus.is_pv():
                continue

            self._validate_bus_interface(
                bus
            )

            q_min, q_max = self._validate_limits(
                bus
            )

            q_calculated = float(
                Q[i]
            )

            # -------------------------------------------------
            # Upper reactive-power limit.
            # -------------------------------------------------

            if q_calculated > (
                q_max
                +
                self.tolerance
            ):

                record = self._convert_to_pq(
                    bus=bus,
                    bus_index=i,
                    q_value=q_calculated,
                    q_limit=q_max,
                    limit_type="Qmax",
                )

                changed.append(
                    record
                )

                continue

            # -------------------------------------------------
            # Lower reactive-power limit.
            # -------------------------------------------------

            if q_calculated < (
                q_min
                -
                self.tolerance
            ):

                record = self._convert_to_pq(
                    bus=bus,
                    bus_index=i,
                    q_value=q_calculated,
                    q_limit=q_min,
                    limit_type="Qmin",
                )

                changed.append(
                    record
                )

        # -----------------------------------------------------
        # Preserve conversion history.
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

        This does NOT change bus states.
        """

        self.converted = []

    # =========================================================
    # DIAGNOSTICS
    # =========================================================

    def summary(
        self,
    ) -> dict:
        """
        Return Q-limit handler diagnostics.
        """

        pv_count = 0
        pq_count = 0

        for bus in self.buses:

            if hasattr(
                bus,
                "is_pv",
            ) and bus.is_pv():

                pv_count += 1

            elif hasattr(
                bus,
                "is_pq",
            ) and bus.is_pq():

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
        Developer-friendly representation.
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
```
