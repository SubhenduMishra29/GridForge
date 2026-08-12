```python
"""
GridForge Protection System
===========================

File:
    core/protection/protection_system.py

Purpose
-------
System-level orchestration of GridForge V2 protection elements.

Architectural principle
-----------------------
A physical Relay may host multiple protection functions.

Therefore:

    Relay
        |
        +-- ProtectionElement
        +-- ProtectionElement
        +-- ProtectionElement

ProtectionSystem owns the collection and orchestration of
ProtectionElement objects.

It does NOT replace the authoritative Relay model.

Responsibilities
----------------
ProtectionSystem provides:

- registration of protection elements;
- removal and lookup of elements;
- multifunction-relay composition;
- evaluation of enabled protection elements;
- reset of protection elements;
- protection decision collection;
- deterministic execution ordering;
- element-level status reporting;
- compatibility views by protection-function type.

ProtectionSystem does NOT:

- create physical Relay objects;
- create CT/PT/CVT objects;
- create MeasurementChannel objects;
- calculate electrical quantities;
- calculate fault current;
- build Ybus;
- perform load flow;
- perform short-circuit analysis;
- perform relay coordination;
- operate circuit breakers;
- schedule breaker operations.

Trip ownership
--------------
Protection functions may assert the authoritative Relay protection
trip state through RelayBase.

ProtectionSystem collects those decisions.

Physical breaker operation remains the responsibility of:

    BreakerManager

Future event scheduling and time grading belong to the simulation /
protection-event layer.

Multifunction relay support
---------------------------
This module deliberately does NOT use:

    one Relay = one protection function

Instead, multiple ProtectionElements may reference the same Relay.

Example:

    Relay R1
        |
        +-- OC51
        +-- Directional67
        +-- Distance21
        +-- Undervoltage27
        +-- Frequency81

The same RelayInput / MeasurementChannel architecture may therefore
be shared by multiple protection functions without duplicating
measurements.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
Proprietary and confidential.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping

from .protection_element import (
    ProtectionElement,
    ProtectionElementState,
)


class ProtectionSystem:
    """
    GridForge V2 protection-system orchestration service.

    ProtectionSystem is a runtime composition layer.

    The authoritative physical/configuration/state object remains the
    Relay model in ``core.model.relay``.
    """

    # =================================================================
    # INITIALIZATION
    # =================================================================

    def __init__(self) -> None:
        self._elements: Dict[Any, ProtectionElement] = {}

    # =================================================================
    # ELEMENT REGISTRATION
    # =================================================================

    def add_element(
        self,
        element: ProtectionElement,
    ) -> None:
        """
        Register a protection element.

        Protection-element identifiers must be unique within this
        ProtectionSystem.
        """

        if not isinstance(
            element,
            ProtectionElement,
        ):
            raise TypeError(
                "element must be a ProtectionElement."
            )

        if element.id in self._elements:
            raise ValueError(
                f"Protection element '{element.id}' "
                "is already registered."
            )

        self._elements[element.id] = element

    # -----------------------------------------------------------------

    def remove_element(
        self,
        element_id: Any,
    ) -> ProtectionElement:
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

    def has_element(
        self,
        element_id: Any,
    ) -> bool:
        """
        Return True when an element is registered.
        """

        return element_id in self._elements

    # -----------------------------------------------------------------

    def get_element(
        self,
        element_id: Any,
    ) -> ProtectionElement:
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

    # =================================================================
    # COLLECTION ACCESS
    # =================================================================

    @property
    def elements(self) -> tuple[ProtectionElement, ...]:
        """
        Return all registered protection elements.

        A tuple is returned so callers cannot modify the internal
        registry.
        """

        return tuple(
            self._elements.values()
        )

    # -----------------------------------------------------------------

    def iter_elements(
        self,
    ) -> Iterable[ProtectionElement]:
        """
        Iterate over registered protection elements.
        """

        return iter(
            self._elements.values()
        )

    # =================================================================
    # RELAY COMPOSITION
    # =================================================================

    def elements_for_relay(
        self,
        relay_id: Any,
    ) -> List[ProtectionElement]:
        """
        Return all protection elements belonging to a Relay.

        This is the primary multifunction-relay access pattern.
        """

        return [
            element
            for element in self._elements.values()
            if element.relay_id == relay_id
        ]

    # -----------------------------------------------------------------

    def relays(self) -> tuple[Any, ...]:
        """
        Return unique authoritative Relay objects represented by the
        registered protection elements.

        Relay identity/state remains owned by the Relay model.
        """

        result: List[Any] = []
        seen: set[int] = set()

        for element in self._elements.values():

            relay = element.relay_model
            identity = id(relay)

            if identity in seen:
                continue

            seen.add(identity)
            result.append(relay)

        return tuple(result)

    # =================================================================
    # FUNCTION TYPE ACCESS
    # =================================================================

    def elements_by_type(
        self,
        function_type: str,
    ) -> List[ProtectionElement]:
        """
        Return protection elements of a given function type.

        Examples
        --------
        ``OVERCURRENT``

        ``DIRECTIONAL``

        ``DISTANCE``

        ``DIFFERENTIAL``

        ``VOLTAGE``

        ``FREQUENCY``
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

        return [
            element
            for element in self._elements.values()
            if element.function_type
            == normalized
        ]

    # =================================================================
    # EXECUTION ORDER
    # =================================================================

    def _execution_order(
        self,
    ) -> List[ProtectionElement]:
        """
        Return elements in deterministic execution order.

        Lower priority values execute first.

        ProtectionSystem does not interpret priority as electrical
        coordination or grading time.

        Actual protection coordination belongs to the coordination
        layer.
        """

        return sorted(
            self._elements.values(),
            key=lambda element: (
                element.priority,
                str(element.id),
            ),
        )

    # =================================================================
    # EVALUATION
    # =================================================================

    def evaluate(
        self,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate all enabled protection elements.

        Returns
        -------
        list of dict
            Element-level protection decisions.

        Notes
        -----
        This method performs orchestration only.

        It does not:

        - calculate fault current;
        - determine system electrical state;
        - coordinate relays;
        - operate breakers;
        - schedule delayed trips.
        """

        decisions: List[
            Dict[str, Any]
        ] = []

        for element in self._execution_order():

            if not element.enabled:
                continue

            operates = element.evaluate()

            decisions.append(
                {
                    "element_id": element.id,
                    "relay_id": element.relay_id,
                    "function_type": (
                        element.function_type
                    ),
                    "operated": operates,
                    "state": element.state.value,
                }
            )

        return decisions

    # =================================================================
    # RESET
    # =================================================================

    def reset(self) -> None:
        """
        Reset all registered protection elements.
        """

        for element in self._elements.values():
            element.reset()

    # =================================================================
    # DECISION QUERIES
    # =================================================================

    def operated_elements(
        self,
    ) -> List[ProtectionElement]:
        """
        Return protection elements that currently report operation.
        """

        result: List[
            ProtectionElement
        ] = []

        for element in self._elements.values():

            function = (
                element.protection_function
            )

            operated = bool(
                getattr(
                    function,
                    "operated",
                    False,
                )
            )

            if operated:
                result.append(
                    element
                )

        return result

    # -----------------------------------------------------------------

    def tripped_elements(
        self,
    ) -> List[ProtectionElement]:
        """
        Return protection elements currently asserting trip.
        """

        result: List[
            ProtectionElement
        ] = []

        for element in self._elements.values():

            if (
                element.state
                == ProtectionElementState.TRIPPED
            ):
                result.append(
                    element
                )

        return result

    # =================================================================
    # COMPATIBILITY VIEWS
    # =================================================================

    @property
    def oc_relays(self) -> List[Any]:
        """
        Compatibility view of overcurrent protection functions.

        This is intentionally NOT the authoritative storage model.

        New code should prefer:

            elements_by_type("OVERCURRENT")
        """

        return [
            element.protection_function
            for element in self.elements_by_type(
                "OVERCURRENT"
            )
        ]

    # -----------------------------------------------------------------

    @property
    def distance_relays(self) -> List[Any]:
        """
        Compatibility view of distance protection functions.

        New code should prefer:

            elements_by_type("DISTANCE")
        """

        return [
            element.protection_function
            for element in self.elements_by_type(
                "DISTANCE"
            )
        ]

    # =================================================================
    # STATUS
    # =================================================================

    def status(self) -> Dict[str, Any]:
        """
        Return structured ProtectionSystem status.
        """

        return {
            "element_count": len(
                self._elements
            ),
            "relay_count": len(
                self.relays()
            ),
            "elements": [
                element.status()
                for element in self._execution_order()
            ],
        }

    # =================================================================
    # REPRESENTATION
    # =================================================================

    def __repr__(self) -> str:
        """
        Return concise developer-facing representation.
        """

        return (
            f"<ProtectionSystem "
            f"elements={len(self._elements)}, "
            f"relays={len(self.relays())}>"
        )


__all__ = [
    "ProtectionSystem",
]
```
