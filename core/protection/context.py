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

Architectural Position
----------------------

    MeasurementChannel
           |
       RelayInput
           |
    ProtectionElement
           |
      RelayBase
           |
    ProtectionContext
           |
           v
    ProtectionDecision

ProtectionContext carries evaluation-time information required by
protection-function execution.

It does NOT:

    * own network state;
    * own measurement state;
    * own relay state;
    * execute protection functions;
    * perform power-system calculations;
    * operate breakers;
    * modify topology;
    * schedule simulation events;
    * own simulation time;
    * contain GUI state;
    * perform persistence;
    * become a simulation-state container.

Authoritative ownership remains with the appropriate GridForge
subsystems.

Design Principles
-----------------

1. Protection functions receive execution-time information through an
   explicit context rather than through global state.

2. MeasurementChannel remains authoritative for measurement state.

3. RelayInput remains the protection-facing measurement binding.

4. Network objects remain authoritative for network state.

5. Simulation objects remain authoritative for simulation state.

6. ProtectionContext may reference authoritative objects but does not
   copy or own their state.

7. Simulation time is supplied by the caller. ProtectionContext does
   not own an independent clock.

8. Supervision information is carried explicitly and is not
   automatically interpreted by this class.

9. The context is immutable after construction.

10. Mapping fields are defensively copied and exposed through
    read-only MappingProxyType wrappers.

11. Mapping immutability is shallow. Values contained inside mappings
    remain owned by the caller/authoritative subsystem.

12. ProtectionContext contains no protection-function logic.

13. ProtectionContext does not convert measurement values or perform
    electrical calculations.

14. ProtectionContext may be freely constructed by simulation,
    protection orchestration, testing, or other execution layers.

Temporal Semantics
------------------

``time`` is the authoritative evaluation timestamp supplied by the
caller.

``timestep`` is the elapsed time since the previous evaluation when
known.

ProtectionContext does not advance time and does not maintain a clock.

Referenced State
----------------

``network_state`` and ``simulation_state`` are references only.

They are deliberately not copied, serialized, or interpreted by this
class.

The context therefore remains an execution-context object rather than
a second network or simulation state container.

Supervision
-----------

The ``supervision`` mapping carries explicit execution-time
information such as:

    blocking
    permissive
    interlock
    test_mode

ProtectionContext does not decide what these values mean.

For convenience, ``is_supervised()`` returns True only when the stored
value is literally ``True``.

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
# PROTECTION EXECUTION CONTEXT
# =====================================================================


@dataclass(frozen=True, slots=True)
class ProtectionContext:
    """
    Immutable execution context for one protection evaluation.

    Parameters
    ----------
    time:
        Current protection-evaluation time.

        The unit is defined by the simulation/execution environment.
        ProtectionContext does not impose a simulation-time unit and
        does not own a clock.

    timestep:
        Optional elapsed time since the previous protection
        evaluation.

    event_id:
        Optional event identifier associated with this evaluation.

    event_type:
        Optional event classification.

        Examples:

            FAULT
            SWITCHING
            DISTURBANCE
            RECOVERY
            SIMULATION_STEP

    network_state:
        Optional reference to authoritative network state.

        The object is referenced, not copied or owned.

    simulation_state:
        Optional reference to authoritative simulation state.

        The object is referenced, not copied or owned.

    supervision:
        Explicit supervision information supplied by the caller.

    metadata:
        Optional non-authoritative execution metadata.

    Notes
    -----
    The dataclass is frozen, preventing reassignment of context
    attributes.

    Mapping fields are additionally wrapped in MappingProxyType.

    This provides shallow mapping immutability:

        context.supervision["x"] = value

    is prohibited.

    However, mutable objects stored as mapping values are not copied or
    recursively frozen. Their ownership remains with the caller or
    authoritative subsystem.
    """

    # ==================================================================
    # TEMPORAL INFORMATION
    # ==================================================================

    time: float

    timestep: float | None = None

    # ==================================================================
    # EVENT INFORMATION
    # ==================================================================

    event_id: str | None = None
    event_type: str | None = None

    # ==================================================================
    # AUTHORITATIVE REFERENCES
    # ==================================================================

    network_state: Any = None
    simulation_state: Any = None

    # ==================================================================
    # EXECUTION INFORMATION
    # ==================================================================

    supervision: Mapping[str, Any] = field(
        default_factory=dict
    )

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    # ==================================================================
    # INITIALIZATION / VALIDATION
    # ==================================================================

    def __post_init__(self) -> None:
        """
        Validate and normalize the execution context.
        """

        # --------------------------------------------------------------
        # Evaluation time
        # --------------------------------------------------------------

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

        object.__setattr__(
            self,
            "time",
            time,
        )

        # --------------------------------------------------------------
        # Timestep
        # --------------------------------------------------------------

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

        # --------------------------------------------------------------
        # Event identifier
        # --------------------------------------------------------------

        if self.event_id is not None:

            if not isinstance(
                self.event_id,
                str,
            ):
                raise TypeError(
                    "ProtectionContext.event_id must be a string "
                    "or None."
                )

            event_id = self.event_id.strip()

            object.__setattr__(
                self,
                "event_id",
                event_id or None,
            )

        # --------------------------------------------------------------
        # Event type
        # --------------------------------------------------------------

        if self.event_type is not None:

            if not isinstance(
                self.event_type,
                str,
            ):
                raise TypeError(
                    "ProtectionContext.event_type must be a string "
                    "or None."
                )

            event_type = self.event_type.strip()

            object.__setattr__(
                self,
                "event_type",
                event_type or None,
            )

        # --------------------------------------------------------------
        # Supervision mapping
        # --------------------------------------------------------------

        if not isinstance(
            self.supervision,
            Mapping,
        ):
            raise TypeError(
                "ProtectionContext.supervision must be a mapping."
            )

        supervision = dict(
            self.supervision
        )

        object.__setattr__(
            self,
            "supervision",
            MappingProxyType(
                supervision
            ),
        )

        # --------------------------------------------------------------
        # Metadata mapping
        # --------------------------------------------------------------

        if not isinstance(
            self.metadata,
            Mapping,
        ):
            raise TypeError(
                "ProtectionContext.metadata must be a mapping."
            )

        metadata = dict(
            self.metadata
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                metadata
            ),
        )

    # ==================================================================
    # TEMPORAL ACCESS
    # ==================================================================

    @property
    def current_time(self) -> float:
        """
        Return the current protection-evaluation time.
        """

        return self.time

    # ------------------------------------------------------------------

    @property
    def elapsed_time(self) -> float | None:
        """
        Return the elapsed time since the previous evaluation.

        Returns None when no timestep was supplied.
        """

        return self.timestep

    # ------------------------------------------------------------------

    def measurement_time(self) -> float:
        """
        Return the time to use for time-dependent measurement-validity
        evaluation.

        ProtectionContext does not own measurement state.

        Example
        -------

            relay_input.is_valid(
                current_time=context.measurement_time()
            )
        """

        return self.time

    # ==================================================================
    # EVENT ACCESS
    # ==================================================================

    @property
    def has_event(self) -> bool:
        """
        Return True when an event identifier is present.
        """

        return self.event_id is not None

    # ------------------------------------------------------------------

    def is_event_type(
        self,
        event_type: str,
    ) -> bool:
        """
        Return True when the current event matches ``event_type``.

        Comparison is case-insensitive and ignores surrounding
        whitespace.
        """

        if not isinstance(
            event_type,
            str,
        ):
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

    # ==================================================================
    # SUPERVISION
    # ==================================================================

    def supervision_get(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Return explicitly supplied supervision information.

        This method does not interpret the value.
        """

        if not isinstance(
            name,
            str,
        ):
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

    # ------------------------------------------------------------------

    def is_supervised(
        self,
        name: str,
    ) -> bool:
        """
        Return True only when the named supervision state is explicitly
        the boolean value True.

        Truthy values such as 1 or non-empty strings are not
        automatically interpreted as asserted supervision.
        """

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Supervision name must be a string."
            )

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "Supervision name cannot be empty."
            )

        return (
            self.supervision.get(normalized_name)
            is True
        )

    # ==================================================================
    # METADATA
    # ==================================================================

    def metadata_get(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Return optional execution metadata.
        """

        if not isinstance(
            name,
            str,
        ):
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

    # ==================================================================
    # DERIVATION
    # ==================================================================

    def with_time(
        self,
        time: float,
        *,
        timestep: float | None = None,
    ) -> ProtectionContext:
        """
        Return a new context at another evaluation time.

        The original context remains unchanged.

        Parameters
        ----------
        time:
            New evaluation time.

        timestep:
            New elapsed timestep.

            If omitted, the existing timestep is retained.
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

    # ==================================================================
    # DIAGNOSTICS
    # ==================================================================

    def diagnostics(self) -> dict[str, Any]:
        """
        Return a detached diagnostic representation.

        Referenced authoritative objects are represented by their
        identifiers where available.

        This method does not serialize or copy referenced objects.
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

    # ==================================================================
    # REPRESENTATION
    # ==================================================================

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


# ======================================================================
# PUBLIC API
# ======================================================================

__all__ = [
    "ProtectionContext",
]
