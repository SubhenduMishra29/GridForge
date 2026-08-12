"""
GridForge Protection Element
============================

File:
    core/protection/protection_element.py

Purpose
-------
Defines the common container/identity abstraction for an individual
protection function operating as part of an authoritative Relay.

Architectural Position
----------------------

    Physical Relay
          |
          v
    model.Relay
          |
          +-----------------------------+
          |                             |
          v                             v
    ProtectionElement              ProtectionElement
          |                             |
          v                             v
    Overcurrent                  Distance / Directional
    Function                     Function
          |                             |
          +-------------+---------------+
                        |
                        v
                ProtectionSystem
                        |
                        v
                  BreakerManager

A single physical Relay may contain multiple protection elements.

Example
-------

    Relay R1
        |
        +-- 50/51 Overcurrent
        +-- 67 Directional Overcurrent
        +-- 21 Distance
        +-- 27 Undervoltage
        +-- 59 Overvoltage
        +-- 81 Frequency
        +-- 50BF Breaker Failure

Architectural Principle
-----------------------

Relay
    = authoritative physical/configuration/state object.

ProtectionElement
    = identity, lifecycle, enablement and execution metadata for
      one protection function.

RelayBase
    = common execution interface for protection-function plugins.

Concrete Protection Function
    = actual electrical protection algorithm.

ProtectionSystem
    = system-level orchestration.

BreakerManager
    = physical breaker operation.

ProtectionElement is NOT a second Relay model.

Responsibilities
----------------
ProtectionElement provides:

- protection-element identity;
- reference to the authoritative Relay;
- reference to the protection-function implementation;
- function type;
- enable/disable state;
- priority;
- service state;
- evaluation lifecycle;
- protection decision state;
- diagnostic/status information;
- stable composition boundary for multifunction relays.

ProtectionElement does NOT:

- duplicate Relay identity;
- duplicate Relay configuration;
- create measurement channels;
- create CT/PT/CVT equipment;
- perform protection mathematics itself;
- calculate fault quantities;
- coordinate multiple relays;
- operate breakers;
- build network topology;
- own global protection-system state.

Multifunction Relay Principle
-----------------------------

A physical Relay may expose many protection elements.

Therefore GridForge does NOT assume:

    one Relay = one protection function

Instead:

    one Relay = one authoritative device
    one Relay = zero or more ProtectionElements

Each ProtectionElement may consume a different set of
RelayInput / MeasurementChannel objects through its associated
protection-function implementation.

Example:

    Relay R1
        |
        +-- OC51
        |     |
        |     +-- IA
        |     +-- IB
        |     +-- IC
        |
        +-- DIR67
        |     |
        |     +-- IA
        |     +-- VA
        |
        +-- DIST21
              |
              +-- VA
              +-- IA

The measurement architecture remains authoritative.

ProtectionElement does not create or duplicate those signals.

Execution Boundary
-------------------

The intended execution chain is:

    MeasurementChannel
            |
            v
       RelayInput
            |
            v
    Protection Function
            |
            v
    ProtectionElement
            |
            v
    ProtectionSystem
            |
            v
     BreakerManager

A ProtectionElement may execute its function, but it does not
directly operate a breaker.

Decision Ownership
------------------

The protection-function implementation may update the authoritative
Relay protection state through RelayBase.

ProtectionElement records only the execution/element-level result
needed for orchestration and diagnostics.

It must not become a duplicate Relay state machine.

Compatibility
-------------

This module intentionally uses a structural interface rather than
requiring concrete RelayBase imports.

That keeps the composition layer independent of individual
protection-function implementations and reduces circular-import risk.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping


# =====================================================================
# PROTECTION ELEMENT STATE
# =====================================================================


class ProtectionElementState(Enum):
    """
    Lifecycle/execution state of a protection element.
    """

    DISABLED = "DISABLED"
    IDLE = "IDLE"
    PICKUP = "PICKUP"
    OPERATED = "OPERATED"
    TRIPPED = "TRIPPED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


# =====================================================================
# PROTECTION ELEMENT
# =====================================================================


class ProtectionElement:
    """
    Composition object representing one protection function of a Relay.

    Parameters
    ----------
    id:
        Unique protection-element identifier.

    relay:
        Authoritative ``core.model.relay.Relay`` instance.

    function:
        Protection-function implementation.

        Typically a subclass of ``RelayBase``.

    function_type:
        Canonical protection-function classification.

        Examples:

            OVERCURRENT
            DIRECTIONAL
            DISTANCE
            DIFFERENTIAL
            VOLTAGE
            FREQUENCY
            POWER
            BREAKER_FAILURE

    name:
        Human-readable element name.

    enabled:
        Whether the protection element is enabled.

    priority:
        Optional execution/orchestration priority.

    metadata:
        Optional element-specific metadata.

    Notes
    -----
    The Relay remains authoritative for physical relay identity,
    configuration and relay-level operating state.

    ProtectionElement provides composition and execution identity
    for one function hosted by that Relay.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(
        self,
        id: str,
        relay: Any,
        function: Any,
        function_type: str,
        *,
        name: str = "",
        enabled: bool = True,
        priority: int = 0,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:

        self._validate_id(id)

        if relay is None:
            raise ValueError(
                "relay cannot be None."
            )

        if function is None:
            raise ValueError(
                "function cannot be None."
            )

        if not isinstance(
            function_type,
            str,
        ):
            raise TypeError(
                "function_type must be a string."
            )

        function_type = function_type.strip().upper()

        if not function_type:
            raise ValueError(
                "function_type cannot be empty."
            )

        if not isinstance(
            priority,
            int,
        ):
            raise TypeError(
                "priority must be an integer."
            )

        self.id = id
        self.relay = relay
        self.function = function
        self.function_type = function_type
        self.name = str(name)
        self.enabled = bool(enabled)
        self.priority = priority

        self._metadata: dict[str, Any] = {}

        if metadata is not None:

            if not isinstance(
                metadata,
                Mapping,
            ):
                raise TypeError(
                    "metadata must be a mapping."
                )

            self._metadata.update(
                metadata
            )

        self._state = (
            ProtectionElementState.IDLE
            if self.enabled
            else ProtectionElementState.DISABLED
        )

        self._last_result: bool | None = None

    # =================================================================
    # VALIDATION
    # =================================================================

    @staticmethod
    def _validate_id(
        value: str,
    ) -> None:
        """
        Validate protection-element identity.
        """

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                "ProtectionElement id must be a string."
            )

        if not value.strip():
            raise ValueError(
                "ProtectionElement id cannot be empty."
            )

    # =================================================================
    # RELAY
    # =================================================================

    @property
    def relay_model(self) -> Any:
        """
        Return the authoritative Relay model.
        """

        return self.relay

    # -----------------------------------------------------------------

    @property
    def relay_id(self) -> Any:
        """
        Return the authoritative Relay identifier.
        """

        return getattr(
            self.relay,
            "id",
            None,
        )

    # =================================================================
    # FUNCTION
    # =================================================================

    @property
    def protection_function(self) -> Any:
        """
        Return the associated protection-function implementation.
        """

        return self.function

    # -----------------------------------------------------------------

    @property
    def function_id(self) -> Any:
        """
        Return the identifier of the protection function when
        available.
        """

        return getattr(
            self.function,
            "id",
            None,
        )

    # =================================================================
    # STATE
    # =================================================================

    @property
    def state(self) -> ProtectionElementState:
        """
        Return the current element execution state.
        """

        return self._state

    # -----------------------------------------------------------------

    @property
    def enabled_state(self) -> bool:
        """
        Return whether the element is enabled.
        """

        return self.enabled

    # =================================================================
    # ENABLE / DISABLE
    # =================================================================

    def enable(self) -> None:
        """
        Enable the protection element.

        Enabling the element does not modify the Relay service state.
        """

        self.enabled = True

        if self._state == ProtectionElementState.DISABLED:
            self._state = ProtectionElementState.IDLE

    # -----------------------------------------------------------------

    def disable(self) -> None:
        """
        Disable the protection element.

        Disabling prevents execution of the associated protection
        function.

        It does not modify the physical Relay service state.
        """

        self.enabled = False
        self._state = ProtectionElementState.DISABLED

    # =================================================================
    # EXECUTION
    # =================================================================

    def evaluate(self) -> bool:
        """
        Execute one evaluation cycle of the associated protection
        function.

        Returns
        -------
        bool
            True when the protection function operates.

        Notes
        -----
        The associated protection function is responsible for
        obtaining its electrical inputs through the configured
        measurement architecture.

        ProtectionElement does not calculate electrical quantities.
        """

        if not self.enabled:
            self._state = (
                ProtectionElementState.DISABLED
            )

            self._last_result = False

            return False

        evaluator = getattr(
            self.function,
            "evaluate",
            None,
        )

        if not callable(evaluator):
            raise TypeError(
                f"Protection function for element "
                f"'{self.id}' does not provide evaluate()."
            )

        result = bool(
            evaluator()
        )

        self._last_result = result

        self._synchronize_state()

        return result

    # =================================================================
    # RESET
    # =================================================================

    def reset(self) -> None:
        """
        Reset the protection-function execution state.

        If the protection function provides its own reset() method,
        that method is called.

        ProtectionElement does not directly manipulate Relay
        protection state when the function owns that responsibility.
        """

        resetter = getattr(
            self.function,
            "reset",
            None,
        )

        if callable(resetter):
            resetter()

        self._last_result = None

        self._state = (
            ProtectionElementState.IDLE
            if self.enabled
            else ProtectionElementState.DISABLED
        )

    # =================================================================
    # STATE SYNCHRONIZATION
    # =================================================================

    def _synchronize_state(self) -> None:
        """
        Synchronize the element execution state from the associated
        protection-function decision state.

        The authoritative Relay remains authoritative for relay-level
        protection state.
        """

        if not self.enabled:
            self._state = (
                ProtectionElementState.DISABLED
            )
            return

        function = self.function

        tripped = bool(
            getattr(
                function,
                "tripped",
                False,
            )
        )

        operated = bool(
            getattr(
                function,
                "operated",
                False,
            )
        )

        picked_up = bool(
            getattr(
                function,
                "picked_up",
                False,
            )
        )

        if tripped:
            self._state = (
                ProtectionElementState.TRIPPED
            )

        elif operated:
            self._state = (
                ProtectionElementState.OPERATED
            )

        elif picked_up:
            self._state = (
                ProtectionElementState.PICKUP
            )

        else:
            self._state = (
                ProtectionElementState.IDLE
            )

    # =================================================================
    # RESULT
    # =================================================================

    @property
    def last_result(self) -> bool | None:
        """
        Return the result of the most recent evaluation cycle.
        """

        return self._last_result

    # =================================================================
    # METADATA
    # =================================================================

    @property
    def metadata(self) -> Mapping[str, Any]:
        """
        Return a copy of element metadata.
        """

        return self._metadata.copy()

    # -----------------------------------------------------------------

    def set_metadata(
        self,
        name: str,
        value: Any,
    ) -> None:
        """
        Set protection-element metadata.

        Metadata is element-level information and must not be used
        to duplicate authoritative Relay configuration.
        """

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Metadata name must be a string."
            )

        if not name.strip():
            raise ValueError(
                "Metadata name cannot be empty."
            )

        self._metadata[name] = value

    # =================================================================
    # STATUS
    # =================================================================

    def status(self) -> dict[str, Any]:
        """
        Return structured protection-element status.
        """

        function_status = None

        status_method = getattr(
            self.function,
            "status",
            None,
        )

        if callable(status_method):
            function_status = status_method()

        return {
            "id": self.id,
            "name": self.name,
            "relay_id": self.relay_id,
            "function_id": self.function_id,
            "function_type": self.function_type,
            "enabled": self.enabled,
            "priority": self.priority,
            "state": self.state.value,
            "last_result": self.last_result,
            "metadata": self.metadata,
            "function_status": function_status,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<ProtectionElement "
            f"id={self.id}, "
            f"relay_id={self.relay_id}, "
            f"type={self.function_type}, "
            f"state={self.state.value}, "
            f"enabled={self.enabled}>"
        )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "ProtectionElementState",
    "ProtectionElement",
]
