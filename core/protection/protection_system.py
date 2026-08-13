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
          |
          +-- ProtectionElement
          |       |
          |       +-- RelayBase
          |
          +-- ProtectionElement
                  |
                  +-- RelayBase

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

ProtectionSystem is an orchestration layer.

It does NOT:

    * own physical Relay objects;
    * create measurement channels;
    * create RelayInput objects;
    * calculate electrical quantities;
    * perform load flow;
    * perform short-circuit analysis;
    * perform relay coordination;
    * operate breakers;
    * schedule breaker operations;
    * own ProtectionDecision state.

Multifunction Relay Architecture
---------------------------------

GridForge V2 deliberately supports:

    one Relay
        |
        +-- 50/51
        +-- 67
        +-- 21
        +-- 46
        +-- 50BF

Each ProtectionElement represents one executable protection
function instance.

The physical Relay remains authoritative in the model layer.

Decision Architecture
---------------------

    MeasurementChannel
            |
            v
       RelayInput
            |
            v
       RelayBase
            |
            v
    ProtectionElement
            |
            v
    ProtectionDecision
            |
            v
     ProtectionSystem
            |
            v
    Protection Output
            |
            v
       BreakerManager

ProtectionDecision is the canonical V2 protection evaluation
contract defined in:

    core/protection/decision.py

ProtectionSystem consumes and preserves complete
ProtectionDecision objects.

It does not reduce decisions to booleans and does not
reconstruct protection semantics from arbitrary result objects.

Decision Ownership
------------------

ProtectionSystem does not create or modify ProtectionDecision
objects.

Each ProtectionElement produces a ProtectionDecision.

ProtectionSystem:

    * collects decisions;
    * commits a complete evaluation cycle atomically;
    * provides decision lookup and diagnostic queries;
    * exposes derived protection-state queries.

Physical breaker operation remains outside this class.

Decision Lifecycle
------------------

Each call to evaluate() creates one complete evaluation cycle.

Only decisions produced during that cycle are retained.

The previous successful cycle is replaced atomically after all
enabled elements evaluate successfully.

If an element raises an exception, the current cycle is not
committed.

Therefore, ProtectionSystem never exposes a partially committed
evaluation cycle as authoritative.

Disabled elements are not evaluated and do not contribute a
ProtectionDecision to the current cycle.

Execution Order
---------------

ProtectionElement.priority controls deterministic orchestration
order.

Ordering is:

    1. lower priority first;
    2. element ID as deterministic tie-breaker.

Priority is NOT:

    * relay coordination time;
    * TMS;
    * grading margin;
    * electrical selectivity.

Those concepts belong to the coordination subsystem.

Architecture Boundaries
-----------------------

ProtectionSystem does not:

    * calculate protection characteristics;
    * interpret measurement quantities;
    * manipulate network topology;
    * manipulate breaker state;
    * schedule simulation events;
    * perform relay coordination.

It is strictly an orchestration and decision-collection layer.

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
    System-level orchestration service for GridForge V2
    ProtectionElement objects.

    ProtectionSystem owns the runtime registry of
    ProtectionElement objects.

    It does not own authoritative physical Relay objects or
    ProtectionDecision state.
    """

    # ==================================================================
    # INITIALIZATION
    # ==================================================================

    def __init__(self) -> None:
        """
        Initialize an empty protection-system registry.
        """

        self._elements: dict[str, ProtectionElement] = {}

        # Decisions from the most recently successfully committed
        # evaluation cycle.

        self._last_decisions: tuple[
            ProtectionDecision,
            ...,
        ] = ()

        # Number of successfully committed evaluation cycles.

        self._evaluation_count: int = 0

    # ==================================================================
    # ELEMENT REGISTRATION
    # ==================================================================

    def add_element(
        self,
        element: ProtectionElement,
    ) -> None:
        """
        Register a ProtectionElement.

        Parameters
        ----------
        element:
            ProtectionElement to register.

        Raises
        ------
        TypeError
            If element is not a ProtectionElement.

        ValueError
            If an element with the same ID is already registered.
        """

        if not isinstance(
            element,
            ProtectionElement,
        ):
            raise TypeError(
                "element must be a ProtectionElement."
            )

        element_id = element.id

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

        Removing an element invalidates the cached decision cycle.

        Raises
        ------
        TypeError
            If element_id is not a string.

        KeyError
            If the element is not registered.
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
        Return True when an element is registered.
        """

        return element_id in self._elements

    # ------------------------------------------------------------------

    def get_element(
        self,
        element_id: str,
    ) -> ProtectionElement:
        """
        Return a registered ProtectionElement.

        Raises
        ------
        KeyError
            If the element is not registered.
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
        Return all registered ProtectionElements.

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
        Iterate over registered ProtectionElements.

        Iteration follows registration order.
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
        Return all ProtectionElements hosted by a physical Relay.
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
        Return unique authoritative Relay objects represented by
        registered ProtectionElements.

        Relay ownership and state remain in the model layer.

        Object identity is used to avoid returning the same physical
        Relay multiple times when it hosts multiple
        ProtectionElements.
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
        Return ProtectionElements belonging to a function type.

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

        normalized = (
            function_type.strip().upper()
        )

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
        Return ProtectionElements in deterministic execution order.

        Ordering:

            1. lower priority first;
            2. element ID as deterministic tie-breaker.

        Priority is an orchestration ordering mechanism only.
        """

        return tuple(
            sorted(
                self._elements.values(),
                key=lambda element: (
                    element.priority,
                    str(element.id),
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
            Optional ProtectionContext supplied to each
            ProtectionElement.

        Returns
        -------
        tuple[ProtectionDecision, ...]
            Complete decisions generated during this evaluation cycle.

        Raises
        ------
        RuntimeError
            If an enabled ProtectionElement returns None.

        TypeError
            If an enabled ProtectionElement returns anything other
            than ProtectionDecision.

        Notes
        -----
        Decisions are first assembled in a local collection.

        The local collection becomes the authoritative latest cycle
        only after every enabled ProtectionElement has completed
        successfully.

        Therefore a failed evaluation cannot leave a partially
        committed decision cycle.
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
                raise RuntimeError(
                    f"Enabled protection element "
                    f"'{element.id}' returned None. "
                    "Enabled protection elements must return "
                    "a ProtectionDecision."
                )

            if not isinstance(
                decision,
                ProtectionDecision,
            ):
                raise TypeError(
                    f"Protection element '{element.id}' "
                    "returned an invalid evaluation result. "
                    "Expected ProtectionDecision."
                )

            decisions.append(
                decision
            )

        # Atomic cycle commit.

        committed = tuple(
            decisions
        )

        self._last_decisions = committed
        self._evaluation_count += 1

        return committed

    # ==================================================================
    # LATEST DECISIONS
    # ==================================================================

    @property
    def last_decisions(
        self,
    ) -> tuple[ProtectionDecision, ...]:
        """
        Return decisions from the most recently successfully
        committed evaluation cycle.
        """

        return self._last_decisions

    # ------------------------------------------------------------------

    def latest_decisions(
        self,
    ) -> tuple[ProtectionDecision, ...]:
        """
        Return decisions from the most recently successfully
        committed evaluation cycle.

        Method form retained as a convenient API alias.
        """

        return self._last_decisions

    # ------------------------------------------------------------------

    @property
    def evaluation_count(
        self,
    ) -> int:
        """
        Return the number of successfully committed evaluation cycles.
        """

        return self._evaluation_count

    # ==================================================================
    # DECISION LOOKUP
    # ==================================================================

    def decision_for_element(
        self,
        element_id: str,
    ) -> ProtectionDecision | None:
        """
        Return the latest decision for one ProtectionElement.

        Returns
        -------
        ProtectionDecision | None
            The latest decision associated with the element.

            None means that the element did not participate in the
            latest evaluation cycle.
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

        Function type is resolved through ProtectionElement.

        ProtectionDecision deliberately does not duplicate
        ProtectionElement.function_type.
        """

        if not isinstance(
            function_type,
            str,
        ):
            raise TypeError(
                "function_type must be a string."
            )

        normalized = (
            function_type.strip().upper()
        )

        if not normalized:
            raise ValueError(
                "function_type cannot be empty."
            )

        element_ids = {
            element.id
            for element in self.elements_by_type(
                normalized
            )
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

        ``operate`` is distinct from physical breaker operation.

        This method therefore identifies protection functions that have
        reached their operating criterion, not breakers that have
        physically opened.
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
        Return elements whose latest valid decision is actionable.

        An actionable ProtectionDecision is a protection output
        request.

        It is NOT physical breaker operation.
        """

        trip_ids = {
            decision.element_id
            for decision in self._last_decisions
            if decision.actionable
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
        Reset all registered ProtectionElements.

        This clears protection-function runtime state through each
        ProtectionElement.

        The following are NOT modified:

            * physical Relay state;
            * MeasurementChannel state;
            * network state;
            * simulation state.
        """

        for element in self._elements.values():
            element.reset()

        self._last_decisions = ()
        self._evaluation_count = 0

    # ==================================================================
    # COMPATIBILITY VIEWS
    # ==================================================================

    @property
    def oc_relays(
        self,
    ) -> list[Any]:
        """
        Compatibility view of overcurrent protection functions.

        New V2 code should prefer:

            elements_by_type("OVERCURRENT")

        This property is a derived compatibility view and is not
        authoritative storage.
        """

        return [
            element.protection_function
            for element in self.elements_by_type(
                "OVERCURRENT"
            )
        ]

    # ------------------------------------------------------------------

    @property
    def distance_relays(
        self,
    ) -> list[Any]:
        """
        Compatibility view of distance protection functions.

        New V2 code should prefer:

            elements_by_type("DISTANCE")

        This property is a derived compatibility view and is not
        authoritative storage.
        """

        return [
            element.protection_function
            for element in self.elements_by_type(
                "DISTANCE"
            )
        ]

    # ==================================================================
    # STATUS
    # ==================================================================

    def status(
        self,
    ) -> dict[str, Any]:
        """
        Return structured diagnostic status.

        This is a diagnostic representation only and is not the
        authoritative persistence schema.
        """

        return {
            "element_count": len(
                self._elements
            ),
            "relay_count": len(
                self.relays()
            ),
            "evaluation_count": self._evaluation_count,
            "decision_count": len(
                self._last_decisions
            ),
            "elements": [
                element.status()
                for element in self._execution_order()
            ],
            "last_decisions": [
                self._decision_diagnostics(
                    decision
                )
                for decision in self._last_decisions
            ],
        }

    # ------------------------------------------------------------------

    @staticmethod
    def _decision_diagnostics(
        decision: ProtectionDecision,
    ) -> dict[str, Any]:
        """
        Return diagnostic representation of a ProtectionDecision.

        ProtectionDecision is the finalized canonical decision
        contract, so diagnostics are obtained directly from its
        finalized diagnostics API.
        """

        return decision.diagnostics()

    # ==================================================================
    # REPRESENTATION
    # ==================================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return concise developer-facing representation.
        """

        return (
            f"<ProtectionSystem "
            f"elements={len(self._elements)}, "
            f"relays={len(self.relays())}, "
            f"decisions={len(self._last_decisions)}, "
            f"evaluations={self._evaluation_count}>"
        )


__all__ = [
    "ProtectionSystem",
]
