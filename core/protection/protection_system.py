"""
GridForge V2 Protection System
==============================

File
----
core/protection/protection_system.py

Purpose
-------
Provides system-level orchestration of GridForge V2
ProtectionElement objects.

Architectural Position
----------------------

    Physical Relay
          |
          +-- ProtectionElement
          |       |
          |       +-- RelayBase
          |              |
          |              +-- RelayInput
          |                     |
          |                     +-- MeasurementChannel
          |
          +-- ProtectionElement
          |
          +-- ProtectionElement
                  |
                  v
          ProtectionSystem
                  |
                  v
         ProtectionDecision
                  |
                  v
       Protection Output Layer
                  |
                  v
            BreakerManager

Core Responsibility
-------------------
ProtectionSystem is the runtime orchestration boundary for
protection elements.

It:

    * registers ProtectionElement objects;
    * provides deterministic execution ordering;
    * evaluates registered protection elements;
    * retains the latest ProtectionDecision objects;
    * provides decision and element queries;
    * provides multifunction-relay views;
    * provides runtime reset and diagnostics.

ProtectionSystem does NOT:

    * own physical Relay objects;
    * own MeasurementChannel objects;
    * create RelayInput objects;
    * implement protection mathematics;
    * calculate electrical quantities;
    * perform load flow;
    * perform short-circuit analysis;
    * perform relay coordination;
    * operate breakers;
    * schedule breaker operations;
    * modify network topology;
    * contain GUI state;
    * perform persistence.

Multifunction Relay Architecture
--------------------------------

A physical Relay is authoritative in:

    core.model.relay.Relay

One Relay may host multiple independent protection functions:

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

ProtectionSystem stores the ProtectionElement objects, not duplicate
Relay objects.

Decision Ownership
------------------

ProtectionSystem retains complete ProtectionDecision objects.

It does not reduce protection results to booleans and does not
construct physical breaker commands.

The semantic flow is:

    RelayBase.evaluate()
            |
            v
    ProtectionDecision
            |
            v
    ProtectionElement
            |
            v
    ProtectionSystem
            |
            v
    Protection Output / Scheme Layer
            |
            v
    BreakerManager

Execution Order
---------------

ProtectionElement.priority is used only for deterministic
orchestration ordering.

It is NOT:

    * relay coordination priority;
    * TMS;
    * grading margin;
    * breaker priority;
    * electrical selectivity.

Coordination remains a separate subsystem.

Decision Cycle
--------------

Each call to evaluate() creates a new decision cycle.

Only decisions produced during that evaluation cycle are retained as
the system's latest decisions.

Disabled elements are not evaluated and therefore do not contribute a
decision to the cycle.

If an element is removed, the cached decision cycle is invalidated.

Reset clears:

    * ProtectionElement runtime state;
    * cached system decisions.

Reset does not reset:

    * Relay objects;
    * MeasurementChannels;
    * RelayInputs;
    * network state;
    * simulation state;
    * breaker state.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from typing import Any, Iterable

from .context import ProtectionContext
from .decision import ProtectionDecision
from .protection_element import ProtectionElement


class ProtectionSystem:
    """
    Runtime orchestration service for GridForge V2 protection elements.

    The system owns the registry of ProtectionElement objects and the
    latest decision cycle.

    It does not become an owner of the authoritative physical Relay.
    """

    # ==================================================================
    # INITIALIZATION
    # ==================================================================

    def __init__(self) -> None:
        """
        Create an empty protection-system registry.
        """

        self._elements: dict[str, ProtectionElement] = {}

        self._last_decisions: tuple[
            ProtectionDecision,
            ...,
        ] = ()

    # ==================================================================
    # ELEMENT REGISTRATION
    # ==================================================================

    def add_element(
        self,
        element: ProtectionElement,
    ) -> None:
        """
        Register one ProtectionElement.

        ProtectionElement identity is the registry identity.

        A physical Relay may therefore safely host multiple elements.
        """

        if not isinstance(
            element,
            ProtectionElement,
        ):
            raise TypeError(
                "element must be a ProtectionElement."
            )

        element_id = element.id

        if not isinstance(element_id, str):
            raise TypeError(
                "ProtectionElement.id must be a string."
            )

        if not element_id.strip():
            raise ValueError(
                "ProtectionElement.id cannot be empty."
            )

        if element_id in self._elements:
            raise ValueError(
                f"Protection element '{element_id}' "
                "is already registered."
            )

        self._elements[element_id] = element

        # Registry mutation invalidates the previous decision cycle.
        self._last_decisions = ()

    # ------------------------------------------------------------------

    def remove_element(
        self,
        element_id: str,
    ) -> ProtectionElement:
        """
        Remove and return a registered ProtectionElement.

        Removing an element invalidates the latest decision cycle.
        """

        if not isinstance(
            element_id,
            str,
        ):
            raise TypeError(
                "element_id must be a string."
            )

        try:
            element = self._elements.pop(
                element_id
            )
        except KeyError as exc:
            raise KeyError(
                f"Protection element '{element_id}' "
                "is not registered."
            ) from exc

        self._last_decisions = ()

        return element

    # ------------------------------------------------------------------

    def has_element(
        self,
        element_id: str,
    ) -> bool:
        """
        Return whether an element is registered.
        """

        return element_id in self._elements

    # ------------------------------------------------------------------

    def get_element(
        self,
        element_id: str,
    ) -> ProtectionElement:
        """
        Return a registered ProtectionElement.
        """

        try:
            return self._elements[element_id]
        except KeyError as exc:
            raise KeyError(
                f"Protection element '{element_id}' "
                "is not registered."
            ) from exc

    # ==================================================================
    # COLLECTION ACCESS
    # ==================================================================

    @property
    def elements(
        self,
    ) -> tuple[ProtectionElement, ...]:
        """
        Return all registered protection elements.

        The returned tuple cannot modify the internal registry.
        """

        return tuple(
            self._elements.values()
        )

    # ------------------------------------------------------------------

    def iter_elements(
        self,
    ) -> Iterable[ProtectionElement]:
        """
        Iterate over registered protection elements.

        Registration order is preserved.
        """

        return iter(
            self._elements.values()
        )

    # ==================================================================
    # RELAY COMPOSITION
    # ==================================================================

    def elements_for_relay(
        self,
        relay_id: Any,
    ) -> tuple[ProtectionElement, ...]:
        """
        Return all protection elements hosted by one physical Relay.
        """

        return tuple(
            element
            for element in self._elements.values()
            if element.relay_id == relay_id
        )

    # ------------------------------------------------------------------

    def relays(
        self,
    ) -> tuple[Any, ...]:
        """
        Return unique authoritative Relay objects represented by the
        registered ProtectionElements.

        The Relay objects themselves remain owned by the model layer.
        """

        result: list[Any] = []
        seen: set[int] = set()

        for element in self._elements.values():

            relay = element.relay_model

            identity = id(relay)

            if identity in seen:
                continue

            seen.add(identity)
            result.append(relay)

        return tuple(result)

    # ==================================================================
    # FUNCTION TYPE ACCESS
    # ==================================================================

    def elements_by_type(
        self,
        function_type: str,
    ) -> tuple[ProtectionElement, ...]:
        """
        Return protection elements belonging to a function type.

        Examples
        --------
        OVERCURRENT
        DIRECTIONAL
        DISTANCE
        DIFFERENTIAL
        VOLTAGE
        FREQUENCY
        POWER
        BREAKER_FAILURE
        """

        if not isinstance(
            function_type,
            str,
        ):
            raise TypeError(
                "function_type must be a string."
            )

        normalized = function_type.strip().upper()

        if not normalized:
            raise ValueError(
                "function_type cannot be empty."
            )

        return tuple(
            element
            for element in self._elements.values()
            if element.function_type == normalized
        )

    # ==================================================================
    # EXECUTION ORDER
    # ==================================================================

    def _execution_order(
        self,
    ) -> tuple[ProtectionElement, ...]:
        """
        Return elements in deterministic execution order.

        Ordering:

            1. priority
            2. element identifier

        Priority is an execution-order mechanism only.

        It has no protection-coordination meaning.
        """

        return tuple(
            sorted(
                self._elements.values(),
                key=lambda element: (
                    element.priority,
                    element.id,
                ),
            )
        )

    # ==================================================================
    # EVALUATION
    # ==================================================================

    def evaluate(
        self,
        context: ProtectionContext | None = None,
    ) -> tuple[ProtectionDecision, ...]:
        """
        Evaluate all enabled ProtectionElements.

        Parameters
        ----------
        context:
            Optional ProtectionContext supplied unchanged to each
            ProtectionElement.

        Returns
        -------
        tuple[ProtectionDecision, ...]
            Decisions produced by the elements that participated in
            this evaluation cycle.

        Notes
        -----
        ProtectionSystem performs orchestration only.

        It does not:

            * calculate electrical quantities;
            * interpret network equations;
            * coordinate protection;
            * operate breakers;
            * schedule breaker operations.
        """

        decisions: list[
            ProtectionDecision
        ] = []

        for element in self._execution_order():

            if not element.enabled:
                continue

            decision = element.evaluate(
                context
            )

            if decision is None:
                raise TypeError(
                    f"Protection element '{element.id}' "
                    "returned None from evaluate(). "
                    "An enabled protection element must "
                    "return a ProtectionDecision."
                )

            if not isinstance(
                decision,
                ProtectionDecision,
            ):
                raise TypeError(
                    f"Protection element '{element.id}' "
                    "returned an invalid evaluation result. "
                    "Expected ProtectionDecision, got "
                    f"{type(decision).__name__}."
                )

            decisions.append(
                decision
            )

        self._last_decisions = tuple(
            decisions
        )

        return self._last_decisions

    # ==================================================================
    # LATEST DECISIONS
    # ==================================================================

    @property
    def last_decisions(
        self,
    ) -> tuple[ProtectionDecision, ...]:
        """
        Return decisions produced during the latest evaluation cycle.
        """

        return self._last_decisions

    # ------------------------------------------------------------------

    def latest_decisions(
        self,
    ) -> tuple[ProtectionDecision, ...]:
        """
        Return decisions produced during the latest evaluation cycle.
        """

        return self._last_decisions

    # ==================================================================
    # DECISION LOOKUP
    # ==================================================================

    def decision_for_element(
        self,
        element_id: str,
    ) -> ProtectionDecision | None:
        """
        Return the latest decision for one protection element.

        Returns None when the element did not participate in the latest
        evaluation cycle.
        """

        for decision in self._last_decisions:

            if decision.element_id == element_id:
                return decision

        return None

    # ------------------------------------------------------------------

    def decisions_for_relay(
        self,
        relay_id: Any,
    ) -> tuple[ProtectionDecision, ...]:
        """
        Return latest decisions associated with a physical Relay.
        """

        return tuple(
            decision
            for decision in self._last_decisions
            if decision.relay_id == relay_id
        )

    # ------------------------------------------------------------------

    def decisions_by_function_type(
        self,
        function_type: str,
    ) -> tuple[ProtectionDecision, ...]:
        """
        Return latest decisions belonging to a function type.

        Function type is obtained from the associated
        ProtectionElement rather than duplicated into
        ProtectionDecision.
        """

        elements = self.elements_by_type(
            function_type
        )

        element_ids = {
            element.id
            for element in elements
        }

        return tuple(
            decision
            for decision in self._last_decisions
            if decision.element_id in element_ids
        )

    # ==================================================================
    # DECISION QUERIES
    # ==================================================================

    def operated_elements(
        self,
    ) -> tuple[ProtectionElement, ...]:
        """
        Return elements whose latest valid decision reports operation.

        A protection operation is not physical breaker operation.
        """

        operated_ids = {
            decision.element_id
            for decision in self._last_decisions
            if (
                decision.valid
                and not decision.blocked
                and decision.operate
            )
        }

        return tuple(
            element
            for element in self._elements.values()
            if element.id in operated_ids
        )

    # ------------------------------------------------------------------

    def tripped_elements(
        self,
    ) -> tuple[ProtectionElement, ...]:
        """
        Return elements whose latest valid decision contains a trip
        request.

        A trip request is a protection-layer output.

        Breaker operation remains the responsibility of the output
        layer / BreakerManager.
        """

        trip_ids = {
            decision.element_id
            for decision in self._last_decisions
            if (
                decision.valid
                and not decision.blocked
                and decision.trip_request
            )
        }

        return tuple(
            element
            for element in self._elements.values()
            if element.id in trip_ids
        )

    # ------------------------------------------------------------------

    def pickup_elements(
        self,
    ) -> tuple[ProtectionElement, ...]:
        """
        Return elements whose latest valid decision reports pickup.
        """

        pickup_ids = {
            decision.element_id
            for decision in self._last_decisions
            if (
                decision.valid
                and decision.pickup
                and not decision.blocked
            )
        }

        return tuple(
            element
            for element in self._elements.values()
            if element.id in pickup_ids
        )

    # ------------------------------------------------------------------

    def blocked_elements(
        self,
    ) -> tuple[ProtectionElement, ...]:
        """
        Return elements whose latest decision reports blocking.
        """

        blocked_ids = {
            decision.element_id
            for decision in self._last_decisions
            if decision.blocked
        }

        return tuple(
            element
            for element in self._elements.values()
            if element.id in blocked_ids
        )

    # ==================================================================
    # RESET
    # ==================================================================

    def reset(
        self,
    ) -> None:
        """
        Reset all registered protection elements and clear the latest
        decision cycle.

        Only protection-system/function runtime state is reset.
        """

        for element in self._elements.values():
            element.reset()

        self._last_decisions = ()

    # ==================================================================
    # STATUS
    # ==================================================================

    def status(
        self,
    ) -> dict[str, Any]:
        """
        Return structured diagnostic information.

        This is a diagnostic representation, not the authoritative
        persistence representation.
        """

        return {
            "element_count": len(
                self._elements
            ),
            "relay_count": len(
                self.relays()
            ),
            "decision_count": len(
                self._last_decisions
            ),
            "elements": [
                element.status()
                for element in self._execution_order()
            ],
            "last_decisions": [
                self._decision_status(
                    decision
                )
                for decision in self._last_decisions
            ],
        }

    # ------------------------------------------------------------------

    @staticmethod
    def _decision_status(
        decision: ProtectionDecision,
    ) -> Any:
        """
        Obtain a diagnostic representation of a decision without
        requiring ProtectionSystem to own decision serialization.

        ``as_dict()`` is preferred when supplied by the authoritative
        ProtectionDecision contract.
        """

        serializer = getattr(
            decision,
            "as_dict",
            None,
        )

        if callable(serializer):
            return serializer()

        diagnostics = getattr(
            decision,
            "diagnostics",
            None,
        )

        if callable(diagnostics):
            return diagnostics()

        return repr(decision)

    # ==================================================================
    # REPRESENTATION
    # ==================================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise developer-facing representation.
        """

        return (
            f"<ProtectionSystem "
            f"elements={len(self._elements)}, "
            f"relays={len(self.relays())}, "
            f"decisions={len(self._last_decisions)}>"
        )


__all__ = [
    "ProtectionSystem",
]
