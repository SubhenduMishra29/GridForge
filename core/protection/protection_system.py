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
                 Protection Result
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
    * own a ProtectionDecision model.

Multifunction Relay Architecture
---------------------------------

GridForge V2 deliberately supports:

    one Relay
        |
        +-- zero or more ProtectionElements

For example:

    Relay R1
        |
        +-- 50/51
        +-- 67
        +-- 21
        +-- 46
        +-- 50BF

Each ProtectionElement represents one executable protection
function instance.

The physical Relay remains authoritative in the model layer.

Execution Architecture
-----------------------

    MeasurementChannel
            |
            v
       RelayInput
            |
            v
       RelayBase
            |
            v
     Protection Result
            |
            v
    ProtectionElement
            |
            v
     ProtectionSystem
            |
            v
    Protection Output Layer
            |
            v
       BreakerManager

Result Ownership
----------------

ProtectionSystem collects the complete results returned by
ProtectionElement.evaluate().

There is deliberately no central ProtectionDecision class.

A protection-function result may expose concepts such as:

    * pickup
    * operate
    * actionable
    * blocked
    * valid
    * operating time
    * measured quantities
    * diagnostics

ProtectionSystem preserves the returned object without reducing it
to a boolean.

Physical breaker operation belongs to the downstream output /
breaker-control layer.

Execution Context
-----------------

ProtectionSystem accepts an optional ProtectionContext.

The context provides evaluation-time information such as:

    * simulation time;
    * timestep;
    * event information;
    * supervision information;
    * authoritative execution references.

ProtectionSystem does not interpret electrical quantities in the
context.

Evaluation Lifecycle
--------------------

Each call to evaluate() creates one complete evaluation cycle.

Only results actually produced during that cycle are retained.

The previous cycle is replaced atomically after successful
evaluation.

If an element raises an exception, the current cycle is not committed
as the latest successful evaluation cycle.

Execution Order
---------------

ProtectionElement.priority controls deterministic orchestration
order.

Ordering is:

    1. priority
    2. element ID

Priority is NOT:

    * relay coordination time;
    * TMS;
    * grading margin;
    * electrical selectivity.

Those concepts belong to the coordination subsystem.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from typing import Any, Iterable

from .context import ProtectionContext
from .protection_element import ProtectionElement


class ProtectionSystem:
    """
    System-level orchestration service for GridForge V2 protection
    elements.

    ProtectionSystem owns the runtime registry of
    ProtectionElement objects.

    It does not own the authoritative physical Relay objects.
    """

    # ==================================================================
    # INITIALIZATION
    # ==================================================================

    def __init__(self) -> None:
        """
        Initialize an empty protection-system registry.
        """

        self._elements: dict[str, ProtectionElement] = {}

        # Results from the most recently successfully committed
        # evaluation cycle.

        self._last_results: tuple[Any, ...] = ()

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

        # Registry mutation invalidates the previous evaluation cycle.
        self._last_results = ()

    # ------------------------------------------------------------------

    def remove_element(
        self,
        element_id: str,
    ) -> ProtectionElement:
        """
        Remove and return a registered ProtectionElement.
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

        self._last_results = ()

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
        Return all protection elements hosted by a physical Relay.
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
        Return elements in deterministic execution order.

        Ordering:

            1. lower priority first;
            2. element ID as deterministic tie-breaker.
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
    ) -> tuple[Any, ...]:
        """
        Evaluate all enabled protection elements.

        Returns
        -------
        tuple[Any, ...]
            Complete protection results generated by the cycle.

        Notes
        -----
        ProtectionSystem deliberately does not require a concrete
        result class.

        The result returned by RelayBase is preserved exactly as
        returned.

        Disabled elements do not participate in the cycle.

        The new cycle is committed only after all enabled elements
        complete successfully.
        """

        results: list[Any] = []

        for element in self._execution_order():

            if not element.enabled:
                continue

            result = element.evaluate(
                context
            )

            if result is None:
                raise RuntimeError(
                    f"Protection element "
                    f"'{element.id}' returned None. "
                    "Enabled protection elements must return "
                    "a protection result."
                )

            results.append(result)

        committed = tuple(
            results
        )

        self._last_results = committed
        self._evaluation_count += 1

        return committed

    # ==================================================================
    # LATEST RESULTS
    # ==================================================================

    @property
    def last_results(
        self,
    ) -> tuple[Any, ...]:
        """
        Return results from the most recently successfully committed
        evaluation cycle.
        """

        return self._last_results

    # ------------------------------------------------------------------

    def latest_results(
        self,
    ) -> tuple[Any, ...]:
        """
        Return results from the most recently successfully committed
        evaluation cycle.
        """

        return self._last_results

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
    # RESULT LOOKUP
    # ==================================================================

    @staticmethod
    def _result_value(
        result: Any,
        *names: str,
        default: Any = None,
    ) -> Any:
        """
        Return the first available result attribute.

        The result object remains owned by the protection function.
        """

        for name in names:

            value = getattr(
                result,
                name,
                None,
            )

            if value is not None:
                return value

        return default

    # ------------------------------------------------------------------

    def result_for_element(
        self,
        element_id: str,
    ) -> Any:
        """
        Return the latest result associated with one element.

        Returns None when that element did not participate in the
        latest evaluation cycle.
        """

        for result in self._last_results:

            if (
                self._result_value(
                    result,
                    "element_id",
                )
                == element_id
            ):
                return result

        return None

    # ------------------------------------------------------------------

    def results_for_relay(
        self,
        relay_id: Any,
    ) -> tuple[Any, ...]:
        """
        Return latest results associated with a physical Relay.
        """

        return tuple(
            result
            for result in self._last_results
            if self._result_value(
                result,
                "relay_id",
            ) == relay_id
        )

    # ------------------------------------------------------------------

    def results_by_function_type(
        self,
        function_type: str,
    ) -> tuple[Any, ...]:
        """
        Return latest results belonging to a function type.

        Function type is resolved through ProtectionElement.
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
            result
            for result in self._last_results
            if self._result_value(
                result,
                "element_id",
            ) in element_ids
        )

    # ==================================================================
    # RESULT QUERIES
    # ==================================================================

    def operated_elements(
        self,
    ) -> tuple[ProtectionElement, ...]:
        """
        Return elements whose latest result reports operation.

        Operation is a protection output indication only.
        """

        operated_ids = {
            self._result_value(
                result,
                "element_id",
            )
            for result in self._last_results
            if (
                self._result_value(
                    result,
                    "valid",
                    default=False,
                )
                and not self._result_value(
                    result,
                    "blocked",
                    default=False,
                )
                and self._result_value(
                    result,
                    "operate",
                    "operated",
                    default=False,
                )
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
        Return elements whose latest result is actionable.

        Actionable protection output is not physical breaker operation.
        """

        actionable_ids = {
            self._result_value(
                result,
                "element_id",
            )
            for result in self._last_results
            if (
                self._result_value(
                    result,
                    "valid",
                    default=False,
                )
                and not self._result_value(
                    result,
                    "blocked",
                    default=False,
                )
                and self._result_value(
                    result,
                    "actionable",
                    default=False,
                )
            )
        }

        return tuple(
            element
            for element in self._elements.values()
            if element.id in actionable_ids
        )

    # ------------------------------------------------------------------

    def pickup_elements(
        self,
    ) -> tuple[ProtectionElement, ...]:
        """
        Return elements whose latest result reports pickup.
        """

        pickup_ids = {
            self._result_value(
                result,
                "element_id",
            )
            for result in self._last_results
            if (
                self._result_value(
                    result,
                    "valid",
                    default=False,
                )
                and self._result_value(
                    result,
                    "pickup",
                    default=False,
                )
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
        Return elements whose latest result reports blocking.
        """

        blocked_ids = {
            self._result_value(
                result,
                "element_id",
            )
            for result in self._last_results
            if self._result_value(
                result,
                "blocked",
                default=False,
            )
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
        Reset all registered protection elements.

        Physical Relay state, measurement infrastructure, network
        state, and simulation state are untouched.
        """

        for element in self._elements.values():
            element.reset()

        self._last_results = ()
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

        New V2 code should prefer elements_by_type("OVERCURRENT").
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

        New V2 code should prefer elements_by_type("DISTANCE").
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

        This is not the persistence schema.
        """

        return {
            "element_count": len(
                self._elements
            ),
            "relay_count": len(
                self.relays()
            ),
            "evaluation_count": self._evaluation_count,
            "result_count": len(
                self._last_results
            ),
            "elements": [
                element.status()
                for element in self._execution_order()
            ],
            "last_results": [
                self._result_diagnostics(
                    result
                )
                for result in self._last_results
            ],
        }

    # ------------------------------------------------------------------

    @staticmethod
    def _result_diagnostics(
        result: Any,
    ) -> Any:
        """
        Produce a diagnostic representation of a protection result.
        """

        diagnostics = getattr(
            result,
            "diagnostics",
            None,
        )

        if callable(diagnostics):
            return diagnostics()

        as_dict = getattr(
            result,
            "as_dict",
            None,
        )

        if callable(as_dict):
            return as_dict()

        if isinstance(
            result,
            dict,
        ):
            return dict(result)

        return repr(result)

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
            f"results={len(self._last_results)}, "
            f"evaluations={self._evaluation_count}>"
        )


__all__ = [
    "ProtectionSystem",
]
