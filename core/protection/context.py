"""
GridForge V2 Protection Execution Context.

File
----
core/protection/context.py

Purpose
-------
Defines the execution context supplied to protection functions during
evaluation.

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

ProtectionContext provides evaluation-time information.

It does NOT:

    * own network state
    * own measurement state
    * own relay state
    * operate breakers
    * execute protection functions
    * perform power-system calculations
    * contain GUI state
    * perform persistence
    * become a simulation state container

The authoritative state remains in the appropriate GridForge
subsystems.

Design Principles
-----------------

1. Protection functions must not depend directly on a GUI or solver.

2. Protection functions should receive evaluation-time information
   through an explicit context.

3. The protection context must remain lightweight.

4. Simulation time is supplied by the caller. The context does not
   own a clock.

5. Measurement channels remain authoritative for measurement state.

6. Network/topology objects remain authoritative for network state.

7. Relay/model objects remain authoritative for equipment state.

8. ProtectionContext may carry references to authoritative objects,
   but must not duplicate their state.

9. Optional context data must be explicit rather than hidden global
   state.

10. The context must be suitable for:
       * steady-state protection evaluation
       * time-domain protection evaluation
       * event-driven evaluation
       * relay coordination
       * future real-time execution

Execution Model
---------------

A typical evaluation is:

    context = ProtectionContext(
        time=simulation_time,
        timestep=simulation_timestep,
    )

    decision = protection_function.evaluate(context)

The function obtains its measurements through RelayInput:

    RelayBase
        |
        +-- RelayInput
                |
                +-- MeasurementChannel

ProtectionContext provides the temporal/execution information needed
to interpret those measurements.

It does not replace RelayInput or MeasurementChannel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
        GridForge protection does not assume seconds internally at
        this layer.

    timestep:
        Optional elapsed execution interval since the previous
        evaluation.

    event_id:
        Optional identifier for the event being evaluated.

    event_type:
        Optional event classification.

        Examples:

            "FAULT"
            "SWITCHING"
            "DISTURBANCE"
            "RECOVERY"
            "SIMULATION_STEP"

    network_state:
        Optional authoritative network-state reference.

        This is a reference only. ProtectionContext does not copy or
        mutate network state.

    simulation_state:
        Optional authoritative simulation-state reference.

        This is a reference only.

    supervision:
        Optional protection-supervision information.

        Examples:

            blocking
            permissive
            interlock
            test_mode

        Protection functions should interpret this data explicitly;
        it is not automatically applied by the context.

    metadata:
        Optional execution metadata.

    Notes
    -----
    The context is frozen so that a protection function cannot
    accidentally mutate execution state belonging to the caller.
    """

    time: float

    timestep: float | None = None

    event_id: str | None = None
    event_type: str | None = None

    network_state: Any = None
    simulation_state: Any = None

    supervision: Mapping[str, Any] = field(
        default_factory=dict
    )

    metadata: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """
        Validate and normalize the execution context.
        """

        time = float(self.time)

        if time != time or time in (
            float("inf"),
            float("-inf"),
        ):
            raise ValueError(
                "ProtectionContext.time must be finite."
            )

        object.__setattr__(
            self,
            "time",
            time,
        )

        if self.timestep is not None:

            timestep = float(
                self.timestep
            )

            if (
                timestep != timestep
                or timestep in (
                    float("inf"),
                    float("-inf"),
                )
            ):
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

        if self.event_id is not None:

            event_id = str(
                self.event_id
            ).strip()

            if not event_id:
                event_id = None

            object.__setattr__(
                self,
                "event_id",
                event_id,
            )

        if self.event_type is not None:

            event_type = str(
                self.event_type
            ).strip()

            if not event_type:
                event_type = None

            object.__setattr__(
                self,
                "event_type",
                event_type,
            )

        object.__setattr__(
            self,
            "supervision",
            MappingProxyType(
                dict(self.supervision or {})
            ),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata or {})
            ),
        )

    # ==================================================================
    # TEMPORAL INFORMATION
    # ==================================================================

    @property
    def current_time(self) -> float:
        """
        Return the current protection-evaluation time.

        ``current_time`` is the preferred semantic property when
        passing the context time to MeasurementChannel validity checks.
        """
        return self.time

    # ------------------------------------------------------------------

    @property
    def elapsed_time(self) -> float | None:
        """
        Return the elapsed time since the previous evaluation.
        """
        return self.timestep

    # ==================================================================
    # EVENT INFORMATION
    # ==================================================================

    @property
    def has_event(self) -> bool:
        """
        Return whether the context identifies an event.
        """
        return self.event_id is not None

    # ------------------------------------------------------------------

    def is_event_type(
        self,
        event_type: str,
    ) -> bool:
        """
        Test the current event type.

        Comparison is case-insensitive.
        """

        if self.event_type is None:
            return False

        return (
            self.event_type.upper()
            == str(event_type).strip().upper()
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
        Return a supervision value.

        The context does not interpret the value.
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
        Return a boolean supervision state.

        Only an explicit boolean ``True`` is considered asserted.
        """
        return (
            self.supervision.get(name)
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
        return self.metadata.get(
            name,
            default,
        )

    # ==================================================================
    # MEASUREMENT VALIDITY SUPPORT
    # ==================================================================

    def measurement_time(self) -> float:
        """
        Return the time that should be supplied to a
        MeasurementChannel when evaluating time-dependent validity.

        Example
        -------

            input.validity(
                current_time=context.measurement_time()
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
        Create a new context at another evaluation time.

        The original context remains unchanged.
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
        Return diagnostic information about the execution context.

        Object references are represented by identity information where
        possible rather than serializing authoritative objects.
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
