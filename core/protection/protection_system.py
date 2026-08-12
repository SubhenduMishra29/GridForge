```python
"""
GridForge V2 Protection System
==============================

File:
    core/protection/protection_system.py

Purpose
-------
Central orchestration layer for GridForge V2 protection-function
plugins.

The ProtectionSystem manages protection ELEMENTS, not physical relay
devices.

A single physical Relay may host many protection functions:

    Relay
      |
      +-- 50  Instantaneous Overcurrent
      +-- 51  Time Overcurrent
      +-- 67  Directional Overcurrent
      +-- 21  Distance
      +-- 87  Differential
      +-- 27  Undervoltage
      +-- 59  Overvoltage
      +-- 81  Frequency
      +-- 50BF Breaker Failure
      +-- custom/vendor functions

Architecture
------------

    Physical Equipment
            |
        CT / PT / CVT
            |
    MeasurementChannel
            |
        RelayInput
            |
    core.model.relay.Relay
            |
    RelayBase / Protection Element
            |
    ProtectionDecision
            |
    ProtectionSystem
            |
       TripRequest
            |
       BreakerManager
            |
          Breaker


Responsibilities
----------------
ProtectionSystem is responsible for:

    - protection-element registration;
    - protection-element lifecycle;
    - multifunction-relay support;
    - deterministic evaluation;
    - collection of ProtectionDecision objects;
    - decision filtering;
    - trip-request extraction;
    - evaluation history;
    - system reset;
    - protection status;
    - element lookup;
    - relay/function lookup;
    - protection-system diagnostics.

ProtectionSystem does NOT:

    - own the authoritative Relay model;
    - create CT/PT/CVT equipment;
    - create MeasurementChannels;
    - calculate measurements;
    - calculate fault current;
    - build Y-bus;
    - perform load flow;
    - perform short-circuit analysis;
    - calculate IEC curves;
    - perform relay coordination;
    - operate circuit breakers;
    - modify network topology;
    - own GUI state;
    - schedule simulation events.

Decision Boundary
-----------------

Protection elements produce ProtectionDecision objects.

ProtectionSystem consumes those decisions.

ProtectionSystem may identify actionable trip requests, but does not
operate a physical breaker.

The intended boundary is:

    Protection Element
            |
            v
    ProtectionDecision
            |
            v
    ProtectionSystem
            |
            v
       TripRequest
            |
            v
      BreakerManager

Future Event Scheduling
-----------------------

ProtectionSystem deliberately does not own a simulation clock or
event scheduler.

A future protection-event layer may use the decisions produced here
to schedule:

    - inverse-time trips;
    - breaker-failure timers;
    - delayed distance zones;
    - reclosing;
    - interlocking;
    - transfer-trip;
    - lockout;
    - sequence-of-events recording.

This keeps protection execution independent from any particular
simulation engine.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Iterable, Mapping, Optional

from .protection_decision import ProtectionDecision


# =====================================================================
# PROTECTION SYSTEM
# =====================================================================


class ProtectionSystem:
    """
    Central GridForge V2 protection-function orchestration service.

    Notes
    -----
    The system stores references to protection elements.

    It does not clone or replace the authoritative Relay model.

    Multiple protection elements may reference the same physical relay.
    """

    def __init__(
        self,
        *,
        history_limit: int = 1000,
    ) -> None:

        history_limit = int(history_limit)

        if history_limit < 0:
            raise ValueError(
                "history_limit must be >= 0."
            )

        self.history_limit = history_limit

        # Ordered storage gives deterministic registration/evaluation
        # behaviour while allowing arbitrary plugin implementations.
        self._elements: "OrderedDict[Any, Any]" = OrderedDict()

        # Evaluation history contains ProtectionDecision objects only.
        self._history: list[ProtectionDecision] = []

    # =================================================================
    # ELEMENT REGISTRATION
    # =================================================================

    def register(
        self,
        element: Any,
    ) -> None:
        """
        Register one protection-function element.

        Parameters
        ----------
        element:
            RelayBase-compatible protection element.

        Notes
        -----
        The element must expose:

            id
            relay
            evaluate()

        ProtectionSystem deliberately does not require a concrete
        RelayBase subclass so that plugin implementations can remain
        decoupled from this orchestration layer.
        """

        if element is None:
            raise ValueError(
                "Protection element cannot be None."
            )

        element_id = getattr(
            element,
            "id",
            None,
        )

        if element_id is None:
            raise TypeError(
                "Protection element must expose an 'id' property."
            )

        if element_id in self._elements:
            raise ValueError(
                f"Protection element '{element_id}' "
                "is already registered."
            )

        evaluate = getattr(
            element,
            "evaluate",
            None,
        )

        if not callable(evaluate):
            raise TypeError(
                "Protection element must expose "
                "a callable evaluate() method."
            )

        self._elements[
            element_id
        ] = element

    # -----------------------------------------------------------------

    def unregister(
        self,
        element_id: Any,
    ) -> Any:
        """
        Remove and return a registered protection element.
        """

        try:
            return self._elements.pop(
                element_id
            )
        except KeyError as exc:
            raise KeyError(
                f"Protection element '{element_id}' "
                "is not registered."
            ) from exc

    # -----------------------------------------------------------------

    def clear(
        self,
    ) -> None:
        """
        Remove all registered protection elements.

        Evaluation history is preserved.
        """

        self._elements.clear()

    # -----------------------------------------------------------------

    @property
    def elements(self) -> tuple[Any, ...]:
        """
        Return registered protection elements in deterministic order.
        """

        return tuple(
            self._elements.values()
        )

    # -----------------------------------------------------------------

    def __len__(self) -> int:
        return len(
            self._elements
        )

    # -----------------------------------------------------------------

    def __contains__(
        self,
        element_id: Any,
    ) -> bool:
        return element_id in self._elements

    # =================================================================
    # LOOKUP
    # =================================================================

    def get_element(
        self,
        element_id: Any,
    ) -> Any:
        """
        Return a registered protection element.
        """

        try:
            return self._elements[
                element_id
            ]
        except KeyError as exc:
            raise KeyError(
                f"Protection element '{element_id}' "
                "is not registered."
            ) from exc

    # -----------------------------------------------------------------

    def elements_for_relay(
        self,
        relay_id: Any,
    ) -> tuple[Any, ...]:
        """
        Return all protection elements hosted by one physical relay.

        This is fundamental to multifunction-relay support.
        """

        result = []

        for element in self._elements.values():

            relay = getattr(
                element,
                "relay",
                None,
            )

            element_relay_id = getattr(
                relay,
                "id",
                None,
            )

            if element_relay_id == relay_id:
                result.append(
                    element
                )

        return tuple(result)

    # -----------------------------------------------------------------

    def elements_by_function(
        self,
        function_code: str,
    ) -> tuple[Any, ...]:
        """
        Return all registered elements with the specified function
        code.

        Examples
        --------
        50
        51
        67
        21
        87T
        """

        normalized = str(
            function_code
        ).strip().upper()

        if not normalized:
            raise ValueError(
                "function_code cannot be empty."
            )

        return tuple(
            element
            for element in self._elements.values()
            if str(
                getattr(
                    element,
                    "function_code",
                    "",
                )
            ).strip().upper()
            == normalized
        )

    # =================================================================
    # EVALUATION
    # =================================================================

    def evaluate(
        self,
        context: Any = None,
        *,
        elements: Optional[
            Iterable[Any]
        ] = None,
        record_history: bool = True,
    ) -> tuple[ProtectionDecision, ...]:
        """
        Evaluate registered protection elements.

        Parameters
        ----------
        context:
            Optional protection/simulation evaluation context.

            ProtectionSystem does not impose a concrete context type.

        elements:
            Optional subset of registered elements.

            Supplied elements must already be registered.

        record_history:
            Whether resulting decisions should be stored in the
            protection history.

        Returns
        -------
        tuple[ProtectionDecision, ...]
            Decisions in deterministic evaluation order.

        Notes
        -----
        ProtectionSystem does not manipulate Relay state directly.

        The protection element owns its algorithm execution and
        produces a ProtectionDecision.
        """

        selected = self._resolve_elements(
            elements
        )

        decisions: list[
            ProtectionDecision
        ] = []

        for element in selected:

            decision = self._evaluate_element(
                element,
                context,
            )

            decisions.append(
                decision
            )

        if record_history:
            self._record_history(
                decisions
            )

        return tuple(
            decisions
        )

    # -----------------------------------------------------------------

    @staticmethod
    def _evaluate_element(
        element: Any,
        context: Any,
    ) -> ProtectionDecision:
        """
        Evaluate one protection element and enforce the decision
        contract.
        """

        evaluate = getattr(
            element,
            "evaluate",
            None,
        )

        if not callable(evaluate):
            raise TypeError(
                "Registered protection element does not expose "
                "a callable evaluate() method."
            )

        # -------------------------------------------------------------
        # Compatibility with both:
        #
        #     evaluate()
        #
        # and future:
        #
        #     evaluate(context)
        # -------------------------------------------------------------

        try:
            if context is None:
                result = evaluate()
            else:
                result = evaluate(
                    context
                )

        except TypeError as exc:

            # Only retry the legacy no-argument form when context was
            # supplied. Other TypeErrors should normally propagate.
            if context is None:
                raise

            try:
                result = evaluate()
            except TypeError:
                raise exc

        if not isinstance(
            result,
            ProtectionDecision,
        ):
            raise TypeError(
                "Protection element "
                f"'{getattr(element, 'id', None)}' "
                "must return a ProtectionDecision."
            )

        return result

    # =================================================================
    # ELEMENT SELECTION
    # =================================================================

    def _resolve_elements(
        self,
        elements: Optional[
            Iterable[Any]
        ],
    ) -> tuple[Any, ...]:
        """
        Resolve an optional element subset.
        """

        if elements is None:
            return self.elements

        selected = []

        for element in elements:

            if element is None:
                raise ValueError(
                    "Protection element selection "
                    "cannot contain None."
                )

            element_id = getattr(
                element,
                "id",
                None,
            )

            if element_id not in self._elements:
                raise ValueError(
                    f"Protection element '{element_id}' "
                    "is not registered."
                )

            # Use the registered object rather than allowing an
            # arbitrary external object with the same identifier.
            selected.append(
                self._elements[
                    element_id
                ]
            )

        return tuple(
            selected
        )

    # =================================================================
    # DECISION FILTERING
    # =================================================================

    @staticmethod
    def actionable_decisions(
        decisions: Iterable[
            ProtectionDecision
        ],
    ) -> tuple[
        ProtectionDecision,
        ...,
    ]:
        """
        Return valid, unblocked trip-request decisions.
        """

        return tuple(
            decision
            for decision in decisions
            if decision.actionable
        )

    # -----------------------------------------------------------------

    @staticmethod
    def operating_decisions(
        decisions: Iterable[
            ProtectionDecision
        ],
    ) -> tuple[
        ProtectionDecision,
        ...,
    ]:
        """
        Return valid decisions whose protection element operated.
        """

        return tuple(
            decision
            for decision in decisions
            if (
                decision.valid
                and decision.operate
                and not decision.blocked
            )
        )

    # -----------------------------------------------------------------

    @staticmethod
    def pickup_decisions(
        decisions: Iterable[
            ProtectionDecision
        ],
    ) -> tuple[
        ProtectionDecision,
        ...,
    ]:
        """
        Return valid decisions for elements that picked up.
        """

        return tuple(
            decision
            for decision in decisions
            if (
                decision.valid
                and decision.pickup
                and not decision.blocked
            )
        )

    # =================================================================
    # TRIP REQUEST BOUNDARY
    # =================================================================

    def trip_requests(
        self,
        decisions: Iterable[
            ProtectionDecision
        ],
    ) -> tuple[
        ProtectionDecision,
        ...,
    ]:
        """
        Extract actionable protection trip requests.

        This method does NOT operate a breaker.

        The returned decisions form the protection-to-breaker
        boundary for downstream orchestration.
        """

        return self.actionable_decisions(
            decisions
        )

    # =================================================================
    # HISTORY
    # =================================================================

    def _record_history(
        self,
        decisions: Iterable[
            ProtectionDecision
        ],
    ) -> None:
        """
        Store evaluation decisions subject to history_limit.
        """

        if self.history_limit == 0:
            return

        self._history.extend(
            decisions
        )

        overflow = (
            len(self._history)
            - self.history_limit
        )

        if overflow > 0:
            del self._history[
                :overflow
            ]

    # -----------------------------------------------------------------

    @property
    def history(self) -> tuple[
        ProtectionDecision,
        ...,
    ]:
        """
        Return recorded protection decisions.
        """

        return tuple(
            self._history
        )

    # -----------------------------------------------------------------

    def clear_history(self) -> None:
        """
        Clear recorded protection decisions.
        """

        self._history.clear()

    # =================================================================
    # RESET
    # =================================================================

    def reset(
        self,
        *,
        clear_history: bool = False,
    ) -> None:
        """
        Reset all registered protection elements.

        The physical Relay devices are not directly manipulated.

        Each protection element owns its own algorithm-specific
        runtime state.
        """

        for element in self._elements.values():

            reset = getattr(
                element,
                "reset",
                None,
            )

            if callable(reset):
                reset()

        if clear_history:
            self.clear_history()

    # =================================================================
    # STATUS
    # =================================================================

    def status(self) -> dict[str, Any]:
        """
        Return structured protection-system diagnostics.
        """

        element_status = []

        for element in self._elements.values():

            status_method = getattr(
                element,
                "status",
                None,
            )

            if callable(status_method):
                element_status.append(
                    status_method()
                )
            else:
                element_status.append(
                    {
                        "id": getattr(
                            element,
                            "id",
                            None,
                        ),
                        "type": type(
                            element
                        ).__name__,
                    }
                )

        return {
            "element_count": len(
                self._elements
            ),
            "history_count": len(
                self._history
            ),
            "history_limit": self.history_limit,
            "elements": element_status,
        }

    # =================================================================
    # GROUPED STATUS
    # =================================================================

    def relay_status(
        self,
        relay_id: Any,
    ) -> dict[str, Any]:
        """
        Return status of all protection elements hosted by one relay.
        """

        elements = (
            self.elements_for_relay(
                relay_id
            )
        )

        result = []

        for element in elements:

            status_method = getattr(
                element,
                "status",
                None,
            )

            if callable(status_method):
                result.append(
                    status_method()
                )
            else:
                result.append(
                    {
                        "id": getattr(
                            element,
                            "id",
                            None,
                        ),
                        "function_code": getattr(
                            element,
                            "function_code",
                            None,
                        ),
                    }
                )

        return {
            "relay_id": relay_id,
            "element_count": len(
                elements
            ),
            "elements": result,
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        return (
            f"<ProtectionSystem "
            f"elements={len(self._elements)}, "
            f"history={len(self._history)}>"
        )


# =====================================================================
# PUBLIC API
# =====================================================================

__all__ = [
    "ProtectionSystem",
]
```
