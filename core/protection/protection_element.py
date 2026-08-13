"""
GridForge V2 Protection Element
================================

File
----
core/protection/protection_element.py

Purpose
-------
Defines the composition object representing one protection function
hosted by an authoritative physical Relay.

Architectural Position
----------------------

    Physical Relay
        |
        +-----------------------------+
        |                             |
        v                             v
 ProtectionElement              ProtectionElement
        |                             |
        v                             v
    RelayBase                     RelayBase
        |                             |
        v                             v
 Protection evaluation           Protection evaluation
        |                             |
        +-------------+---------------+
                      |
                      v
              ProtectionSystem
                      |
                      v
             Protection output
                      |
                      v
              BreakerManager

Important
---------
ProtectionElement is NOT the executable protection algorithm.

RelayBase is the executable protection-function contract.

ProtectionElement is the stable composition boundary between:

    authoritative Relay
            and
    executable RelayBase protection function.

A physical Relay may therefore host multiple independent
ProtectionElements.

Example
-------

    Relay R1
        |
        +-- ProtectionElement OC51
        |       |
        |       +-- RelayBase
        |
        +-- ProtectionElement DIR67
        |       |
        |       +-- RelayBase
        |
        +-- ProtectionElement DIST21
                |
                +-- RelayBase

Measurement Architecture
-------------------------

    CT / PT / CVT
          |
          v
    MeasurementChannel
          |
          v
       RelayInput
          |
          v
       RelayBase
          |
          v
    Protection evaluation
          |
          v
    ProtectionElement
          |
          v
    ProtectionSystem

MeasurementChannel remains authoritative for measurement state.

RelayInput remains the protection-facing measurement binding.

ProtectionElement does not create, copy, transform, validate, or own
measurement state.

Responsibilities
----------------

ProtectionElement owns:

* protection-element identity;
* reference to the authoritative Relay;
* reference to one RelayBase implementation;
* element classification;
* enable/disable state;
* orchestration priority;
* lifecycle/execution state;
* latest evaluation result;
* element-level metadata;
* diagnostics.

ProtectionElement does NOT own:

* physical Relay identity;
* CT/PT/CVT state;
* MeasurementChannel state;
* protection mathematics;
* protection settings belonging to RelayBase;
* network topology;
* breaker operation;
* system-wide coordination;
* simulation time;
* protection scheduling;
* protection decisions as a separate state model.

Execution Contract
------------------

The executable protection function is evaluated through:

    function.evaluate(context)

The returned object is preserved as-is by ProtectionElement.

ProtectionElement does not reduce the result to a boolean.

ProtectionElement therefore remains compatible with the canonical V2
protection evaluation contract without maintaining a second
ProtectionDecision implementation.

State Semantics
---------------

ProtectionElementState represents only the lifecycle/orchestration
state of the element.

It is intentionally not a duplicate representation of the complete
protection decision.

The canonical states are:

    DISABLED
    IDLE
    PICKUP
    OPERATED
    BLOCKED
    FAILED

The detailed protection result remains in ``last_decision``.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping

from core.protection.context import ProtectionContext


# =====================================================================
# PROTECTION ELEMENT STATE
# =====================================================================


class ProtectionElementState(Enum):
    """
    Lifecycle/orchestration state of a ProtectionElement.

    These states provide a coarse operational view.

    They are not a replacement for the detailed result returned by
    the associated RelayBase implementation.
    """

    DISABLED = "DISABLED"
    IDLE = "IDLE"
    PICKUP = "PICKUP"
    OPERATED = "OPERATED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


# =====================================================================
# PROTECTION ELEMENT
# =====================================================================


class ProtectionElement:
    """
    Composition object representing one protection function hosted by
    an authoritative physical Relay.

    A ProtectionElement does not implement protection mathematics.

    It owns the relationship between:

        Relay
          |
          +-- ProtectionElement
                  |
                  +-- RelayBase
    """

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

        # -------------------------------------------------------------
        # Identity
        # -------------------------------------------------------------

        self._validate_id(id)

        element_id = id.strip()

        # -------------------------------------------------------------
        # Authoritative Relay
        # -------------------------------------------------------------

        if relay is None:
            raise ValueError(
                "relay cannot be None."
            )

        # -------------------------------------------------------------
        # Executable protection function
        # -------------------------------------------------------------

        if function is None:
            raise ValueError(
                "function cannot be None."
            )

        evaluator = getattr(
            function,
            "evaluate",
            None,
        )

        if not callable(evaluator):
            raise TypeError(
                "function must provide a callable evaluate(context) "
                "method."
            )

        # -------------------------------------------------------------
        # Function classification
        # -------------------------------------------------------------

        if not isinstance(
            function_type,
            str,
        ):
            raise TypeError(
                "function_type must be a string."
            )

        normalized_function_type = (
            function_type.strip().upper()
        )

        if not normalized_function_type:
            raise ValueError(
                "function_type cannot be empty."
            )

        # -------------------------------------------------------------
        # Priority
        # -------------------------------------------------------------

        if isinstance(
            priority,
            bool,
        ):
            raise TypeError(
                "priority must be an integer."
            )

        if not isinstance(
            priority,
            int,
        ):
            raise TypeError(
                "priority must be an integer."
            )

        # -------------------------------------------------------------
        # Metadata
        # -------------------------------------------------------------

        if metadata is None:
            normalized_metadata: dict[str, Any] = {}
        elif not isinstance(
            metadata,
            Mapping,
        ):
            raise TypeError(
                "metadata must be a mapping."
            )
        else:
            normalized_metadata = dict(
                metadata
            )

        # -------------------------------------------------------------
        # Store authoritative references
        # -------------------------------------------------------------

        self.id = element_id
        self.relay = relay
        self.function = function

        self.function_type = (
            normalized_function_type
        )

        self.name = str(
            name
        ).strip()

        self.enabled = bool(
            enabled
        )

        self.priority = priority

        self._metadata = (
            normalized_metadata
        )

        # -------------------------------------------------------------
        # Runtime state
        # -------------------------------------------------------------

        self._state = (
            ProtectionElementState.IDLE
            if self.enabled
            else ProtectionElementState.DISABLED
        )

        self._last_decision: Any = None

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
        Return the authoritative physical Relay reference.
        """

        return self.relay

    # -----------------------------------------------------------------

    @property
    def relay_id(self) -> Any:
        """
        Return the authoritative physical Relay identifier.

        The identifier is derived from the Relay and is not duplicated
        as independent ProtectionElement state.
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
        Return the executable RelayBase protection-function instance.
        """

        return self.function

    # -----------------------------------------------------------------

    @property
    def function_id(self) -> Any:
        """
        Return the executable protection-function identifier when
        available.
        """

        return getattr(
            self.function,
            "id",
            None,
        )

    # -----------------------------------------------------------------

    @property
    def function_code(self) -> str | None:
        """
        Return the canonical protection-function code exposed by the
        RelayBase implementation.

        ProtectionElement does not maintain a second function-code
        identity.
        """

        value = getattr(
            self.function,
            "function_code",
            None,
        )

        if value is None:
            return None

        return str(
            value
        ).strip().upper()

    # =================================================================
    # STATE
    # =================================================================

    @property
    def state(self) -> ProtectionElementState:
        """
        Return the current element lifecycle state.
        """

        return self._state

    # -----------------------------------------------------------------

    @property
    def enabled_state(self) -> bool:
        """
        Return whether this protection element is enabled.
        """

        return self.enabled

    # =================================================================
    # LAST DECISION
    # =================================================================

    @property
    def last_decision(self) -> Any:
        """
        Return the complete result of the most recent evaluation.

        The result is intentionally preserved without conversion to a
        boolean so that protection information is not lost.
        """

        return self._last_decision

    # =================================================================
    # ENABLE / DISABLE
    # =================================================================

    def enable(self) -> None:
        """
        Enable this protection element.

        Enabling the element does not modify the authoritative Relay.
        """

        self.enabled = True

        if (
            self._state
            == ProtectionElementState.DISABLED
        ):
            self._state = (
                ProtectionElementState.IDLE
            )

    # -----------------------------------------------------------------

    def disable(self) -> None:
        """
        Disable this protection element.

        Disabling the element does not modify the authoritative Relay.
        """

        self.enabled = False

        self._state = (
            ProtectionElementState.DISABLED
        )

    # =================================================================
    # EXECUTION
    # =================================================================

    def evaluate(
        self,
        context: ProtectionContext,
    ) -> Any:
        """
        Evaluate the associated RelayBase protection function.

        Parameters
        ----------
        context:
            Immutable protection execution context.

        Returns
        -------
        Any
            The complete result returned by RelayBase.evaluate().

        Notes
        -----
        ProtectionElement does not perform protection calculations.

        The returned protection result is preserved as-is.

        A disabled element does not execute its protection function
        and returns None.
        """

        if not isinstance(
            context,
            ProtectionContext,
        ):
            raise TypeError(
                "context must be a ProtectionContext."
            )

        if not self.enabled:

            self._state = (
                ProtectionElementState.DISABLED
            )

            self._last_decision = None

            return None

        evaluator = getattr(
            self.function,
            "evaluate",
            None,
        )

        if not callable(
            evaluator
        ):
            self._state = (
                ProtectionElementState.FAILED
            )

            raise TypeError(
                f"Protection function for element "
                f"'{self.id}' does not provide "
                f"evaluate(context)."
            )

        try:
            result = evaluator(
                context
            )

        except Exception:
            self._state = (
                ProtectionElementState.FAILED
            )
            raise

        self._last_decision = result

        self._synchronize_state()

        return result

    # =================================================================
    # RESET
    # =================================================================

    def reset(self) -> None:
        """
        Reset this ProtectionElement runtime state.

        The associated RelayBase runtime is reset when supported.

        The authoritative physical Relay is never reset here.
        """

        resetter = getattr(
            self.function,
            "reset",
            None,
        )

        if callable(
            resetter
        ):
            resetter()

        self._last_decision = None

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
        Synchronize the coarse element state from the latest result.

        This method intentionally uses the canonical V2 decision
        attributes rather than maintaining a second decision model.
        """

        if not self.enabled:

            self._state = (
                ProtectionElementState.DISABLED
            )

            return

        result = self._last_decision

        if result is None:

            self._state = (
                ProtectionElementState.IDLE
            )

            return

        if bool(
            getattr(
                result,
                "blocked",
                False,
            )
        ):

            self._state = (
                ProtectionElementState.BLOCKED
            )

            return

        if bool(
            getattr(
                result,
                "operate",
                False,
            )
        ):

            self._state = (
                ProtectionElementState.OPERATED
            )

            return

        if bool(
            getattr(
                result,
                "pickup",
                False,
            )
        ):

            self._state = (
                ProtectionElementState.PICKUP
            )

            return

        self._state = (
            ProtectionElementState.IDLE
        )

    # =================================================================
    # METADATA
    # =================================================================

    @property
    def metadata(self) -> Mapping[str, Any]:
        """
        Return a detached copy of element-local metadata.
        """

        return self._metadata.copy()

    # -----------------------------------------------------------------

    def set_metadata(
        self,
        name: str,
        value: Any,
    ) -> None:
        """
        Set element-local metadata.

        Metadata must not duplicate authoritative Relay state or
        RelayBase protection settings.
        """

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "Metadata name must be a string."
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "Metadata name cannot be empty."
            )

        self._metadata[name] = value

    # =================================================================
    # STATUS
    # =================================================================

    def status(self) -> dict[str, Any]:
        """
        Return structured diagnostic information.

        This is a diagnostic representation, not a persistence
        representation.
        """

        function_status = None

        status_method = getattr(
            self.function,
            "status",
            None,
        )

        if callable(
            status_method
        ):
            function_status = status_method()

        decision_status = None

        if self._last_decision is not None:

            diagnostics = getattr(
                self._last_decision,
                "diagnostics",
                None,
            )

            if callable(
                diagnostics
            ):
                decision_status = diagnostics()

            elif isinstance(
                self._last_decision,
                Mapping,
            ):
                decision_status = dict(
                    self._last_decision
                )

        return {
            "id": self.id,
            "name": self.name,
            "relay_id": self.relay_id,
            "function_id": self.function_id,
            "function_code": self.function_code,
            "function_type": self.function_type,
            "enabled": self.enabled,
            "priority": self.priority,
            "state": self.state.value,
            "last_decision": decision_status,
            "metadata": self.metadata,
            "function_status": function_status,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        return (
            f"<ProtectionElement "
            f"id={self.id!r}, "
            f"relay_id={self.relay_id!r}, "
            f"type={self.function_type!r}, "
            f"state={self.state.value!r}, "
            f"enabled={self.enabled}>"
        )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "ProtectionElementState",
    "ProtectionElement",
]
