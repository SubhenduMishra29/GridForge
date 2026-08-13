"""
GridForge Relay Coordination Engine
===================================

File:
    core/protection/coordination/relay_coordination.py

Purpose
-------
Protection-function grading and primary/backup coordination study.

The coordinator evaluates configured protection functions at specified
fault-current points and determines whether the required Coordination
Time Interval (CTI) is satisfied.

Architectural Position
----------------------

    Fault Study
        |
        v
    Fault Current
        |
        v
    Relay Coordination
        |
        +--------------------+
        |                    |
        v                    v
 Primary Function       Backup Function
        |                    |
        +---------+----------+
                  |
                  v
          CoordinationResult

Responsibilities
----------------
This module is responsible for:

    - registering primary/backup protection-function pairs;
    - evaluating operating times at specified fault currents;
    - calculating coordination margins;
    - checking CTI;
    - producing non-mutating TMS adjustment recommendations;
    - providing coordination-study diagnostics.

This module does NOT:

    - detect faults;
    - calculate fault currents;
    - perform short-circuit studies;
    - operate breakers;
    - modify Relay state;
    - modify protection-function settings;
    - schedule protection events;
    - automatically optimise relay settings.

Important V2 Principle
----------------------
Coordination belongs ABOVE individual protection functions.

A physical Relay may contain multiple protection functions:

    Relay
      |
      +-- 50
      +-- 51
      +-- 67
      +-- 21
      +-- ...

Therefore coordination pairs should reference the actual protection
elements being graded, rather than assuming one Relay corresponds to
one protection algorithm.

Timing Interface
----------------
A protection function participating in coordination should expose:

    operating_time(fault_current)

or another explicitly supported timing interface.

The coordinator does not inspect private implementation details to
reconstruct protection behaviour.

For legacy IEC/TCC implementations, a compatibility adapter may be
used through the TCCCurve interface.

No protection setting is changed by this class.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from core.protection.coordination.tcc_curve import (
    TCCCurve,
)


# =====================================================================
# DEFAULTS
# =====================================================================

DEFAULT_CTI = 0.3


# =====================================================================
# COORDINATION PAIR
# =====================================================================


@dataclass(frozen=True)
class CoordinationPair:
    """
    Immutable primary/backup protection-function relationship.

    Parameters
    ----------
    primary:
        Primary protection function.

    backup:
        Backup protection function.

    Notes
    -----
    The objects are referenced only.

    Their settings and operating state are never modified by the
    coordination engine.
    """

    primary: Any
    backup: Any

    @property
    def primary_id(self) -> Any:
        """
        Return the primary protection-function identity.
        """

        return RelayCoordination._object_id(
            self.primary
        )

    @property
    def backup_id(self) -> Any:
        """
        Return the backup protection-function identity.
        """

        return RelayCoordination._object_id(
            self.backup
        )


# =====================================================================
# COORDINATION RESULT
# =====================================================================


@dataclass(frozen=True)
class CoordinationResult:
    """
    Immutable result of one primary/backup coordination study point.
    """

    primary: Any
    backup: Any

    fault_current: float

    primary_time: float
    backup_time: float

    margin: float

    CTI: float

    coordinated: bool

    primary_operates: bool
    backup_operates: bool

    @property
    def required_additional_delay(self) -> float:
        """
        Return additional backup delay required to satisfy CTI.

        Returns
        -------
        float
            Required additional delay.

            0.0
                when already coordinated.

            positive value
                when additional backup delay is required.

            infinity
                when the result cannot establish a finite
                coordination margin.
        """

        if self.coordinated:
            return 0.0

        if math.isinf(
            self.margin
        ):
            return 0.0

        return max(
            0.0,
            self.CTI - self.margin,
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Return a serialization-friendly result dictionary.
        """

        return {
            "primary": self.primary,
            "backup": self.backup,
            "fault_current": self.fault_current,
            "primary_time": self.primary_time,
            "backup_time": self.backup_time,
            "margin": self.margin,
            "CTI": self.CTI,
            "coordinated": self.coordinated,
            "primary_operates": self.primary_operates,
            "backup_operates": self.backup_operates,
            "required_additional_delay": (
                self.required_additional_delay
            ),
        }


# =====================================================================
# RELAY COORDINATION ENGINE
# =====================================================================


class RelayCoordination:
    """
    GridForge V2 protection coordination engine.

    Parameters
    ----------
    CTI:
        Required coordination time interval in seconds.

    Notes
    -----
    This is a non-mutating study engine.

    It does not modify:

        - Relay objects;
        - protection functions;
        - protection settings;
        - breaker state;
        - network state.
    """

    # ================================================================
    # INITIALIZATION
    # ================================================================

    def __init__(
        self,
        CTI: float = DEFAULT_CTI,
    ) -> None:
        """
        Initialize the coordination engine.
        """

        self.CTI = self._validate_non_negative_finite(
            CTI,
            "CTI",
        )

        self.relay_pairs: list[
            CoordinationPair
        ] = []

    # ================================================================
    # VALIDATION
    # ================================================================

    @staticmethod
    def _validate_non_negative_finite(
        value: float,
        name: str,
    ) -> float:
        """
        Validate a finite non-negative scalar.
        """

        try:
            value = float(value)

        except (TypeError, ValueError) as exc:

            raise ValueError(
                f"{name} must be numeric."
            ) from exc

        if not math.isfinite(
            value
        ):
            raise ValueError(
                f"{name} must be finite."
            )

        if value < 0.0:
            raise ValueError(
                f"{name} must be >= 0."
            )

        return value

    # ----------------------------------------------------------------

    @staticmethod
    def _validate_fault_current(
        fault_current: float,
    ) -> float:
        """
        Validate and normalize a fault-current study point.
        """

        try:
            fault_current = abs(
                float(fault_current)
            )

        except (TypeError, ValueError) as exc:

            raise ValueError(
                "Fault current must be numeric."
            ) from exc

        if not math.isfinite(
            fault_current
        ):
            raise ValueError(
                "Fault current must be finite."
            )

        if fault_current <= 0.0:
            raise ValueError(
                "Fault current must be > 0."
            )

        return fault_current

    # ================================================================
    # OBJECT IDENTITY
    # ================================================================

    @staticmethod
    def _object_id(
        protection_function: Any,
    ) -> Any:
        """
        Resolve a stable display identity.

        Preferred V2 identity:

            element_id

        Compatibility fallbacks:

            id
            relay.id
        """

        element_id = getattr(
            protection_function,
            "element_id",
            None,
        )

        if element_id is not None:
            return element_id

        object_id = getattr(
            protection_function,
            "id",
            None,
        )

        if object_id is not None:
            return object_id

        relay = getattr(
            protection_function,
            "relay",
            None,
        )

        if relay is not None:

            relay_id = getattr(
                relay,
                "id",
                None,
            )

            if relay_id is not None:
                return relay_id

        return None

    # ================================================================
    # PAIR REGISTRATION
    # ================================================================

    def add_coordination_pair(
        self,
        primary: Any,
        backup: Any,
    ) -> CoordinationPair:
        """
        Register a primary/backup protection-function pair.

        Returns
        -------
        CoordinationPair
            Registered immutable pair.

        Notes
        -----
        The pair stores references only.

        No protection state or settings are modified.
        """

        if primary is None:
            raise ValueError(
                "Primary protection function cannot be None."
            )

        if backup is None:
            raise ValueError(
                "Backup protection function cannot be None."
            )

        primary_id = self._object_id(
            primary
        )

        backup_id = self._object_id(
            backup
        )

        if primary_id is None:
            raise ValueError(
                "Primary protection function must provide "
                "a stable identity."
            )

        if backup_id is None:
            raise ValueError(
                "Backup protection function must provide "
                "a stable identity."
            )

        if (
            primary is backup
            or primary_id == backup_id
        ):
            raise ValueError(
                "Primary and backup protection functions "
                "must be different."
            )

        pair = CoordinationPair(
            primary=primary,
            backup=backup,
        )

        self.relay_pairs.append(
            pair
        )

        return pair

    # ================================================================
    # OPERATING TIME
    # ================================================================

    @classmethod
    def _operating_time(
        cls,
        protection_function: Any,
        fault_current: float,
    ) -> float:
        """
        Determine protection-function operating time at a specified
        fault current.

        Preferred interface
        -------------------
        The protection function exposes:

            operating_time(fault_current)

        Compatibility interface
        ------------------------
        Legacy IEC/TCC implementations may expose:

            pickup_current
            curve
            TMS

        In that case TCCCurve is used as a compatibility calculation.

        Returns
        -------
        float
            Operating time in seconds.

            math.inf
                when the protection function does not operate at the
                specified current.
        """

        fault_current = cls._validate_fault_current(
            fault_current
        )

        operating_time = getattr(
            protection_function,
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

            except TypeError as exc:

                raise TypeError(
                    f"Protection function "
                    f"'{cls._object_id(protection_function)}' "
                    "does not implement the required "
                    "operating_time(fault_current) interface."
                ) from exc

            return cls._validate_operating_time(
                result,
                protection_function,
            )

        # ------------------------------------------------------------
        # Legacy IEC/TCC compatibility path.
        #
        # This path is intentionally isolated. New V2 protection
        # functions should expose operating_time(fault_current).
        # ------------------------------------------------------------

        pickup_current = getattr(
            protection_function,
            "pickup_current",
            None,
        )

        curve_type = getattr(
            protection_function,
            "curve",
            None,
        )

        TMS = getattr(
            protection_function,
            "TMS",
            None,
        )

        if (
            pickup_current is not None
            and curve_type is not None
            and TMS is not None
        ):

            try:
                pickup_current = float(
                    pickup_current
                )

                TMS = float(
                    TMS
                )

            except (TypeError, ValueError) as exc:

                raise ValueError(
                    "Legacy IEC protection settings must be numeric."
                ) from exc

            if (
                not math.isfinite(
                    pickup_current
                )
                or pickup_current <= 0.0
            ):
                raise ValueError(
                    "pickup_current must be finite and positive."
                )

            if (
                not math.isfinite(
                    TMS
                )
                or TMS < 0.0
            ):
                raise ValueError(
                    "TMS must be finite and >= 0."
                )

            tcc = TCCCurve(
                curve_type=curve_type
            )

            result = tcc.calculate_time(
                fault_current=fault_current,
                pickup_current=pickup_current,
                TMS=TMS,
            )

            return cls._validate_operating_time(
                result,
                protection_function,
            )

        raise TypeError(
            f"Protection function "
            f"'{cls._object_id(protection_function)}' "
            "does not expose a supported operating-time "
            "interface."
        )

    # ----------------------------------------------------------------

    @staticmethod
    def _validate_operating_time(
        value: Any,
        protection_function: Any,
    ) -> float:
        """
        Validate a protection-function operating-time result.
        """

        try:
            value = float(
                value
            )

        except (TypeError, ValueError) as exc:

            raise ValueError(
                f"Protection function "
                f"'{RelayCoordination._object_id(protection_function)}' "
                "returned a non-numeric operating time."
            ) from exc

        if math.isnan(
            value
        ):
            raise ValueError(
                f"Protection function "
                f"'{RelayCoordination._object_id(protection_function)}' "
                "returned NaN operating time."
            )

        if value < 0.0:
            raise ValueError(
                f"Protection function "
                f"'{RelayCoordination._object_id(protection_function)}' "
                "returned a negative operating time."
            )

        return value

    # ================================================================
    # CHECK PAIR
    # ================================================================

    def check_pair(
        self,
        primary: Any,
        backup: Any,
        fault_current: float,
    ) -> CoordinationResult:
        """
        Check coordination between primary and backup protection
        functions at one fault-current study point.

        Coordination criterion:

            backup_time - primary_time >= CTI

        If the primary does not operate, the study point is treated
        as non-operating for the primary/backup pair.

        If the backup does not operate while the primary does,
        the pair cannot provide backup protection at this study point.
        """

        fault_current = self._validate_fault_current(
            fault_current
        )

        primary_time = self._operating_time(
            primary,
            fault_current,
        )

        backup_time = self._operating_time(
            backup,
            fault_current,
        )

        primary_operates = math.isfinite(
            primary_time
        )

        backup_operates = math.isfinite(
            backup_time
        )

        # ------------------------------------------------------------
        # Neither element operates.
        #
        # This is not a coordination failure; there is simply no
        # protection operation at this study point.
        # ------------------------------------------------------------

        if not primary_operates:

            margin = float(
                "inf"
            )

            coordinated = True

        # ------------------------------------------------------------
        # Primary operates, backup does not.
        #
        # The backup cannot fulfil its intended role at this point.
        # ------------------------------------------------------------

        elif not backup_operates:

            margin = float(
                "-inf"
            )

            coordinated = False

        # ------------------------------------------------------------
        # Both operate.
        # ------------------------------------------------------------

        else:

            margin = (
                backup_time
                - primary_time
            )

            coordinated = (
                margin >= self.CTI
            )

        return CoordinationResult(
            primary=self._object_id(
                primary
            ),
            backup=self._object_id(
                backup
            ),
            fault_current=fault_current,
            primary_time=primary_time,
            backup_time=backup_time,
            margin=margin,
            CTI=self.CTI,
            coordinated=coordinated,
            primary_operates=primary_operates,
            backup_operates=backup_operates,
        )

    # ================================================================
    # REGISTERED STUDY
    # ================================================================

    def evaluate(
        self,
        fault_current: float,
    ) -> list[CoordinationResult]:
        """
        Evaluate every registered coordination pair at one
        fault-current study point.
        """

        fault_current = self._validate_fault_current(
            fault_current
        )

        results: list[
            CoordinationResult
        ] = []

        for pair in self.relay_pairs:

            results.append(
                self.check_pair(
                    primary=pair.primary,
                    backup=pair.backup,
                    fault_current=fault_current,
                )
            )

        return results

    # ================================================================
    # MULTI-POINT STUDY
    # ================================================================

    def evaluate_points(
        self,
        fault_currents: list[float] | tuple[float, ...],
    ) -> list[CoordinationResult]:
        """
        Evaluate all registered pairs over multiple fault-current
        study points.

        This is useful for coordination studies where the CTI must
        be verified over a range of fault levels rather than at one
        nominal fault current.
        """

        results: list[
            CoordinationResult
        ] = []

        for fault_current in fault_currents:

            results.extend(
                self.evaluate(
                    fault_current
                )
            )

        return results

    # ================================================================
    # TMS RECOMMENDATION
    # ================================================================

    def suggest_TMS_change(
        self,
        result: CoordinationResult | dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate a non-mutating TMS adjustment recommendation.

        No relay or protection-function setting is modified.

        The recommendation is deliberately conservative:

            increase backup delay

        Automatic optimisation is outside the responsibility of
        this class.
        """

        if isinstance(
            result,
            CoordinationResult,
        ):
            coordinated = result.coordinated
            margin = result.margin
            backup = result.backup

        elif isinstance(
            result,
            dict,
        ):

            if "coordinated" not in result:
                raise ValueError(
                    "Invalid coordination result: "
                    "'coordinated' is required."
                )

            coordinated = bool(
                result["coordinated"]
            )

            margin = result.get(
                "margin"
            )

            backup = result.get(
                "backup"
            )

        else:

            raise TypeError(
                "result must be a CoordinationResult "
                "or result dictionary."
            )

        if coordinated:

            return {
                "action": "NO_CHANGE",
                "reason": (
                    "Primary and backup protection functions "
                    "satisfy the required CTI."
                ),
                "required_CTI": self.CTI,
                "actual_margin": margin,
                "backup": backup,
            }

        if margin == float(
            "-inf"
        ):

            return {
                "action": "BACKUP_DOES_NOT_OPERATE",
                "reason": (
                    "The backup protection function does not "
                    "operate at the specified fault-current "
                    "study point."
                ),
                "required_CTI": self.CTI,
                "actual_margin": margin,
                "backup": backup,
            }

        if margin is None:

            raise ValueError(
                "Invalid coordination result: "
                "'margin' is required."
            )

        return {
            "action": "INCREASE_BACKUP_DELAY",
            "reason": (
                "Coordination margin is below the required CTI."
            ),
            "required_CTI": self.CTI,
            "actual_margin": margin,
            "required_additional_delay": max(
                0.0,
                self.CTI - float(
                    margin
                ),
            ),
            "backup": backup,
        }

    # ================================================================
    # CLEAR
    # ================================================================

    def clear_pairs(
        self,
    ) -> None:
        """
        Remove all registered coordination pairs.
        """

        self.relay_pairs.clear()

    # ================================================================
    # SUMMARY
    # ================================================================

    def summary(
        self,
    ) -> dict[str, Any]:
        """
        Return coordination-engine diagnostics.
        """

        return {
            "CTI": self.CTI,
            "pair_count": len(
                self.relay_pairs
            ),
            "pairs": [
                {
                    "primary": pair.primary_id,
                    "backup": pair.backup_id,
                }
                for pair in self.relay_pairs
            ],
        }

    # ================================================================
    # REPRESENTATION
    # ================================================================

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


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "CoordinationPair",
    "CoordinationResult",
    "RelayCoordination",
]
