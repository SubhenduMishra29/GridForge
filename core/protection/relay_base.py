"""
GridForge Protection Relay Base
===============================

File:
    core/protection/relay_base.py

Purpose
-------
Defines the common execution contract for GridForge V2 protection
function plugins.

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
      model.Relay
            |
      RelayBase
            |
    Protection Function
            |
      ProtectionSystem
            |
      BreakerManager


The Relay model in ``core/model/relay.py`` remains the authoritative
relay device/configuration/state object.

RelayBase is NOT a second relay model.

It provides the common protection-function interface through which
protection plugins consume the relay's configured inputs and produce
protection decisions.

Responsibilities
----------------
RelayBase provides:

- access to the authoritative Relay model;
- relay identity;
- relay configuration/state access;
- access to configured RelayInput objects;
- access to measurement-channel signals through RelayInput;
- common service-state handling;
- common pickup/operate/trip decision handling;
- reset handling;
- protection status reporting;
- a stable plugin interface for protection functions.

RelayBase does NOT:

- create CT/PT/CVT objects;
- create MeasurementChannel objects;
- create RelayInput objects implicitly;
- duplicate measured current/voltage/impedance state;
- build Y-bus;
- perform load flow;
- perform short-circuit analysis;
- calculate system-wide fault quantities;
- operate circuit breakers;
- coordinate multiple relays;
- perform TCC coordination;
- schedule protection events;
- own global protection-system state.

Those responsibilities belong to their respective GridForge layers.

Important V2 Principle
----------------------
Protection algorithms consume signals.

They do not invent measurements.

For example:

    CT
      |
      v
    MeasurementChannel
      |
      v
    RelayInput
      |
      v
    OvercurrentProtection

The overcurrent algorithm therefore evaluates a signal supplied by
the measurement architecture rather than reading ``relay.current``.

Similarly:

    PT / CVT
       |
       v
    MeasurementChannel
       |
       v
    RelayInput
       |
       v
    DistanceProtection

Distance protection obtains voltage and current-derived quantities
through the configured input architecture.

Trip Ownership
--------------
RelayBase may request/set the authoritative Relay's protection
operating state.

It does NOT operate a physical breaker.

The intended boundary is:

    RelayBase
        |
        | protection decision
        v
    ProtectionSystem
        |
        | trip command
        v
    BreakerManager

Plugin Architecture
-------------------
Concrete protection functions should derive from RelayBase.

Examples:

    OvercurrentRelay
    DirectionalRelay
    DistanceRelay
    DifferentialRelay
    VoltageRelay
    FrequencyRelay

A plugin may maintain algorithm-specific transient state, but such
state must be protection-function state rather than a duplicate of
Relay model state.

Copyright © 2026 Subhendu Mishra
All Rights Reserved.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping


class RelayBase(ABC):
    """
    Common base class for GridForge V2 protection-function plugins.

    Parameters
    ----------
    relay:
        Authoritative ``core.model.relay.Relay`` instance.

    relay_inputs:
        RelayInput objects configured for this protection function.

        The inputs are references to the existing measurement
        architecture. RelayBase does not create or own the physical
        measurement chain.

    Notes
    -----
    The supplied Relay remains authoritative for relay identity,
    configuration, service state, and protection operating state.

    RelayBase is an algorithm/execution layer object.
    """

    # =============================================================
    # INITIALIZATION
    # =============================================================

    def __init__(
        self,
        relay: Any,
        relay_inputs: Mapping[str, Any] | None = None,
    ) -> None:

        if relay is None:
            raise ValueError(
                "relay cannot be None."
            )

        self.relay = relay

        self._relay_inputs: dict[str, Any] = {}

        if relay_inputs is not None:
            self._set_relay_inputs(
                relay_inputs
            )

    # =============================================================
    # RELAY IDENTITY
    # =============================================================

    @property
    def id(self) -> Any:
        """
        Return the authoritative relay identifier.
        """

        return self.relay.id

    # -----------------------------------------------------------------

    @property
    def name(self) -> str:
        """
        Return the authoritative relay name.
        """

        return self.relay.name

    # -----------------------------------------------------------------

    @property
    def relay_type(self) -> str:
        """
        Return the authoritative relay type.
        """

        return self.relay.type

    # =============================================================
    # RELAY MODEL
    # =============================================================

    @property
    def relay_model(self) -> Any:
        """
        Return the authoritative Relay model.

        This is an explicit V2 accessor intended for plugins that
        need relay configuration/state not exposed by convenience
        properties.
        """

        return self.relay

    # =============================================================
    # SERVICE STATE
    # =============================================================

    @property
    def in_service(self) -> bool:
        """
        Return the authoritative relay service state.
        """

        return bool(
            self.relay.in_service
        )

    # =============================================================
    # INPUT ARCHITECTURE
    # =============================================================

    def _set_relay_inputs(
        self,
        relay_inputs: Mapping[str, Any],
    ) -> None:
        """
        Register RelayInput references for this protection function.

        This method stores references only.

        It does not create, modify, or connect measurement channels.
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

            if not name.strip():
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
        Return the configured RelayInput references.

        The returned mapping is read-only from the caller's
        perspective.
        """

        return self._relay_inputs.copy()

    # -----------------------------------------------------------------

    def get_input(
        self,
        name: str,
    ) -> Any:
        """
        Return a configured RelayInput.

        Raises
        ------
        KeyError
            If the requested input is not configured.
        """

        try:
            return self._relay_inputs[name]
        except KeyError as exc:
            raise KeyError(
                f"Relay input '{name}' is not configured "
                f"for relay '{self.id}'."
            ) from exc

    # -----------------------------------------------------------------

    def has_input(
        self,
        name: str,
    ) -> bool:
        """
        Return True when the named RelayInput is configured.
        """

        return name in self._relay_inputs

    # =============================================================
    # SIGNAL ACCESS
    # =============================================================

    def input_signal(
        self,
        name: str,
    ) -> Any:
        """
        Return the current signal supplied by a RelayInput.

        RelayInput remains authoritative for the signal path.

        RelayBase does not cache the returned measurement.
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

        # Compatibility with implementations that expose
        # a ``value`` property rather than ``signal``.
        if hasattr(
            relay_input,
            "value",
        ):
            value = getattr(
                relay_input,
                "value",
            )

            if callable(value):
                return value()

            return value

        raise AttributeError(
            f"RelayInput '{name}' does not expose "
            "a supported signal interface."
        )

    # =============================================================
    # INPUT VALIDATION
    # =============================================================

    def require_inputs(
        self,
        *names: str,
    ) -> None:
        """
        Require specific RelayInputs before protection evaluation.

        Protection plugins should use this during initialization or
        before evaluation when their input requirements are explicit.
        """

        missing = [
            name
            for name in names
            if name not in self._relay_inputs
        ]

        if missing:
            raise ValueError(
                f"Relay '{self.id}' is missing required "
                f"RelayInput(s): {missing}"
            )

    # =============================================================
    # PROTECTION STATE
    # =============================================================

    @property
    def picked_up(self) -> bool:
        """
        Return the authoritative relay pickup/operate state when
        supported by the V2 Relay model.

        RelayBase does not maintain a duplicate pickup state.
        """

        if hasattr(
            self.relay,
            "picked_up",
        ):
            return bool(
                self.relay.picked_up
            )

        return False

    # -----------------------------------------------------------------

    @property
    def operated(self) -> bool:
        """
        Return the authoritative relay operating state when exposed
        by the V2 Relay model.

        Falls back to pickup state for models that intentionally
        combine pickup and operation.
        """

        if hasattr(
            self.relay,
            "operated",
        ):
            return bool(
                self.relay.operated
            )

        return self.picked_up

    # -----------------------------------------------------------------

    @property
    def tripped(self) -> bool:
        """
        Return the authoritative relay trip state.
        """

        return bool(
            self.relay.trip
        )

    # =============================================================
    # DECISION CONTROL
    # =============================================================

    def set_pickup(
        self,
        state: bool,
    ) -> bool:
        """
        Set the authoritative relay pickup state.

        The V2 Relay model owns this state.

        If the Relay model does not expose a separate pickup state,
        the method intentionally does not create one in RelayBase.
        """

        if hasattr(
            self.relay,
            "set_pickup_state",
        ):
            self.relay.set_pickup_state(
                bool(state)
            )

        return bool(state)

    # -----------------------------------------------------------------

    def set_operated(
        self,
        state: bool,
    ) -> bool:
        """
        Set the authoritative relay operated state when supported.

        No duplicate state is created in RelayBase.
        """

        if hasattr(
            self.relay,
            "set_operated",
        ):
            self.relay.set_operated(
                bool(state)
            )

        return bool(state)

    # -----------------------------------------------------------------

    def trip(self) -> bool:
        """
        Assert the authoritative relay trip state.

        This represents a protection trip decision.

        It does NOT operate a circuit breaker.
        """

        if not self.in_service:
            self.reset_trip()
            return False

        self.relay.set_trip(
            True
        )

        return bool(
            self.relay.trip
        )

    # -----------------------------------------------------------------

    def reset_trip(self) -> None:
        """
        Clear the authoritative relay trip state.
        """

        self.relay.set_trip(
            False
        )

    # =============================================================
    # EVALUATION
    # =============================================================

    @abstractmethod
    def check_pickup(self) -> bool:
        """
        Evaluate the protection pickup criterion.

        Returns
        -------
        bool
            True when the protection element should pick up.

        Notes
        -----
        Implementations must obtain electrical signals through the
        configured RelayInput/MeasurementChannel architecture.

        They must not assume that current, voltage, impedance, or
        other quantities are stored directly on the protection
        algorithm object.
        """

        raise NotImplementedError

    # -----------------------------------------------------------------

    def evaluate(
        self,
    ) -> bool:
        """
        Execute one protection evaluation cycle.

        This is the common instantaneous decision boundary.

        Sequence
        --------
        1. Check relay service state.
        2. Evaluate plugin-specific pickup criterion.
        3. Update authoritative relay pickup/operate state.
        4. Assert or clear the relay trip state.

        Time grading, intentional delay, TCC operation, event
        scheduling, and breaker operation are outside this method.
        """

        if not self.in_service:
            self.set_pickup(
                False
            )

            self.set_operated(
                False
            )

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

    # =============================================================
    # RESET
    # =============================================================

    def reset(self) -> None:
        """
        Reset protection-function operating state.

        The authoritative Relay model is reset first.

        Subclasses may override this method to clear genuine
        algorithm-specific transient state, but should call
        ``super().reset()``.
        """

        if hasattr(
            self.relay,
            "reset_protection_state",
        ):
            self.relay.reset_protection_state()
        else:
            self.reset_trip()

            if hasattr(
                self.relay,
                "set_pickup_state",
            ):
                self.relay.set_pickup_state(
                    False
                )

            if hasattr(
                self.relay,
                "set_operated",
            ):
                self.relay.set_operated(
                    False
                )

    # =============================================================
    # STATUS
    # =============================================================

    def status(self) -> dict[str, Any]:
        """
        Return protection-function status.

        The status is assembled from the authoritative Relay and
        configured input architecture.

        No measurement state is duplicated here.
        """

        return {
            "relay_id": self.id,
            "relay_name": self.name,
            "relay_type": self.relay_type,
            "in_service": self.in_service,
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
        Obtain diagnostic information from a RelayInput.

        This method deliberately avoids imposing a concrete
        RelayInput implementation on the protection base class.
        """

        if hasattr(
            relay_input,
            "status",
        ):
            status = getattr(
                relay_input,
                "status",
            )

            if callable(status):
                return status()

            return status

        if hasattr(
            relay_input,
            "summary",
        ):
            summary = getattr(
                relay_input,
                "summary",
            )

            if callable(summary):
                return summary()

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


__all__ = [
    "RelayBase",
]
```
