```python
"""
GridForge Relay Coordination Engine
===================================

File:
    core/protection/coordination/relay_coordination.py

Purpose
-------
Protection relay grading and primary/backup coordination.

Responsibilities
----------------
- Register primary/backup relay pairs.
- Calculate primary and backup operating times.
- Check Coordination Time Interval (CTI).
- Report coordination margins.
- Provide a non-mutating TMS adjustment recommendation.

This module does NOT:
- Detect faults.
- Calculate system fault currents.
- Operate circuit breakers.
- Modify the electrical network.
- Modify authoritative Relay model state.
- Perform automatic optimisation.

Fault currents are supplied by the calling protection/fault-study
layer.

TCC calculations are delegated to:

    core.protection.coordination.tcc_curve.TCCCurve

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

import math
from typing import Any

from core.protection.coordination.tcc_curve import (
    TCCCurve,
)


class RelayCoordination:
    """
    Relay coordination and grading engine.

    Parameters
    ----------
    CTI:
        Required coordination time interval in seconds.

    Notes
    -----
    The coordinator is intentionally non-mutating.

    It evaluates relay behaviour and produces coordination
    recommendations. It does not directly alter relay settings.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        CTI: float = 0.3,
    ) -> None:
        """
        Initialize the coordination engine.
        """

        self.CTI = float(
            CTI
        )

        if not math.isfinite(
            self.CTI
        ):
            raise ValueError(
                "CTI must be finite."
            )

        if self.CTI < 0.0:
            raise ValueError(
                "CTI must be >= 0."
            )

        self.relay_pairs: list[
            dict[str, Any]
        ] = []

    # =========================================================
    # ADD COORDINATION PAIR
    # =========================================================

    def add_coordination_pair(
        self,
        primary,
        backup,
    ) -> None:
        """
        Register a primary/backup relay pair.

        Parameters
        ----------
        primary:
            Primary protection relay.

        backup:
            Backup protection relay.

        Notes
        -----
        The coordinator stores references only. It does not
        modify either relay.
        """

        if primary is None:
            raise ValueError(
                "Primary relay cannot be None."
            )

        if backup is None:
            raise ValueError(
                "Backup relay cannot be None."
            )

        primary_id = getattr(
            primary,
            "id",
            None,
        )

        backup_id = getattr(
            backup,
            "id",
            None,
        )

        if primary_id is None:
            raise ValueError(
                "Primary relay must provide an 'id'."
            )

        if backup_id is None:
            raise ValueError(
                "Backup relay must provide an 'id'."
            )

        if primary_id == backup_id:
            raise ValueError(
                "Primary and backup relays "
                "must be different."
            )

        self.relay_pairs.append(
            {
                "primary": primary,
                "backup": backup,
            }
        )

    # =========================================================
    # OPERATING TIME
    # =========================================================

    @staticmethod
    def _operating_time(
        relay,
        fault_current: float,
    ) -> float:
        """
        Determine relay operating time for a specified
        fault current.

        Supported relay interfaces
        --------------------------
        1. Protection relay exposing:

               operating_time(fault_current)

        2. IEC-style relay exposing:

               pickup_current
               curve
               TMS

           In this case the calculation is delegated to TCCCurve.

        Returns
        -------
        float
            Operating time in seconds.

            infinity
                when the relay does not operate at the
                specified fault current.
        """

        fault_current = abs(
            float(fault_current)
        )

        if not math.isfinite(
            fault_current
        ):
            raise ValueError(
                "Fault current must be finite."
            )

        # -----------------------------------------------------
        # Preferred protection-relay interface
        # -----------------------------------------------------

        operating_time = getattr(
            relay,
            "operating_time",
            None,
        )

        if callable(
            operating_time
        ):

            try:
                result = operating_time(
                    fault_current
                )

                return float(
                    result
                )

            except TypeError:
                # -------------------------------------------------
                # Compatibility with legacy relay implementations
                # whose operating_time() takes no argument.
                #
                # Do not silently use that value unless the relay
                # exposes enough information to perform the
                # specified-current calculation below.
                # -------------------------------------------------
                pass

        # -----------------------------------------------------
        # IEC inverse-time relay interface
        # -----------------------------------------------------

        pickup_current = getattr(
            relay,
            "pickup_current",
            None,
        )

        curve_type = getattr(
            relay,
            "curve",
            None,
        )

        TMS = getattr(
            relay,
            "TMS",
            None,
        )

        if (
            pickup_current is not None
            and curve_type is not None
            and TMS is not None
        ):

            tcc = TCCCurve(
                curve_type=curve_type
            )

            return tcc.calculate_time(
                fault_current=fault_current,
                pickup_current=float(
                    pickup_current
                ),
                TMS=float(TMS),
            )

        raise TypeError(
            f"Relay '{getattr(relay, 'id', '<unknown>')}' "
            "does not expose a supported operating-time "
            "interface."
        )

    # =========================================================
    # CHECK COORDINATION
    # =========================================================

    def check_pair(
        self,
        primary,
        backup,
        fault_current: float,
    ) -> dict:
        """
        Check coordination between a primary and backup relay.

        Parameters
        ----------
        primary:
            Primary relay.

        backup:
            Backup relay.

        fault_current:
            Fault current used for the coordination study.

        Returns
        -------
        dict
            Coordination result containing:

                primary
                backup
                fault_current
                primary_time
                backup_time
                margin
                CTI
                coordinated
        """

        fault_current = abs(
            float(fault_current)
        )

        if not math.isfinite(
            fault_current
        ):
            raise ValueError(
                "Fault current must be finite."
            )

        primary_time = self._operating_time(
            primary,
            fault_current,
        )

        backup_time = self._operating_time(
            backup,
            fault_current,
        )

        # -----------------------------------------------------
        # Coordination margin
        # -----------------------------------------------------

        if math.isinf(
            primary_time
        ):

            margin = float("inf")

        elif math.isinf(
            backup_time
        ):

            margin = float("inf")

        else:

            margin = (
                backup_time
                -
                primary_time
            )

        coordinated = (
            margin >= self.CTI
        )

        return {
            "primary": getattr(
                primary,
                "id",
                None,
            ),
            "backup": getattr(
                backup,
                "id",
                None,
            ),
            "fault_current": fault_current,
            "primary_time": primary_time,
            "backup_time": backup_time,
            "margin": margin,
            "CTI": self.CTI,
            "coordinated": coordinated,
        }

    # =========================================================
    # RUN STUDY
    # =========================================================

    def evaluate(
        self,
        fault_current: float,
    ) -> list[dict]:
        """
        Evaluate all registered coordination pairs.

        Parameters
        ----------
        fault_current:
            Fault current used for the study.

        Returns
        -------
        list[dict]
            Coordination results for every registered pair.
        """

        results = []

        for pair in self.relay_pairs:

            result = self.check_pair(
                primary=pair["primary"],
                backup=pair["backup"],
                fault_current=fault_current,
            )

            results.append(
                result
            )

        return results

    # =========================================================
    # TMS ADJUSTMENT RECOMMENDATION
    # =========================================================

    def suggest_TMS_change(
        self,
        result: dict,
    ) -> dict:
        """
        Generate a non-mutating TMS adjustment recommendation.

        This method does NOT change relay settings.

        Automatic optimisation can be added later using:

            MILP
            Genetic Algorithm
            Particle Swarm Optimisation

        Returns
        -------
        dict
            Recommended coordination action.
        """

        if "coordinated" not in result:
            raise ValueError(
                "Invalid coordination result."
            )

        if result["coordinated"]:

            return {
                "action": "NO_CHANGE",
                "reason": (
                    "Primary and backup relays "
                    "satisfy the required CTI."
                ),
            }

        return {
            "action": (
                "INCREASE_BACKUP_DELAY"
            ),
            "reason": (
                "Coordination margin is below "
                "the required CTI."
            ),
            "required_CTI": self.CTI,
            "actual_margin": result.get(
                "margin"
            ),
            "backup": result.get(
                "backup"
            ),
        }

    # =========================================================
    # CLEAR PAIRS
    # =========================================================

    def clear_pairs(
        self,
    ) -> None:
        """
        Remove all registered coordination pairs.
        """

        self.relay_pairs.clear()

    # =========================================================
    # SUMMARY
    # =========================================================

    def summary(
        self,
    ) -> dict:
        """
        Return coordination-engine status.
        """

        return {
            "CTI": self.CTI,
            "pair_count": len(
                self.relay_pairs
            ),
            "pairs": [
                {
                    "primary": getattr(
                        pair["primary"],
                        "id",
                        None,
                    ),
                    "backup": getattr(
                        pair["backup"],
                        "id",
                        None,
                    ),
                }
                for pair in self.relay_pairs
            ],
        }

    # =========================================================
    # DEBUG
    # =========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Developer-friendly representation.
        """

        return (
            f"<RelayCoordination "
            f"CTI={self.CTI:.4f}s, "
            f"pairs={len(self.relay_pairs)}>"
        )


__all__ = [
    "RelayCoordination",
]
```
