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
 ProtectionDecision             ProtectionDecision
        |                             |
        +-------------+---------------+
                      |
                      v
              ProtectionSystem
                      |
                      v
             Protection Output
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
    ProtectionDecision
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
* latest ProtectionDecision;
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
* ProtectionDecision as a separate decision model.


Execution Contract
------------------

The executable protection function is evaluated through:

    function.evaluate(context)

The required return type is:

    ProtectionDecision

The returned ProtectionDecision is preserved as-is.

ProtectionElement additionally verifies that the returned decision
belongs to this ProtectionElement and its authoritative Relay.

This prevents a protection-function implementation from accidentally
returning a decision belonging to another protection element.


Decision Identity Contract
--------------------------

The canonical ProtectionDecision identity is:

    decision.element_id

The authoritative physical Relay identity is:

    decision.relay_id

Therefore, after successful evaluation:

    decision.element_id == self.id

and, when the authoritative Relay exposes ``id``:

    decision.relay_id == self.relay_id

A decision violating either identity constraint is rejected and the
element enters FAILED state.

This is an integrity boundary, not protection logic.


State Semantics
---------------

ProtectionElementState represents only lifecycle/orchestration state.

It is intentionally not a duplicate representation of the complete
ProtectionDecision.

Canonical states:

    DISABLED
    IDLE
    PICKUP
    OPERATED
    BLOCKED
    FAILED

The detailed protection result remains in ``last_decision``.

``OPERATED`` means that the protection decision reports
``operate=True``.

It does NOT mean that a physical breaker has operated.


Lifecycle
---------

Each successful call to evaluate():

    1. validates the execution context;
    2. invokes RelayBase.evaluate(context);
    3. requires a ProtectionDecision;
    4. validates decision identity;
    5. stores that exact decision object;
    6. synchronizes the coarse lifecycle state;
    7. returns the same ProtectionDecision object.

If evaluation raises an exception:

    * the element enters FAILED state;
    * the previous successful decision is retained;
    * the exception is propagated.

If the function returns an invalid result:

    * the element enters FAILED state;
    * the previous successful decision is retained;
    * the invalid result is not committed.


Reset
-----

reset() clears runtime decision state.

The associated RelayBase reset() method is invoked when available.

If RelayBase.reset() raises an exception:

    * the element enters FAILED state;
    * the previous decision is retained;
    * the exception is propagated.

If reset succeeds:

    * last_decision becomes None;
    * state becomes IDLE when enabled;
    * state becomes DISABLED when disabled.

The authoritative physical Relay is never reset here.


Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .context import ProtectionContext
from .decision import ProtectionDecision


# =====================================================================
# PROTECTION ELEMENT STATE
# =====================================================================


class ProtectionElementState(Enum):
    """
    Coarse lifecycle/orchestration state of a ProtectionElement.

    These states are derived from element execution state and the
    latest canonical ProtectionDecision.

    They are not a replacement for ProtectionDecision.
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
    Composition boundary between an authoritative Relay and one
    executable RelayBase protection function.

    ProtectionElement owns orchestration state only.

    It does not perform protection calculations and does not own
    measurement, network, simulation, or breaker state.
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
        # -------------------------------------------------------------
        # Element identity
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

        relay_id = getattr(
            relay,
            "id",
            None,
        )

        if relay_id is None:
            raise TypeError(
                "relay must expose a non-None 'id' attribute."
            )

        # A physical Relay identity must be stable enough to
        # participate in ProtectionDecision identity validation.
        if isinstance(relay_id, str):
            if not relay_id.strip():
                raise ValueError(
                    "relay.id cannot be empty."
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
                "function must provide a callable "
                "evaluate(context) method."
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

        # Authoritative physical Relay reference.
        self.relay = relay

        # Executable RelayBase protection-function reference.
        self.function = function

        # Element-level classification.
        #
        # This is intentionally distinct from function.function_code.
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

        # Canonical latest ProtectionDecision.
        self._last_decision: ProtectionDecision | None = None

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
        Return the protection-function code exposed by RelayBase.

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

        normalized = str(
            value
        ).strip().upper()

        return normalized or None

    # =================================================================
    # STATE
    # =================================================================

    @property
    def state(self) -> ProtectionElementState:
        """
        Return the current lifecycle state.
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
    def last_decision(
        self,
    ) -> ProtectionDecision | None:
        """
        Return the latest successfully committed ProtectionDecision.

        The exact canonical decision object is preserved.
        """

        return self._last_decision

    # =================================================================
    # ENABLE / DISABLE
    # =================================================================

    def enable(self) -> None:
        """
        Enable this protection element.

        Enabling does not clear the previous decision.

        Enabling does not modify the authoritative Relay.
        """

        self.enabled = True

        if self._state == ProtectionElementState.DISABLED:
            self._state = ProtectionElementState.IDLE

    # -----------------------------------------------------------------

    def disable(self) -> None:
        """
        Disable this protection element.

        The previous successful decision remains available until
        reset() or a later successful evaluation.

        Disabling does not modify the authoritative Relay.
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
    ) -> ProtectionDecision | None:
        """
        Evaluate the associated RelayBase protection function.

        Parameters
        ----------
        context:
            Canonical immutable ProtectionContext.

        Returns
        -------
        ProtectionDecision | None
            The exact canonical ProtectionDecision returned by the
            RelayBase implementation.

            ``None`` is returned only when this element is disabled.

        Raises
        ------
        TypeError
            If context is not ProtectionContext or the function returns
            an invalid result.

        ValueError
            If the returned ProtectionDecision has an identity mismatch.

        Exception
            Any exception raised by the underlying protection function
            is propagated after the element enters FAILED state.

        Transaction Semantics
        ---------------------
        A decision is committed only after:

            1. function evaluation succeeds;
            2. result type is valid;
            3. element identity matches;
            4. Relay identity matches.

        Therefore a failed evaluation never destroys the previous
        successfully committed decision.
        """

        # -------------------------------------------------------------
        # Context contract
        # -------------------------------------------------------------

        if not isinstance(
            context,
            ProtectionContext,
        ):
            raise TypeError(
                "context must be a ProtectionContext."
            )

        # -------------------------------------------------------------
        # Disabled element
        # -------------------------------------------------------------

        if not self.enabled:

            self._state = (
                ProtectionElementState.DISABLED
            )

            return None

        # -------------------------------------------------------------
        # Validate executable function
        # -------------------------------------------------------------

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

        # -------------------------------------------------------------
        # Execute protection function
        # -------------------------------------------------------------

        try:
            decision = evaluator(
                context
            )

        except Exception:
            self._state = (
                ProtectionElementState.FAILED
            )

            # Previous successful decision remains untouched.
            raise

        # -------------------------------------------------------------
        # Canonical decision contract
        # -------------------------------------------------------------

        if not isinstance(
            decision,
            ProtectionDecision,
        ):
            self._state = (
                ProtectionElementState.FAILED
            )

            raise TypeError(
                f"Protection function for element "
                f"'{self.id}' returned an invalid evaluation result. "
                f"Expected ProtectionDecision, got "
                f"{type(decision).__name__}."
            )

        # -------------------------------------------------------------
        # Decision identity integrity
        # -------------------------------------------------------------

        if decision.element_id != self.id:

            self._state = (
                ProtectionElementState.FAILED
            )

            raise ValueError(
                f"Protection decision identity mismatch for "
                f"element '{self.id}': "
                f"expected element_id={self.id!r}, "
                f"received {decision.element_id!r}."
            )

        # -------------------------------------------------------------
        # Relay identity integrity
        # -------------------------------------------------------------

        expected_relay_id = self.relay_id

        if decision.relay_id != expected_relay_id:

            self._state = (
                ProtectionElementState.FAILED
            )

            raise ValueError(
                f"Protection decision Relay identity mismatch "
                f"for element '{self.id}': "
                f"expected relay_id={expected_relay_id!r}, "
                f"received {decision.relay_id!r}."
            )

        # -------------------------------------------------------------
        # Commit canonical decision
        # -------------------------------------------------------------

        self._last_decision = decision

        self._synchronize_state()

        # Return the exact object supplied by RelayBase.
        return decision

    # =================================================================
    # RESET
    # =================================================================

    def reset(self) -> None:
        """
        Reset runtime state.

        RelayBase.reset() is delegated when available.

        The authoritative physical Relay is never reset.

        Reset is transactional with respect to the element's
        ProtectionDecision: the previous decision is retained if the
        underlying function reset fails.
        """

        resetter = getattr(
            self.function,
            "reset",
            None,
        )

        if callable(
            resetter
        ):
            try:
                resetter()

            except Exception:
                self._state = (
                    ProtectionElementState.FAILED
                )

                # Preserve previous successful decision.
                raise

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
        Synchronize coarse lifecycle state from the canonical
        ProtectionDecision.

        Precedence:

            BLOCKED
                ↓
            OPERATED
                ↓
            PICKUP
                ↓
            IDLE

        The decision remains authoritative for detailed semantics.
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

        if decision.blocked:

            self._state = (
                ProtectionElementState.BLOCKED
            )

            return

        if decision.operate:

            self._state = (
                ProtectionElementState.OPERATED
            )

            return

        if decision.pickup:

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
    def metadata(
        self,
    ) -> Mapping[str, Any]:
        """
        Return read-only element-local metadata.

        Metadata is descriptive/orchestration information only.
        """

        return MappingProxyType(
            dict(
                self._metadata
            )
        )

    # -----------------------------------------------------------------

    def set_metadata(
        self,
        name: str,
        value: Any,
    ) -> None:
        """
        Set element-local metadata.

        This does not modify authoritative Relay or RelayBase state.
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

        self._metadata[
            normalized_name
        ] = value

    # =================================================================
    # STATUS
    # =================================================================

    def status(
        self,
    ) -> dict[str, Any]:
        """
        Return structured diagnostic information.

        This is a diagnostic representation, not a persistence
        representation.
        """

        # -------------------------------------------------------------
        # Protection-function diagnostics
        # -------------------------------------------------------------

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

        # -------------------------------------------------------------
        # Decision diagnostics
        # -------------------------------------------------------------

        decision_status = None

        if self._last_decision is not None:
            decision_status = (
                self._last_decision.diagnostics()
            )

        # -------------------------------------------------------------
        # Diagnostic structure
        # -------------------------------------------------------------

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
            "metadata": dict(
                self._metadata
            ),
            "function_status": function_status,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return concise developer-facing representation.
        """

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
