"""
GridForge V2 Protection Execution Context
=========================================

File
----
core/protection/context.py

Purpose
-------
Defines the immutable execution context supplied to protection
functions during evaluation.

ProtectionContext is an execution-time snapshot. It carries temporal,
event, supervision, metadata, and authoritative subsystem references
required by protection-function evaluation.

It does not own simulation time, network state, measurement state,
relay state, or protection state.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping


# =====================================================================
# VALIDATION HELPERS
# =====================================================================


def _normalize_mapping(
    value: Mapping[str, Any],
    name: str,
) -> MappingProxyType:
    """
    Validate, normalize, copy, and freeze a string-keyed mapping.

    Mapping values remain opaque caller-owned objects.

    Keys must be non-empty strings after stripping whitespace.
    Normalization collisions are rejected.
    """

    if not isinstance(value, Mapping):
        raise TypeError(
            f"{name} must be a mapping."
        )

    normalized: dict[str, Any] = {}

    for key, item in value.items():

        if not isinstance(key, str):
            raise TypeError(
                f"{name} keys must be strings."
            )

        normalized_key = key.strip()

        if not normalized_key:
            raise ValueError(
                f"{name} keys cannot be empty."
            )

        if normalized_key in normalized:
            raise ValueError(
                f"Duplicate normalized {name} key "
                f"'{normalized_key}'."
            )

        normalized[normalized_key] = item

    return MappingProxyType(normalized)


def _normalize_optional_string(
    value: Any,
    name: str,
) -> str | None:
    """
    Normalize an optional string.

    Empty or whitespace-only strings become None.
    """

    if value is None:
        return None

    if not isinstance(value, str):
        raise TypeError(
            f"{name} must be a string or None."
        )

    normalized = value.strip()

    return normalized or None


# =====================================================================
# PROTECTION EXECUTION CONTEXT
# =====================================================================


@dataclass(
    frozen=True,
    slots=True,
)
class ProtectionContext:
    """
    Immutable execution context for one protection evaluation.

    Parameters
    ----------
    time:
        Current protection-evaluation time.

        GridForge protection execution time is represented as a
        non-negative finite scalar supplied by the caller.

        ProtectionContext does not own a clock and does not advance
        time.

    timestep:
        Optional non-negative elapsed time since the previous
        protection evaluation.

    event_id:
        Optional event identifier.

    event_type:
        Optional event classification.

        Stored in canonical uppercase form.

    network_state:
        Optional reference to authoritative network state.

        The object is referenced, not copied or owned.

    simulation_state:
        Optional reference to authoritative simulation state.

        The object is referenced, not copied or owned.

    supervision:
        Explicit execution-time supervision information.

    metadata:
        Optional non-authoritative execution metadata.

    Notes
    -----
    The dataclass is frozen.

    Mapping fields are copied into new dictionaries and exposed through
    MappingProxyType.

    This provides shallow mapping immutability. Mutable objects stored
    as mapping values remain caller-owned.
    """

    # =================================================================
    # TEMPORAL INFORMATION
    # =================================================================

    time: float

    timestep: float | None = None

    # =================================================================
    # EVENT INFORMATION
    # =================================================================

    event_id: str | None = None

    event_type: str | None = None

    # =================================================================
    # AUTHORITATIVE REFERENCES
    # =================================================================

    network_state: Any = None

    simulation_state: Any = None

    # =================================================================
    # EXECUTION INFORMATION
    # =================================================================

    supervision: Mapping[str, Any] = field(
        default_factory=dict
    )

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    # =================================================================
    # INITIALIZATION / VALIDATION
    # =================================================================

    def __post_init__(self) -> None:
        """
        Validate and normalize the execution context.
        """

        # -------------------------------------------------------------
        # Evaluation time
        # -------------------------------------------------------------

        try:
            time = float(self.time)

        except (TypeError, ValueError) as exc:
            raise TypeError(
                "ProtectionContext.time must be numeric."
            ) from exc

        if not isfinite(time):
            raise ValueError(
                "ProtectionContext.time must be finite."
            )

        if time < 0.0:
            raise ValueError(
                "ProtectionContext.time cannot be negative."
            )

        object.__setattr__(
            self,
            "time",
            time,
        )

        # -------------------------------------------------------------
        # Timestep
        # -------------------------------------------------------------

        if self.timestep is not None:

            try:
                timestep = float(self.timestep)

            except (TypeError, ValueError) as exc:
                raise TypeError(
                    "ProtectionContext.timestep must be numeric "
                    "or None."
                ) from exc

            if not isfinite(timestep):
                raise ValueError(
                    "ProtectionContext.timestep must be finite."
                )

            if timestep < 0.0:
                raise ValueError(
                    "ProtectionContext.timestep cannot be negative."
                )

            object.__setattr__(
                self,
                "timestep",
                timestep,
            )

        # -------------------------------------------------------------
        # Event identifier
        # -------------------------------------------------------------

        object.__setattr__(
            self,
            "event_id",
            _normalize_optional_string(
                self.event_id,
                "ProtectionContext.event_id",
            ),
        )

        # -------------------------------------------------------------
        # Event type
        # -------------------------------------------------------------

        event_type = _normalize_optional_string(
            self.event_type,
            "ProtectionContext.event_type",
        )

        if event_type is not None:
            event_type = event_type.upper()

        object.__setattr__(
            self,
            "event_type",
            event_type,
        )

        # -------------------------------------------------------------
        # Supervision mapping
        # -------------------------------------------------------------

        object.__setattr__(
            self,
            "supervision",
            _normalize_mapping(
                self.supervision,
                "ProtectionContext.supervision",
            ),
        )

        # -------------------------------------------------------------
        # Metadata mapping
        # -------------------------------------------------------------

        object.__setattr__(
            self,
            "metadata",
            _normalize_mapping(
                self.metadata,
                "ProtectionContext.metadata",
            ),
        )

    # =================================================================
    # TEMPORAL ACCESS
    # =================================================================

    @property
    def current_time(self) -> float:
        """
        Return the current protection-evaluation time.
        """

        return self.time

    # -----------------------------------------------------------------

    @property
    def elapsed_time(self) -> float | None:
        """
        Return the elapsed time since the previous evaluation.
        """

        return self.timestep

    # -----------------------------------------------------------------

    def measurement_time(self) -> float:
        """
        Return the timestamp to use for time-dependent measurement
        validity evaluation.
        """

        return self.time

    # =================================================================
    # EVENT ACCESS
    # =================================================================

    @property
    def has_event(self) -> bool:
        """
        Return True when an event identifier is present.
        """

        return self.event_id is not None

    # -----------------------------------------------------------------

    def is_event_type(
        self,
        event_type: str,
    ) -> bool:
        """
        Return True when the current event matches ``event_type``.

        Comparison is case-insensitive and ignores surrounding
        whitespace.
        """

        if not isinstance(event_type, str):
            return False

        if self.event_type is None:
            return False

        normalized = event_type.strip()

        if not normalized:
            return False

        return (
            self.event_type.casefold()
            == normalized.casefold()
        )

    # =================================================================
    # SUPERVISION
    # =================================================================

    def supervision_get(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Return explicitly supplied supervision information.

        The value is not interpreted.
        """

        if not isinstance(name, str):
            raise TypeError(
                "Supervision name must be a string."
            )

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Supervision name cannot be empty."
            )

        return self.supervision.get(
            normalized_name,
            default,
        )

    # -----------------------------------------------------------------

    def is_supervised(
        self,
        name: str,
    ) -> bool:
        """
        Return True only when the named supervision state is literally
        the boolean value True.

        Truthy values such as 1 or "true" are not interpreted as
        asserted supervision.
        """

        if not isinstance(name, str):
            raise TypeError(
                "Supervision name must be a string."
            )

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Supervision name cannot be empty."
            )

        return (
            self.supervision.get(
                normalized_name
            )
            is True
        )

    # =================================================================
    # METADATA
    # =================================================================

    def metadata_get(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Return optional execution metadata.
        """

        if not isinstance(name, str):
            raise TypeError(
                "Metadata name must be a string."
            )

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Metadata name cannot be empty."
            )

        return self.metadata.get(
            normalized_name,
            default,
        )

    # =================================================================
    # DERIVATION
    # =================================================================

    def with_time(
        self,
        time: float,
        *,
        timestep: float | None = None,
    ) -> ProtectionContext:
        """
        Return a new context at another evaluation time.

        The original context remains unchanged.

        If ``timestep`` is omitted, the existing timestep is retained.
        """

        return ProtectionContext(
            time=time,
            timestep=(
                self.timestep
                if timestep is None
                else timestep
            ),
            event_id=self.event_id,
            event_type=self.event_type,
            network_state=self.network_state,
            simulation_state=self.simulation_state,
            supervision=dict(
                self.supervision
            ),
            metadata=dict(
                self.metadata
            ),
        )

    # =================================================================
    # DIAGNOSTICS
    # =================================================================

    def diagnostics(self) -> dict[str, Any]:
        """
        Return a detached diagnostic representation.

        Authoritative referenced objects are represented by their
        identifiers where available.

        Referenced objects themselves are neither serialized nor
        copied.
        """

        return {
            "time": self.time,
            "timestep": self.timestep,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "network_state": (
                getattr(
                    self.network_state,
                    "id",
                    None,
                )
                if self.network_state is not None
                else None
            ),
            "simulation_state": (
                getattr(
                    self.simulation_state,
                    "id",
                    None,
                )
                if self.simulation_state is not None
                else None
            ),
            "supervision": dict(
                self.supervision
            ),
            "metadata": dict(
                self.metadata
            ),
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<ProtectionContext "
            f"time={self.time!r}, "
            f"timestep={self.timestep!r}, "
            f"event_id={self.event_id!r}, "
            f"event_type={self.event_type!r}>"
        )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "ProtectionContext",
]
