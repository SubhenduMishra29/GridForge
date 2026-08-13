"""
GridForge V2 Protection Execution Context.

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
      Protection Function
           |
    ProtectionContext
           |
           v
    ProtectionDecision

ProtectionContext carries evaluation-time information.

It does NOT:

    * own network state;
    * own measurement state;
    * own relay state;
    * execute protection functions;
    * perform power-system calculations;
    * operate breakers;
    * modify topology;
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

4. Network and simulation objects remain authoritative for their own
   state.

5. ProtectionContext may reference authoritative objects but must not
   duplicate their state.

6. Simulation time is supplied by the caller. ProtectionContext does
   not own a clock.

7. Supervision information is carried explicitly and is not
   automatically interpreted by this class.

8. The context is immutable after construction.

9. The context is lightweight enough for:
       * steady-state evaluation;
       * time-domain evaluation;
       * event-driven evaluation;
       * relay coordination;
       * future real-time execution.

Typical Usage
-------------

    context = ProtectionContext(
        time=simulation_time,
        timestep=simulation_timestep,
        event_id="FAULT_001",
        event_type="FAULT",
    )

    decision = protection_function.evaluate(context)

Measurement access remains through RelayInput:

    RelayBase
        |
        +-- RelayInput
                |
                +-- MeasurementChannel

ProtectionContext therefore complements RelayInput; it does not
replace it.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ProtectionContext:
    """
    Immutable execution context for one protection evaluation.

    Parameters
    ----------
    time:
        Current protection-evaluation time.

        The unit is defined by the caller/execution environment.
        This layer does not impose a simulation-time unit.

    timestep:
        Optional elapsed time since the previous protection
        evaluation.

    event_id:
        Optional identifier of the event associated with this
        evaluation.

    event_type:
        Optional event classification.

        Examples:

            "FAULT"
            "SWITCHING"
            "DISTURBANCE"
            "RECOVERY"
            "SIMULATION_STEP"

    network_state:
        Optional reference to authoritative network state.

        This object is referenced, not copied or owned.

    simulation_state:
        Optional reference to authoritative simulation state.

        This object is referenced, not copied or owned.

    supervision:
        Optional explicit supervision information.

        Examples:

            blocking
            permissive
            interlock
            test_mode

        ProtectionContext does not automatically apply these states.

    metadata:
        Optional non-authoritative execution metadata.

    Notes
    -----
    The dataclass is frozen so the context itself cannot be mutated
    after construction.

    The mapping fields are additionally wrapped in
    MappingProxyType so their contents cannot be modified through the
    context.
    """

    time: float

    timestep: float | None = None

    event_id: str | None = None
    event_type: str | None = None

    network_state: Any = None
    simulation_state: Any = None

    supervision: Mapping[str, Any] = field(
        default_factory=dict,
    )

    metadata: Mapping[str, Any] = field(
        default_factory=dict,
    )

    # ==================================================================
    # INITIALIZATION / VALIDATION
    # ==================================================================

    def __post_init__(self) -> None:
        """
        Normalize immutable/public values and validate the context.
        """

        # --------------------------------------------------------------
        # Evaluation time
        # --------------------------------------------------------------

        try:
            time = float(self.time)
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "ProtectionContext.time must be a real numeric value."
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
                    "ProtectionContext.timestep must be a real "
                    "numeric value or None."
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
        # Event identity
        # --------------------------------------------------------------

        if self.event_id is not None:

            event_id = str(
                self.event_id
            ).strip()

            object.__setattr__(
                self,
                "event_id",
                event_id or None,
            )

        # --------------------------------------------------------------
        # Event type
        # --------------------------------------------------------------

        if self.event_type is not None:

            event_type = str(
                self.event_type
            ).strip()

            object.__setattr__(
                self,
                "event_type",
                event_type or None,
            )

        # --------------------------------------------------------------
        # Immutable mappings
        # --------------------------------------------------------------

        try:
            supervision = dict(
                self.supervision or {}
            )
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "ProtectionContext.supervision must be a mapping."
            ) from exc

        try:
            metadata = dict(
                self.metadata or {}
            )
        except (TypeError, ValueError) as exc:
            raise TypeError(
                "ProtectionContext.metadata must be a mapping."
            ) from exc

        object.__setattr__(
            self,
            "supervision",
            MappingProxyType(
                supervision
            ),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                metadata
            ),
        )

    # ==================================================================
    # TEMPORAL INFORMATION
    # ==================================================================

    @property
    def current_time(self) -> float:
        """
        Return the current protection-evaluation time.

        This is the preferred semantic property when passing the
        context time to time-dependent measurement-validity checks.
        """

        return self.time

    # ------------------------------------------------------------------

    @property
    def elapsed_time(self) -> float | None:
        """
        Return the elapsed time since the previous evaluation.

        Returns None when the caller did not provide a timestep.
        """

        return self.timestep

    # ==================================================================
    # EVENT INFORMATION
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

        return (
            self.event_type.casefold()
            == event_type.strip().casefold()
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
        Return an explicitly supplied supervision value.

        ProtectionContext does not interpret the value.
        """

        return self.supervision.get(
            name,
            default,
        )

    # ------------------------------------------------------------------

    def is_supervised(
        self,
        name: str,
    ) -> bool:
        """
        Return whether the named supervision state is explicitly True.

        Only the boolean value ``True`` is treated as asserted.

        Truthy values such as ``1`` or non-empty strings are not
        automatically interpreted as active supervision.
        """

        return self.supervision.get(name) is True

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

        return self.metadata.get(
            name,
            default,
        )

    # ==================================================================
    # MEASUREMENT VALIDITY SUPPORT
    # ==================================================================

    def measurement_time(self) -> float:
        """
        Return the authoritative time to use when evaluating
        time-dependent MeasurementChannel validity.

        Example
        -------

            input.validity(
                current_time=context.measurement_time(),
            )
        """

        return self.time

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
        Return a diagnostic representation of this context.

        Authoritative referenced objects are represented by their
        identifiers where available rather than being serialized.

        This is intended for diagnostics and testing, not persistence.
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


__all__ = [
    "ProtectionContext",
]
