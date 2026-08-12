```python
"""
GridForge Protection Relay Function Base
========================================

File:
    core/protection/relay_base.py

Purpose
-------
Defines the common execution contract for GridForge V2 protection
function/element plugins.

Architectural Position
----------------------

    Physical Power System
            |
        CT / PT / CVT
            |
    MeasurementChannel
            |
        RelayInput
            |
    authoritative Relay
            |
       RelayBase
            |
    Protection Function
            |
    ProtectionSystem
            |
      BreakerManager
            |
          Breaker


Important V2 Architectural Principle
-------------------------------------

A physical/numerical Relay may contain MULTIPLE protection
functions.

Therefore:

    Relay != ProtectionFunction

For example, one authoritative Relay may contain:

    50/51   Overcurrent
    50N/51N Earth Fault
    67      Directional Overcurrent
    21      Distance
    27      Undervoltage
    59      Overvoltage
    81      Frequency

Each protection function is represented by a separate execution
object derived from RelayBase.

All such functions may reference the same authoritative Relay and
shared measurement architecture.

RelayBase is therefore a protection-FUNCTION contract.

It is NOT a second Relay model.

Authority
---------

core/model/relay.py
    Authoritative physical/device-level Relay identity,
    configuration and protection state.

core/model/measurement_channel.py
    Authoritative measurement-channel state.

RelayInput
    Existing input-path object connecting measurement channels to
    protection functions.

core/protection/relay_base.py
    Common protection-function execution contract.

core/protection/<function>.py
    Concrete protection algorithms.

core/protection/protection_system.py
    Protection orchestration and decision aggregation.

core/protection/breaker_manager.py
    Breaker command boundary.

Responsibilities
----------------
RelayBase provides:

- authoritative Relay access;
- protection-function identity;
- function metadata;
- access to configured RelayInput references;
- signal access through RelayInput;
- service-state handling;
- enable/block supervision hooks;
- pickup state handling;
- operate state handling;
- protection trip-decision handling;
- reset handling;
- structured function status;
- a stable plugin interface;
- compatibility with ProtectionDecision;
- a common evaluation boundary.

RelayBase does NOT:

- create Relay objects;
- create CT/PT/CVT objects;
- create MeasurementChannel objects;
- create RelayInput objects implicitly;
- duplicate measurement values;
- calculate system-wide electrical quantities;
- build Y-bus;
- perform load flow;
- perform short-circuit analysis;
- coordinate multiple protection functions;
- operate breakers;
- modify network topology;
- schedule simulation events;
- own ProtectionSystem state.

Multi-Function Relay Principle
------------------------------

Multiple protection functions may reference the same Relay:

    Relay
      |
      +---- OvercurrentFunction
      |
      +---- EarthFaultFunction
      |
      +---- DirectionalFunction
      |
      +---- DistanceFunction
      |
      +---- VoltageFunction
      |
      +---- FrequencyFunction

The function objects must not copy the Relay's authoritative
configuration or device state.

Algorithm-specific state is permitted.

Examples:

- inverse-time accumulation;
- distance-zone state;
- directional polarization state;
- differential restraint state;
- frequency filtering state;
- definite-time pickup timer;
- dropout timer;
- element latch state.

Such state belongs to the protection-function execution layer.

Decision Ownership
------------------

RelayBase may communicate protection operating state to the
authoritative Relay where the Relay model exposes the corresponding
API.

It never operates a physical breaker.

The command path remains:

    Protection Function
            |
            v
    ProtectionSystem
            |
       TripRequest
            |
            v
      BreakerManager
            |
            v
          Breaker

Timing
------

RelayBase deliberately does not impose a particular operating-time
model.

A protection function may be:

- instantaneous;
- definite-time;
- inverse-time;
- multi-stage;
- zone-based;
- accumulated;
- state-machine based;
- supervised;
- blocked;
- latched.

Concrete functions own their algorithmic timing state.

ProtectionSystem owns orchestration.

Simulation/event scheduling belongs outside this class.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class RelayBase(ABC):
    """
    Common base class for GridForge V2 protection-function plugins.

    A RelayBase instance represents ONE protection function/element.

    It references an authoritative Relay model but does not represent
    the complete physical relay device.

    Multiple RelayBase-derived objects may therefore reference the
    same authoritative Relay.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        relay: Any,
        relay_inputs: Mapping[str, Any] | None = None,
        *,
        function_id: str | None = None,
        function_name: str | None = None,
        enabled: bool = True,
    ) -> None:
        """
        Create a protection-function execution object.

        Parameters
        ----------
        relay:
            Authoritative core.model.relay.Relay instance.

        relay_inputs:
            Existing RelayInput references.

        function_id:
            Unique identifier for this protection-function instance.

            This MUST be distinct from relay.id when multiple
            functions are attached to the same Relay.

        function_name:
            Human-readable/canonical function identifier.

        enabled:
            Protection-function execution enable state.

        Notes
        -----
        No measurement objects are created here.
        """

        if relay is None:
            raise ValueError(
                "relay cannot be None."
            )

        self.relay = relay

        # -------------------------------------------------------------
        # Function identity
        # -------------------------------------------------------------

        if function_id is None:
            function_id = self._default_function_id()

        self._function_id = self._validate_identifier(
            function_id,
            "function_id",
        )

        if function_name is None:
            function_name = self.__class__.__name__

        self._function_name = self._validate_identifier(
            function_name,
            "function_name",
        )

        # -------------------------------------------------------------
        # Execution state
        #
        # These are function-layer states, NOT copies of measurement
        # or Relay configuration.
        # -------------------------------------------------------------

        self._enabled = bool(enabled)
        self._blocked = False

        self._relay_inputs: dict[str, Any] = {}

        if relay_inputs is not None:
            self._set_relay_inputs(
                relay_inputs
            )

    # =================================================================
    # IDENTITY
    # =================================================================

    @staticmethod
    def _validate_identifier(
        value: Any,
        name: str,
    ) -> str:
        """
        Validate a protection-function identifier.
        """

        if not isinstance(value, str):
            raise TypeError(
                f"{name} must be a string."
            )

        value = value.strip()

        if not value:
            raise ValueError(
                f"{name} cannot be empty."
            )

        return value

    # -----------------------------------------------------------------

    def _default_function_id(self) -> str:
        """
        Generate a deterministic default function identifier.

        Concrete implementations are encouraged to supply an
        explicit function_id when multiple instances of the same
        function type may exist on one Relay.
        """

        return (
            f"{self.relay.id}:"
            f"{self.__class__.__name__}"
        )

    # -----------------------------------------------------------------

    @property
    def id(self) -> str:
        """
        Return the protection-function instance identifier.
        """

        return self._function_id

    # -----------------------------------------------------------------

    @property
    def function_id(self) -> str:
        """
        Alias for the protection-function instance identifier.
        """

        return self._function_id

    # -----------------------------------------------------------------

    @property
    def function_name(self) -> str:
        """
        Return the protection-function type/name.

        Examples:

            overcurrent
            directional_overcurrent
            distance
            differential
            undervoltage
            frequency
        """

        return self._function_name

    # -----------------------------------------------------------------

    @property
    def relay_id(self) -> Any:
        """
        Return the authoritative Relay identifier.
        """

        return self.relay.id

    # -----------------------------------------------------------------

    @property
    def name(self) -> str:
        """
        Return the authoritative Relay name.
        """

        return self.relay.name

    # -----------------------------------------------------------------

    @property
    def relay_type(self) -> str:
        """
        Return the authoritative Relay type.
        """

        return self.relay.type

    # -----------------------------------------------------------------

    @property
    def relay_model(self) -> Any:
        """
        Return the authoritative Relay model.

        No copy is created.
        """

        return self.relay

    # =================================================================
    # SERVICE STATE
    # =================================================================

    @property
    def in_service(self) -> bool:
        """
        Return the authoritative Relay service state.
        """

        return bool(
            getattr(
                self.relay,
                "in_service",
                True,
            )
        )

    # -----------------------------------------------------------------

    @property
    def enabled(self) -> bool:
        """
        Return whether this protection function is enabled.

        This is function-level execution state.
        """

        return self._enabled

    # -----------------------------------------------------------------

    def set_enabled(
        self,
        state: bool,
    ) -> None:
        """
        Enable or disable this protection function.
        """

        self._enabled = bool(state)

        if not self._enabled:
            self.set_pickup(False)
            self.set_operated(False)
            self.reset_trip()

    # -----------------------------------------------------------------

    @property
    def blocked(self) -> bool:
        """
        Return whether this protection function is blocked.

        Blocking is intentionally distinct from Relay service state.

        Examples include:

        - scheme blocking;
        - maintenance blocking;
        - directional supervision;
        - breaker-status supervision;
        - external interlock.
        """

        return self._blocked

    # -----------------------------------------------------------------

    def set_blocked(
        self,
        state: bool,
    ) -> None:
        """
        Set function-level blocking state.
        """

        self._blocked = bool(state)

        if self._blocked:
            self.set_pickup(False)
            self.set_operated(False)
            self.reset_trip()

    # -----------------------------------------------------------------

    def is_available(self) -> bool:
        """
        Return whether the function may currently operate.

        Concrete functions may override this to add supervision.

        The default condition is:

            Relay in service
            AND function enabled
            AND function not blocked
        """

        return (
            self.in_service
            and self.enabled
            and not self.blocked
        )

    # =================================================================
    # INPUT ARCHITECTURE
    # =================================================================

    def _set_relay_inputs(
        self,
        relay_inputs: Mapping[str, Any],
    ) -> None:
        """
        Register existing RelayInput references.

        No measurement object is created or modified.
        """

        if not isinstance(
            relay_inputs,
            Mapping,
        ):
            raise TypeError(
                "relay_inputs must be a mapping."
            )

        for name, relay_input in relay_inputs.items():

            if not isinstance(name, str):
                raise TypeError(
                    "Relay input names must be strings."
                )

            name = name.strip()

            if not name:
                raise ValueError(
                    "Relay input name cannot be empty."
                )

            if relay_input is None:
                raise ValueError(
                    f"Relay input '{name}' cannot be None."
                )

            self._relay_inputs[name] = relay_input

    # -----------------------------------------------------------------

    @property
    def relay_inputs(self) -> Mapping[str, Any]:
        """
        Return a shallow read-only view of configured input references.
        """

        return dict(
            self._relay_inputs
        )

    # -----------------------------------------------------------------

    def add_input(
        self,
        name: str,
        relay_input: Any,
    ) -> None:
        """
        Add an existing RelayInput reference.

        This method does not create the RelayInput.
        """

        if not isinstance(name, str):
            raise TypeError(
                "Relay input name must be a string."
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "Relay input name cannot be empty."
            )

        if relay_input is None:
            raise ValueError(
                f"Relay input '{name}' cannot be None."
            )

        if name in self._relay_inputs:
            raise ValueError(
                f"Relay input '{name}' is already configured "
                f"for function '{self.id}'."
            )

        self._relay_inputs[name] = relay_input

    # -----------------------------------------------------------------

    def remove_input(
        self,
        name: str,
    ) -> None:
        """
        Remove an input reference.

        The underlying RelayInput and measurement channel are not
        modified.
        """

        self._relay_inputs.pop(
            name,
            None,
        )

    # -----------------------------------------------------------------

    def get_input(
        self,
        name: str,
    ) -> Any:
        """
        Return a configured RelayInput.
        """

        try:
            return self._relay_inputs[name]
        except KeyError as exc:
            raise KeyError(
                f"Relay input '{name}' is not configured "
                f"for protection function '{self.id}'."
            ) from exc

    # -----------------------------------------------------------------

    def has_input(
        self,
        name: str,
    ) -> bool:
        """
        Return True when the named RelayInput exists.
        """

        return name in self._relay_inputs

    # -----------------------------------------------------------------

    def require_inputs(
        self,
        *names: str,
    ) -> None:
        """
        Require specific RelayInputs.

        Concrete protection functions should call this when their
        input requirements are structurally mandatory.
        """

        missing = [
            name
            for name in names
            if name not in self._relay_inputs
        ]

        if missing:
            raise ValueError(
                f"Protection function '{self.id}' on Relay "
                f"'{self.relay_id}' is missing required "
                f"RelayInput(s): {missing}"
            )

    # =================================================================
    # SIGNAL ACCESS
    # =================================================================

    def input_signal(
        self,
        name: str,
    ) -> Any:
        """
        Return the current signal exposed by a RelayInput.

        The signal is never cached by RelayBase.
        """

        relay_input = self.get_input(
            name
        )

        signal = getattr(
            relay_input,
            "signal",
            None,
        )

        if callable(signal):
            return signal()

        if signal is not None:
            return signal

        value = getattr(
            relay_input,
            "value",
            None,
        )

        if callable(value):
            return value()

        if value is not None:
            return value

        raise AttributeError(
            f"RelayInput '{name}' does not expose a supported "
            "signal or value interface."
        )

    # =================================================================
    # PROTECTION STATE
    # =================================================================

    @property
    def picked_up(self) -> bool:
        """
        Return authoritative Relay pickup state when available.

        RelayBase does not maintain a duplicate pickup state.
        """

        return bool(
            getattr(
                self.relay,
                "picked_up",
                False,
            )
        )

    # -----------------------------------------------------------------

    @property
    def operated(self) -> bool:
        """
        Return authoritative Relay operated state when available.
        """

        operated = getattr(
            self.relay,
            "operated",
            None,
        )

        if operated is not None:
            return bool(operated)

        return self.picked_up

    # -----------------------------------------------------------------

    @property
    def tripped(self) -> bool:
        """
        Return authoritative Relay protection-trip state.
        """

        return bool(
            getattr(
                self.relay,
                "trip",
                False,
            )
        )

    # =================================================================
    # DECISION CONTROL
    # =================================================================

    def set_pickup(
        self,
        state: bool,
    ) -> bool:
        """
        Set authoritative Relay pickup state when supported.
        """

        state = bool(state)

        setter = getattr(
            self.relay,
            "set_pickup_state",
            None,
        )

        if callable(setter):
            setter(state)

        return state

    # -----------------------------------------------------------------

    def set_operated(
        self,
        state: bool,
    ) -> bool:
        """
        Set authoritative Relay operated state when supported.
        """

        state = bool(state)

        setter = getattr(
            self.relay,
            "set_operated",
            None,
        )

        if callable(setter):
            setter(state)

        return state

    # -----------------------------------------------------------------

    def trip(self) -> bool:
        """
        Assert the authoritative Relay protection-trip state.

        This is a protection decision only.

        It does NOT operate a physical breaker.
        """

        if not self.is_available():
            self.reset_trip()
            return False

        setter = getattr(
            self.relay,
            "set_trip",
            None,
        )

        if not callable(setter):
            raise AttributeError(
                "Authoritative Relay does not provide "
                "set_trip()."
            )

        setter(True)

        return self.tripped

    # -----------------------------------------------------------------

    def reset_trip(self) -> None:
        """
        Clear the authoritative Relay protection-trip state.
        """

        setter = getattr(
            self.relay,
            "set_trip",
            None,
        )

        if callable(setter):
            setter(False)

    # =================================================================
    # SUPERVISION
    # =================================================================

    def check_supervision(self) -> bool:
        """
        Return whether the function's supervision conditions permit
        operation.

        Concrete functions may override this.

        Examples:

        - VT supervision;
        - CT supervision;
        - directional supervision;
        - breaker status supervision;
        - communication supervision.
        """

        return True

    # -----------------------------------------------------------------

    def can_operate(self) -> bool:
        """
        Return the complete common operation permission.

        This method intentionally separates availability from the
        protection pickup algorithm.
        """

        return (
            self.is_available()
            and self.check_supervision()
        )

    # =================================================================
    # EVALUATION
    # =================================================================

    @abstractmethod
    def check_pickup(self) -> bool:
        """
        Evaluate the protection function's pickup criterion.

        Concrete functions must obtain electrical quantities through
        their configured input architecture.

        They must not assume measurements are stored directly on the
        protection function.

        Examples:

            Overcurrent:
                current input

            Distance:
                voltage/current inputs

            Directional:
                current/voltage polarization inputs

            Differential:
                multiple terminal current inputs

            Frequency:
                frequency measurement input
        """

        raise NotImplementedError

    # -----------------------------------------------------------------

    def evaluate(
        self,
    ) -> bool:
        """
        Execute one common protection-function evaluation cycle.

        The method intentionally represents a protection element
        decision, not a complete breaker-operation sequence.

        Sequence
        --------

            availability
                  |
                  v
            supervision
                  |
                  v
            check_pickup()
                  |
                  v
            authoritative Relay state
                  |
                  v
            protection trip decision

        Timing and delayed operation belong to concrete functions or
        higher-level protection/simulation infrastructure.
        """

        if not self.can_operate():

            self.set_pickup(False)
            self.set_operated(False)
            self.reset_trip()

            return False

        operates = bool(
            self.check_pickup()
        )

        self.set_pickup(
            operates
        )

        self.set_operated(
            operates
        )

        if operates:
            self.trip()
        else:
            self.reset_trip()

        return operates

    # =================================================================
    # RESET
    # =================================================================

    def reset(self) -> None:
        """
        Reset common protection-function state.

        Subclasses may override this to clear genuine algorithmic
        state such as timers, filters, accumulators, latches, or
        zone state.

        Subclasses should call super().reset().
        """

        self._blocked = False

        reset_state = getattr(
            self.relay,
            "reset_protection_state",
            None,
        )

        if callable(reset_state):
            reset_state()
            return

        self.reset_trip()

        pickup_setter = getattr(
            self.relay,
            "set_pickup_state",
            None,
        )

        if callable(pickup_setter):
            pickup_setter(False)

        operated_setter = getattr(
            self.relay,
            "set_operated",
            None,
        )

        if callable(operated_setter):
            operated_setter(False)

    # =================================================================
    # STATUS
    # =================================================================

    def status(self) -> dict[str, Any]:
        """
        Return structured protection-function diagnostics.

        Authoritative Relay state is read rather than duplicated.

        Input diagnostic information is delegated to RelayInput.
        """

        return {
            "function_id": self.function_id,
            "function_name": self.function_name,
            "relay_id": self.relay_id,
            "relay_name": self.name,
            "relay_type": self.relay_type,
            "in_service": self.in_service,
            "enabled": self.enabled,
            "blocked": self.blocked,
            "available": self.is_available(),
            "supervised": self.check_supervision(),
            "picked_up": self.picked_up,
            "operated": self.operated,
            "trip": self.tripped,
            "inputs": {
                name: self._input_status(
                    relay_input
                )
                for name, relay_input
                in self._relay_inputs.items()
            },
        }

    # -----------------------------------------------------------------

    @staticmethod
    def _input_status(
        relay_input: Any,
    ) -> Any:
        """
        Obtain diagnostic information from a RelayInput without
        imposing a concrete RelayInput implementation.
        """

        status = getattr(
            relay_input,
            "status",
            None,
        )

        if callable(status):
            return status()

        if status is not None:
            return status

        summary = getattr(
            relay_input,
            "summary",
            None,
        )

        if callable(summary):
            return summary()

        if summary is not None:
            return summary

        return {
            "id": getattr(
                relay_input,
                "id",
                None,
            ),
            "type": type(
                relay_input
            ).__name__,
        }

    # =================================================================
    # METADATA
    # =================================================================

    def metadata(self) -> dict[str, Any]:
        """
        Return protection-function metadata.

        Concrete functions may override this to expose function
        characteristics without exposing algorithm internals.
        """

        return {
            "function_id": self.function_id,
            "function_name": self.function_name,
            "relay_id": self.relay_id,
            "relay_type": self.relay_type,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<{self.__class__.__name__} "
            f"function_id={self.function_id!r}, "
            f"relay_id={self.relay_id!r}, "
            f"enabled={self.enabled}, "
            f"blocked={self.blocked}>"
        )


__all__ = [
    "RelayBase",
]
```
