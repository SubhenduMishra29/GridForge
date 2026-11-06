"""
GridForge V2 - Control Limit Contracts
=======================================

Author:
    Subhendu Mishra

File:
    core/control/limits.py

Purpose
-------
Provides pure, headless limiting primitives for the Control domain.

These primitives are shared by:

    Dynamic Control
        AVR, Governor, PSS, inverter controllers, etc.

    Logic Control
        Comparators, timers, interlocks, threshold logic, etc.

This module contains no controller-specific behavior.

Architectural Rules
-------------------
1. No numerical integration.
2. No network/model access.
3. No plugin imports.
4. No UI dependencies.
5. No controller-specific equations.
6. Limits operate only on supplied values.
7. Limit objects are immutable configuration.
8. Runtime application is deterministic and side-effect free.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math


# ============================================================================
# ERRORS
# ============================================================================


class LimitError(ValueError):
    """Base exception for Control limit errors."""


class LimitConfigurationError(LimitError):
    """Invalid limit configuration."""


class LimitValueError(LimitError):
    """Invalid value supplied to a limit."""


# ============================================================================
# ENUMERATIONS
# ============================================================================


class LimitStatus(str, Enum):
    """
    Resulting position of a value relative to a bounded interval.
    """

    BELOW = "below"
    WITHIN = "within"
    ABOVE = "above"


# ============================================================================
# LIMIT
# ============================================================================


@dataclass(frozen=True)
class Limit:
    """
    Immutable lower/upper bound definition.

    Either bound may be unbounded by using ``None``.

    Examples
    --------
    Bounded:

        Limit(lower=0.0, upper=1.0)

    Lower bounded:

        Limit(lower=0.0)

    Upper bounded:

        Limit(upper=1.0)

    Unbounded:

        Limit()
    """

    lower: float | None = None
    upper: float | None = None

    def __post_init__(self) -> None:
        lower = (
            None
            if self.lower is None
            else _finite_float(
                self.lower,
                "lower",
            )
        )

        upper = (
            None
            if self.upper is None
            else _finite_float(
                self.upper,
                "upper",
            )
        )

        if (
            lower is not None
            and upper is not None
            and lower > upper
        ):
            raise LimitConfigurationError(
                "lower limit cannot be greater "
                "than upper limit."
            )

        object.__setattr__(
            self,
            "lower",
            lower,
        )

        object.__setattr__(
            self,
            "upper",
            upper,
        )

    @property
    def is_lower_bounded(self) -> bool:
        """Whether a lower bound exists."""

        return self.lower is not None

    @property
    def is_upper_bounded(self) -> bool:
        """Whether an upper bound exists."""

        return self.upper is not None

    @property
    def is_bounded(self) -> bool:
        """Whether both bounds exist."""

        return (
            self.lower is not None
            and self.upper is not None
        )

    def contains(
        self,
        value: float,
    ) -> bool:
        """
        Return True when value lies inside the interval.
        """

        value = _finite_float(
            value,
            "value",
        )

        if (
            self.lower is not None
            and value < self.lower
        ):
            return False

        if (
            self.upper is not None
            and value > self.upper
        ):
            return False

        return True

    def status(
        self,
        value: float,
    ) -> LimitStatus:
        """
        Return the position of value relative to the limits.
        """

        value = _finite_float(
            value,
            "value",
        )

        if (
            self.lower is not None
            and value < self.lower
        ):
            return LimitStatus.BELOW

        if (
            self.upper is not None
            and value > self.upper
        ):
            return LimitStatus.ABOVE

        return LimitStatus.WITHIN

    def clamp(
        self,
        value: float,
    ) -> float:
        """
        Clamp value to the configured interval.
        """

        value = _finite_float(
            value,
            "value",
        )

        if (
            self.lower is not None
            and value < self.lower
        ):
            return self.lower

        if (
            self.upper is not None
            and value > self.upper
        ):
            return self.upper

        return value


# ============================================================================
# SATURATION
# ============================================================================


@dataclass(frozen=True)
class Saturation:
    """
    Named saturation primitive.

    Saturation is intentionally separate from ``Limit`` so controller
    implementations can express engineering intent explicitly.

    Example
    -------

        excitation_limit = Saturation(
            lower=0.0,
            upper=5.0,
        )

        efd = excitation_limit.apply(
            raw_efd
        )
    """

    lower: float | None = None
    upper: float | None = None

    def __post_init__(self) -> None:
        self._limit()

    def _limit(self) -> Limit:
        """
        Construct the underlying immutable Limit.

        A new tiny immutable object is acceptable here because the
        saturation configuration itself is immutable.
        """

        return Limit(
            lower=self.lower,
            upper=self.upper,
        )

    @property
    def limits(self) -> Limit:
        """Return the underlying Limit."""

        return self._limit()

    def apply(
        self,
        value: float,
    ) -> float:
        """
        Apply saturation.
        """

        return self._limit().clamp(
            value
        )

    def is_active(
        self,
        value: float,
    ) -> bool:
        """
        Return True when saturation modifies the supplied value.
        """

        value = _finite_float(
            value,
            "value",
        )

        return (
            self._limit().status(value)
            is not LimitStatus.WITHIN
        )

    def status(
        self,
        value: float,
    ) -> LimitStatus:
        """Return saturation status."""

        return self._limit().status(
            value
        )


# ============================================================================
# DEADBAND
# ============================================================================


@dataclass(frozen=True)
class Deadband:
    """
    Symmetric or asymmetric deadband primitive.

    The deadband removes small input deviations around zero.

    Symmetric example:

        Deadband(width=0.01)

    Behavior:

        x > +0.01  → x - 0.01
        |x| <= 0.01 → 0
        x < -0.01  → x + 0.01

    Asymmetric form:

        Deadband(
            lower=0.01,
            upper=0.02,
        )

    Behavior:

        x < -0.01 → x + 0.01
        -0.01 <= x <= 0.02 → 0
        x > +0.02 → x - 0.02

    This is useful for controller error signals and threshold logic.
    """

    lower: float = 0.0
    upper: float | None = None

    def __post_init__(self) -> None:
        lower = _finite_float(
            self.lower,
            "lower",
        )

        if lower < 0.0:
            raise LimitConfigurationError(
                "Deadband lower width cannot be negative."
            )

        if self.upper is None:
            upper = lower
        else:
            upper = _finite_float(
                self.upper,
                "upper",
            )

            if upper < 0.0:
                raise LimitConfigurationError(
                    "Deadband upper width cannot be negative."
                )

        object.__setattr__(
            self,
            "lower",
            lower,
        )

        object.__setattr__(
            self,
            "upper",
            upper,
        )

    @property
    def is_symmetric(self) -> bool:
        """Return True for symmetric deadband."""

        return (
            self.lower == self.upper
        )

    def apply(
        self,
        value: float,
    ) -> float:
        """
        Apply the deadband to value.
        """

        value = _finite_float(
            value,
            "value",
        )

        if (
            -self.lower
            <= value
            <= self.upper
        ):
            return 0.0

        if value < -self.lower:
            return value + self.lower

        return value - self.upper

    def active(
        self,
        value: float,
    ) -> bool:
        """
        Return True when value lies inside the deadband.
        """

        value = _finite_float(
            value,
            "value",
        )

        return (
            -self.lower
            <= value
            <= self.upper
        )


# ============================================================================
# THRESHOLD
# ============================================================================


class ThresholdOperator(str, Enum):
    """
    Comparison operators for discrete control logic.
    """

    GREATER = ">"
    GREATER_EQUAL = ">="
    LESS = "<"
    LESS_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="


@dataclass(frozen=True)
class Threshold:
    """
    Pure threshold comparator.

    This primitive is useful to both Dynamic and Logic Control.

    It does not create a Logic Control component by itself.
    """

    value: float
    operator: ThresholdOperator = ThresholdOperator.GREATER_EQUAL

    def __post_init__(self) -> None:
        value = _finite_float(
            self.value,
            "value",
        )

        if not isinstance(
            self.operator,
            ThresholdOperator,
        ):
            object.__setattr__(
                self,
                "operator",
                ThresholdOperator(
                    self.operator
                ),
            )

        object.__setattr__(
            self,
            "value",
            value,
        )

    def evaluate(
        self,
        value: float,
    ) -> bool:
        """
        Evaluate value against the configured threshold.
        """

        value = _finite_float(
            value,
            "value",
        )

        if self.operator is ThresholdOperator.GREATER:
            return value > self.value

        if self.operator is ThresholdOperator.GREATER_EQUAL:
            return value >= self.value

        if self.operator is ThresholdOperator.LESS:
            return value < self.value

        if self.operator is ThresholdOperator.LESS_EQUAL:
            return value <= self.value

        if self.operator is ThresholdOperator.EQUAL:
            return value == self.value

        if self.operator is ThresholdOperator.NOT_EQUAL:
            return value != self.value

        raise LimitConfigurationError(
            f"Unsupported threshold operator: "
            f"{self.operator!r}"
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _finite_float(
    value: float,
    name: str,
) -> float:
    """
    Convert value to finite float.
    """

    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise LimitValueError(
            f"{name} must be numeric."
        ) from exc

    if not math.isfinite(
        result
    ):
        raise LimitValueError(
            f"{name} must be finite."
        )

    return result


# ============================================================================
# PUBLIC EXPORTS
# ============================================================================

__all__ = [
    "Limit",
    "Saturation",
    "Deadband",
    "Threshold",
    "ThresholdOperator",
    "LimitStatus",
    "LimitError",
    "LimitConfigurationError",
    "LimitValueError",
]
