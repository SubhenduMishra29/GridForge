"""
GridForge V2 Protection Element
==============================

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
        v
    core.model.relay.Relay
        |
        +----------------------------+
        |                            |
        v                            v
 ProtectionElement             ProtectionElement
        |                            |
        v                            v
   RelayBase                    RelayBase
        |                            |
        v                            v
  50/51 Function                21 / 67 / 87 ...
        |
        v
 ProtectionDecision
        |
        v
 ProtectionSystem
        |
        v
 Breaker/control orchestration

Important
---------
ProtectionElement is NOT the executable protection algorithm.

RelayBase is the executable protection-function contract.

ProtectionElement is the stable composition boundary between:

    authoritative Relay
            and
    executable protection function

A physical Relay may therefore contain multiple
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

Measurement architecture
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
 ProtectionDecision
          |
          v
 ProtectionElement
          |
          v
 ProtectionSystem

ProtectionElement does not create or own measurement channels.

Responsibilities
----------------

ProtectionElement owns:

* protection-element identity;
* reference to the authoritative Relay;
* reference to one RelayBase implementation;
* element classification;
* enable/disable state;
* orchestration priority;
* element lifecycle state;
* latest protection decision;
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
* simulation clock;
* global protection state.

Execution Contract
------------------

The protection function is evaluated through:

    function.evaluate(context)

and returns a ProtectionDecision or compatible decision object.

ProtectionElement records that result.

It does not convert the result into a boolean and discard the
decision information.

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
    Element-level execution state.

    These states describe the orchestration state of the protection
    element. They are not a replacement for the detailed
    ProtectionDecision returned by RelayBase.
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
    Composition object representing one protection function hosted by
    an authoritative Relay.
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

        self._validate_id(id)

        if relay is None:
            raise ValueError(
                "relay cannot be None."
            )

        if function is None:
            raise ValueError(
                "function cannot be None."
            )

        if not isinstance(function_type, str):
            raise TypeError(
                "function_type must be a string."
            )

        function_type = function_type.strip().upper()

        if not function_type:
            raise ValueError(
                "function_type cannot be empty."
            )

        if isinstance(priority, bool):
            raise TypeError(
                "priority must be an integer."
            )

        if not isinstance(priority, int):
            raise TypeError(
                "priority must be an integer."
            )

        self.id = id
        self.relay = relay
        self.function = function
        self.function_type = function_type
        self.name = str(name).strip()

        self.enabled = bool(enabled)
        self.priority = priority

        self._metadata: dict[str, Any] = dict(
            metadata or {}
        )

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
    def _validate_id(value: str) -> None:
        """
        Validate protection-element identity.
        """

        if not isinstance(value, str):
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
        Return the authoritative physical Relay.
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
        Return the executable protection-function implementation.

        Normally this is a RelayBase instance.
        """

        return self.function

    # -----------------------------------------------------------------

    @property
    def function_id(self) -> Any:
        """
        Return the protection-function identifier when available.
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
        Return the canonical protection function code when available.
        """

        value = getattr(
            self.function,
            "function_code",
            None,
        )

        if value is None:
            return None

        return str(value)

    # =================================================================
    # STATE
    # =================================================================

    @property
    def state(self) -> ProtectionElementState:
        """
        Return the element orchestration state.
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
    # DECISION
    # =================================================================

    @property
    def last_decision(self) -> Any:
        """
        Return the complete result of the most recent evaluation.

        The decision object is intentionally returned without being
        converted to a boolean so that trip, pickup, blocking,
        timing and diagnostic information is preserved.
        """

        return self._last_decision

    # -----------------------------------------------------------------

    @property
    def last_result(self) -> bool | None:
        """
        Compatibility-level boolean indication.

        Returns True when the latest decision indicates operation.

        Detailed protection information remains available through
        ``last_decision``.
        """

        decision = self._last_decision

        if decision is None:
            return None

        return self._decision_operated(
            decision
        )

    # =================================================================
    # ENABLE / DISABLE
    # =================================================================

    def enable(self) -> None:
        """
        Enable this protection element.

        Does not modify the physical Relay service state.
        """

        self.enabled = True

        if self._state == ProtectionElementState.DISABLED:
            self._state = ProtectionElementState.IDLE

    # -----------------------------------------------------------------

    def disable(self) -> None:
        """
        Disable this protection element.

        Does not modify the physical Relay service state.
        """

        self.enabled = False
        self._state = ProtectionElementState.DISABLED

    # =================================================================
    # EXECUTION
    # =================================================================

    def evaluate(
        self,
        context: ProtectionContext | None = None,
    ) -> Any:
        """
        Evaluate the associated protection function.

        Parameters
        ----------
        context:
            Optional ProtectionContext.

            The context is forwarded to RelayBase.evaluate().

        Returns
        -------
        Any
            Normally a ProtectionDecision.

        Notes
        -----
        ProtectionElement does not perform protection calculations.

        It records the complete decision returned by the protection
        function.
        """

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

        if not callable(evaluator):
            raise TypeError(
                f"Protection function for element "
                f"'{self.id}' does not provide evaluate()."
            )

        try:
            decision = evaluator(
                context
            )
        except Exception:
            self._state = (
                ProtectionElementState.FAILED
            )
            raise

        self._last_decision = decision

        self._synchronize_state()

        return decision

    # =================================================================
    # RESET
    # =================================================================

    def reset(self) -> None:
        """
        Reset this protection element.

        The associated RelayBase runtime is reset if supported.

        The authoritative Relay itself is never reset here.
        """

        resetter = getattr(
            self.function,
            "reset",
            None,
        )

        if callable(resetter):
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
        Derive the element state from the latest protection decision.

        Decision objects are intentionally queried structurally so
        this composition layer does not need to own the concrete
        decision implementation.
        """

        if not self.enabled:
            self._state = (
                ProtectionElementState.DISABLED
            )
            return

        decision = self._last_decision

        if decision is None:
            self._state = (
                ProtectionElementState.IDLE
            )
            return

        if self._decision_blocked(decision):
            self._state = (
                ProtectionElementState.BLOCKED
            )
            return

        if self._decision_tripped(decision):
            self._state = (
                ProtectionElementState.TRIPPED
            )
            return

        if self._decision_operated(decision):
            self._state = (
                ProtectionElementState.OPERATED
            )
            return

        if self._decision_pickup(decision):
            self._state = (
                ProtectionElementState.PICKUP
            )
            return

        self._state = (
            ProtectionElementState.IDLE
        )

    # =================================================================
    # DECISION INTERPRETATION
    # =================================================================

    @staticmethod
    def _decision_value(
        decision: Any,
        *names: str,
    ) -> bool:
        """
        Return the first supported boolean decision attribute.
        """

        for name in names:

            value = getattr(
                decision,
                name,
                None,
            )

            if value is not None:
                return bool(value)

        return False

    # -----------------------------------------------------------------

    @classmethod
    def _decision_pickup(
        cls,
        decision: Any,
    ) -> bool:
        return cls._decision_value(
            decision,
            "pickup",
            "picked_up",
        )

    # -----------------------------------------------------------------

    @classmethod
    def _decision_operated(
        cls,
        decision: Any,
    ) -> bool:
        return cls._decision_value(
            decision,
            "operate",
            "operated",
            "trip",
            "tripped",
        )

    # -----------------------------------------------------------------

    @classmethod
    def _decision_tripped(
        cls,
        decision: Any,
    ) -> bool:
        return cls._decision_value(
            decision,
            "trip",
            "tripped",
        )

    # -----------------------------------------------------------------

    @classmethod
    def _decision_blocked(
        cls,
        decision: Any,
    ) -> bool:
        return cls._decision_value(
            decision,
            "blocked",
        )

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
        Set element-level metadata.

        Metadata must not be used to duplicate authoritative Relay
        configuration or protection-function settings.
        """

        if not isinstance(name, str):
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

        decision_status = None

        if self._last_decision is not None:

            diagnostics = getattr(
                self._last_decision,
                "diagnostics",
                None,
            )

            if callable(diagnostics):
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
            "last_result": self.last_result,
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
