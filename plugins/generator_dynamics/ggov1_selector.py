"""GGOV1 low-value fuel-command selection and tracking signals.

This block owns no controller states. The host evaluates each active controller,
then this deterministic selector chooses the smallest admissible fuel request.
Each controller consumes its own selected-minus-requested tracking error.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

from .controllers import _number


@dataclass(frozen=True, slots=True)
class GGOV1Selection:
    """Immutable result of one low-value selector evaluation."""

    selected_source: str
    selected_fuel_command_pu: float
    tracking_errors_pu: tuple[tuple[str, float], ...]

    def tracking_error_for(self, source: str) -> float:
        """Return selected minus this controller's own requested command."""
        for name, error in self.tracking_errors_pu:
            if name == source:
                return error
        raise KeyError(f"controller source {source!r} was not active")


class GGOV1LowValueSelector:
    """Select the minimum active GGOV1 fuel request and expose tracking errors.

    Accepted source names are 'governor', 'acceleration', and
    'load_temperature'. The latter represents the already-combined
    load/temperature limiter output. Disabled limiters are omitted; the
    governor request is always required. Equal values use the stable priority
    governor, acceleration, load_temperature for reproducible source identity.
    """

    SOURCE_PRIORITY = ("governor", "acceleration", "load_temperature")

    @classmethod
    def select(cls, candidates_pu: Mapping[str, float]) -> GGOV1Selection:
        if not isinstance(candidates_pu, Mapping) or not candidates_pu:
            raise TypeError("candidates_pu must be a non-empty mapping")
        unknown = set(candidates_pu) - set(cls.SOURCE_PRIORITY)
        if unknown:
            raise ValueError(f"unsupported GGOV1 selector sources: {sorted(unknown)!r}")
        if "governor" not in candidates_pu:
            raise ValueError("the governor fuel request is required")
        ordered = []
        for source in cls.SOURCE_PRIORITY:
            if source in candidates_pu:
                value = _number(candidates_pu[source], f"{source}_fuel_command_pu")
                ordered.append((source, value))
        selected_source, selected = min(ordered, key=lambda item: item[1])
        tracking = tuple((source, selected - value) for source, value in ordered)
        return GGOV1Selection(
            selected_source=selected_source,
            selected_fuel_command_pu=selected,
            tracking_errors_pu=tracking,
        )


__all__ = ["GGOV1LowValueSelector", "GGOV1Selection"]
